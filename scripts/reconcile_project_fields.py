#!/usr/bin/env python3
"""Reconcile Initiative and Sprint on open items in the Homelab Project.

Rules (docs/tracking.md):
- Initiative mirrors the item's codeword label. The label is authoritative.
- Sprint is the sprint ID at the start of the title (`<codeword>-<n>: ...`),
  or `backlog` when an open item's title has none.

Dry run by default: prints planned changes and gaps, and changes nothing.
It checks open items in the Project's linked repositories and open items
already in the Project from other repositories, plus closed items whose title
carries a sprint ID. With --apply, it creates missing Sprint options, adds
missing items from linked repositories and sets both fields. A Sprint option
is created only for a sprint ID whose codeword is an Initiative option.
Existing options keep their IDs, so no item loses its value. Items it cannot
resolve are reported as gaps and left unchanged. Requires the GitHub CLI with
the `project` scope.

Exit status: 0 when nothing is pending and no open item has a gap, 1
otherwise. Gaps on closed items are reported but do not fail the run.
"""
import argparse
import json
import re
import subprocess
import sys

SPRINT_TITLE = re.compile(r'^([a-z]+-[0-9]+):')
# `state` is selected per type: Issue and PR states are different enums, so
# a shared selection would be an invalid field merge in load_items.
CONTENT = '''
  id number title
  repository { nameWithOwner }
  labels(first: 30) { nodes { name } }
'''


def graphql(query, **variables):
    body = json.dumps({'query': query, 'variables': variables})
    result = subprocess.run(['gh', 'api', 'graphql', '--input', '-'],
                            input=body, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit('GraphQL request failed: ' + result.stderr.strip())
    payload = json.loads(result.stdout)
    if payload.get('errors'):
        sys.exit('GraphQL request failed: ' + json.dumps(payload['errors']))
    return payload['data']


def load_project(owner, number):
    data = graphql('''
      query($owner: String!, $number: Int!) {
        user(login: $owner) { projectV2(number: $number) {
          id
          fields(first: 50) { nodes {
            ... on ProjectV2SingleSelectField {
              id name options { id name color description } } } }
          repositories(first: 50) { nodes { nameWithOwner } }
        } }
      }''', owner=owner, number=number)
    project = data['user']['projectV2']
    fields = {f['name']: f for f in project['fields']['nodes'] if f}
    for name in ('Initiative', 'Sprint', 'Status'):
        if name not in fields:
            sys.exit('Project has no single-select field named %s.' % name)
    repos = [r['nameWithOwner'] for r in project['repositories']['nodes']]
    return project['id'], fields, repos


def load_items(project_id):
    items, cursor = [], None
    while True:
        data = graphql('''
          query($id: ID!, $after: String) {
            node(id: $id) { ... on ProjectV2 {
              items(first: 100, after: $after) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id type
                  content {
                    ... on Issue { %s state }
                    ... on PullRequest { %s prState: state }
                    ... on DraftIssue { title }
                  }
                  fieldValues(first: 30) { nodes {
                    ... on ProjectV2ItemFieldSingleSelectValue {
                      name field { ... on ProjectV2SingleSelectField { name } } } } }
                } } } }
          }''' % (CONTENT, CONTENT), id=project_id, **({'after': cursor} if cursor else {}))
        page = data['node']['items']
        for node in page['nodes']:
            if node['content'] and 'prState' in node['content']:
                node['content']['state'] = node['content'].pop('prState')
        items += page['nodes']
        if not page['pageInfo']['hasNextPage']:
            return items
        cursor = page['pageInfo']['endCursor']


def repo_content(repo, closed=False):
    """Open Issues and PRs in a repository, or closed and merged ones."""
    owner, name = repo.split('/')
    states = {'issues': 'CLOSED', 'pullRequests': '[CLOSED, MERGED]'} if closed else \
             {'issues': 'OPEN', 'pullRequests': 'OPEN'}
    nodes = []
    for kind in ('issues', 'pullRequests'):
        cursor = None
        while True:
            data = graphql('''
              query($owner: String!, $name: String!, $after: String) {
                repository(owner: $owner, name: $name) {
                  %s(first: 100, after: $after, states: %s) {
                    pageInfo { hasNextPage endCursor }
                    nodes { %s state } } }
              }''' % (kind, states[kind], CONTENT), owner=owner, name=name,
                **({'after': cursor} if cursor else {}))
            page = data['repository'][kind]
            nodes += page['nodes']
            if not page['pageInfo']['hasNextPage']:
                break
            cursor = page['pageInfo']['endCursor']
    return nodes


def sprint_id(title):
    match = SPRINT_TITLE.match(title)
    return match.group(1) if match else None


def missing_sprints(titles, fields):
    """Sprint IDs in titles that have no Sprint option but a known codeword."""
    codewords = {o['name'] for o in fields['Initiative']['options']}
    existing = {o['name'] for o in fields['Sprint']['options']}
    found = {sprint_id(t) for t in titles} - {None} - existing
    return sorted(s for s in found if s.rsplit('-', 1)[0] in codewords)


def merged_options(existing, names):
    """Option input that keeps every existing option and appends new ones."""
    keep = [{'id': o['id'], 'name': o['name'], 'color': o['color'],
             'description': o.get('description') or ''} for o in existing]
    have = {o['name'] for o in existing}
    return keep + [{'name': n, 'color': 'GRAY', 'description': ''}
                   for n in names if n not in have]


def add_sprint_options(field, names):
    data = graphql('''
      mutation($field: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
        updateProjectV2Field(input: {fieldId: $field, singleSelectOptions: $options}) {
          projectV2Field { ... on ProjectV2SingleSelectField {
            id name options { id name color description } } } } }''',
                   field=field['id'], options=merged_options(field['options'], names))
    updated = data['updateProjectV2Field']['projectV2Field']
    lost = {o['id'] for o in field['options']} - {o['id'] for o in updated['options']}
    if lost:
        sys.exit('STOP: Sprint option IDs changed during update: %s' % sorted(lost))
    return updated


def add_item(project_id, content_id):
    data = graphql('''
      mutation($project: ID!, $content: ID!) {
        addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
          item { id } } }''', project=project_id, content=content_id)
    return data['addProjectV2ItemById']['item']['id']


def set_option(project_id, item_id, field, option_id):
    graphql('''
      mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
        updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item,
          fieldId: $field, value: {singleSelectOptionId: $option}}) {
          projectV2Item { id } } }''',
            project=project_id, item=item_id, field=field, option=option_id)


def desired(content, fields):
    """Return ({field: option name}, [gaps]) for one Issue or PR."""
    want, gaps = {}, []
    codewords = {o['name'] for o in fields['Initiative']['options']}
    labels = sorted(l['name'] for l in content['labels']['nodes'] if l['name'] in codewords)
    if len(labels) == 1:
        want['Initiative'] = labels[0]
    elif not labels:
        gaps.append('no codeword label')
    else:
        gaps.append('multiple codeword labels: ' + ', '.join(labels))
    sprints = {o['name'] for o in fields['Sprint']['options']}
    sprint = sprint_id(content['title']) or 'backlog'
    if sprint in sprints:
        want['Sprint'] = sprint
    else:
        gaps.append('Sprint option %r cannot be created: its codeword is not an '
                    'Initiative option' % sprint)
    return want, gaps


def reconcile(ref, content, item, fields, options, project_id, apply, closed):
    """Plan or set one item's fields. Return (pending, gaps)."""
    pending, gaps, current = 0, 0, {}
    if item is None:
        if not apply:
            print('ADD   %s (not in the Project)' % ref)
            pending += 1
        else:
            item = {'id': add_item(project_id, content['id'])}
            print('ADDED %s' % ref)
    else:
        for value in item['fieldValues']['nodes']:
            if value and value.get('field'):
                current[value['field']['name']] = value['name']
    want, item_gaps = desired(content, fields)
    for gap in item_gaps:
        print('GAP   %s%s: %s' % (ref, ' (closed)' if closed else '', gap))
    gaps += len(item_gaps)
    for field, value in sorted(want.items()):
        if current.get(field) == value:
            continue
        if apply and item is not None and value in options[field]:
            set_option(project_id, item['id'], fields[field]['id'], options[field][value])
            print('SET   %s %s: %s -> %s' % (ref, field, current.get(field), value))
        else:
            print('PLAN  %s %s: %s -> %s' % (ref, field, current.get(field), value))
            pending += 1
    if not closed and item is not None and 'fieldValues' in item and 'Status' not in current:
        print('GAP   %s: no Status' % ref)
        gaps += 1
    return pending, gaps


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--owner', default='kevtruo')
    parser.add_argument('--project', type=int, default=1)
    parser.add_argument('--apply', action='store_true', help='write changes')
    args = parser.parse_args()

    project_id, fields, repos = load_project(args.owner, args.project)
    items = load_items(project_id)
    by_content = {i['content']['id']: i for i in items
                  if i['content'] and 'id' in i['content']}

    pending, gaps, closed_gaps = 0, 0, 0
    for item in items:
        if item['type'] == 'DRAFT_ISSUE':
            print('GAP   draft item %r: convert it to an Issue or remove it'
                  % item['content']['title'])
            gaps += 1

    # Open items in linked repositories, plus open items already in the
    # Project from repositories that are not linked.
    work = [(content, by_content.get(content['id']))
            for repo in repos for content in repo_content(repo)]
    seen = {content['id'] for content, _ in work}
    work += [(i['content'], i) for i in items
             if i['content'] and i['content'].get('state') == 'OPEN'
             and i['content']['id'] not in seen]

    # Closed items with a sprint ID: linked repositories and the Project.
    closed = [(content, by_content.get(content['id']))
              for repo in repos for content in repo_content(repo, closed=True)
              if sprint_id(content['title'])]
    seen = {content['id'] for content, _ in closed}
    closed += [(i['content'], i) for i in items
               if i['content'] and i['content'].get('state') in ('CLOSED', 'MERGED')
               and i['content']['id'] not in seen and sprint_id(i['content']['title'])]

    # Sprint options first, so items can be set in the same run.
    new = missing_sprints([c['title'] for c, _ in work + closed], fields)
    if new and args.apply:
        fields['Sprint'] = add_sprint_options(fields['Sprint'], new)
        print('OPTION Sprint: added %s' % ', '.join(new))
    elif new:
        print('PLAN  Sprint options to add: %s' % ', '.join(new))
        pending += len(new)
    # A planned option counts as present when deciding gaps in a dry run.
    for name in new:
        if name not in {o['name'] for o in fields['Sprint']['options']}:
            fields['Sprint']['options'].append({'id': None, 'name': name})
    options = {name: {o['name']: o['id'] for o in fields[name]['options'] if o['id']}
               for name in ('Initiative', 'Sprint')}

    for group, is_closed in ((work, False), (closed, True)):
        for content, item in group:
            ref = '%s#%d' % (content['repository']['nameWithOwner'], content['number'])
            p, g = reconcile(ref, content, item, fields, options, project_id,
                             args.apply, is_closed)
            pending += p
            if is_closed:
                closed_gaps += g
            else:
                gaps += g

    print('Summary: %d open and %d closed item(s) checked, %d pending change(s), '
          '%d gap(s) on open items, %d on closed items%s'
          % (len(work), len(closed), pending, gaps, closed_gaps,
             '' if args.apply else ' (dry run)'))
    return 1 if pending or gaps else 0


if __name__ == '__main__':
    sys.exit(main())
