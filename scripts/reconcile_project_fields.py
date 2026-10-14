#!/usr/bin/env python3
"""Reconcile Initiative and Sprint on open items in the Homelab Project.

Rules (docs/tracking.md):
- Initiative mirrors the item's codeword label. The label is authoritative.
- Sprint is the sprint ID at the start of the title (`<codeword>-<n>: ...`),
  or `backlog` when the title has none.

Dry run by default: prints planned changes and gaps, and changes nothing.
It checks open items in the Project's linked repositories and open items
already in the Project from other repositories. With --apply, it adds missing
open items from linked repositories and sets both fields. Items it cannot resolve are reported as
gaps and left unchanged. Requires the GitHub CLI with the `project` scope.

Exit status: 0 when nothing is pending and there are no gaps, 1 otherwise.
"""
import argparse
import json
import re
import subprocess
import sys

SPRINT_TITLE = re.compile(r'^([a-z]+-[0-9]+):')
CONTENT = '''
  id number title state
  repository { nameWithOwner }
  labels(first: 30) { nodes { name } }
'''


def graphql(query, **variables):
    cmd = ['gh', 'api', 'graphql', '-f', 'query=' + query]
    for key, value in variables.items():
        cmd += ['-F' if isinstance(value, int) else '-f', '%s=%s' % (key, value)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit('GraphQL request failed: ' + result.stderr.strip())
    return json.loads(result.stdout)['data']


def load_project(owner, number):
    data = graphql('''
      query($owner: String!, $number: Int!) {
        user(login: $owner) { projectV2(number: $number) {
          id
          fields(first: 50) { nodes {
            ... on ProjectV2SingleSelectField { id name options { id name } } } }
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
                    ... on Issue { %s }
                    ... on PullRequest { %s }
                    ... on DraftIssue { title }
                  }
                  fieldValues(first: 30) { nodes {
                    ... on ProjectV2ItemFieldSingleSelectValue {
                      name field { ... on ProjectV2SingleSelectField { name } } } } }
                } } } }
          }''' % (CONTENT, CONTENT), id=project_id, **({'after': cursor} if cursor else {}))
        page = data['node']['items']
        items += page['nodes']
        if not page['pageInfo']['hasNextPage']:
            return items
        cursor = page['pageInfo']['endCursor']


def open_content(repo):
    owner, name = repo.split('/')
    nodes = []
    for kind in ('issues', 'pullRequests'):
        cursor = None
        while True:
            data = graphql('''
              query($owner: String!, $name: String!, $after: String) {
                repository(owner: $owner, name: $name) {
                  %s(first: 100, after: $after, states: OPEN) {
                    pageInfo { hasNextPage endCursor }
                    nodes { %s } } }
              }''' % (kind, CONTENT), owner=owner, name=name,
                **({'after': cursor} if cursor else {}))
            page = data['repository'][kind]
            nodes += page['nodes']
            if not page['pageInfo']['hasNextPage']:
                break
            cursor = page['pageInfo']['endCursor']
    return nodes


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
    """Return ({field: option name}, [gaps]) for one open Issue or PR."""
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
    match = SPRINT_TITLE.match(content['title'])
    sprint = match.group(1) if match else 'backlog'
    if sprint in sprints:
        want['Sprint'] = sprint
    else:
        gaps.append('Sprint option %r does not exist (add it at sprint planning)' % sprint)
    return want, gaps


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--owner', default='kevtruo')
    parser.add_argument('--project', type=int, default=1)
    parser.add_argument('--apply', action='store_true', help='write changes')
    args = parser.parse_args()

    project_id, fields, repos = load_project(args.owner, args.project)
    options = {name: {o['name']: o['id'] for o in fields[name]['options']}
               for name in ('Initiative', 'Sprint')}
    items = load_items(project_id)
    by_content = {i['content']['id']: i for i in items
                  if i['content'] and 'id' in i['content']}

    pending, gaps = 0, 0
    for item in items:
        if item['type'] == 'DRAFT_ISSUE':
            print('GAP   draft item %r: convert it to an Issue or remove it'
                  % item['content']['title'])
            gaps += 1

    # Open items in linked repositories, plus open items already in the
    # Project from repositories that are not linked.
    work = [(content, by_content.get(content['id']))
            for repo in repos for content in open_content(repo)]
    seen = {content['id'] for content, _ in work}
    work += [(i['content'], i) for i in items
             if i['content'] and i['content'].get('state') == 'OPEN'
             and i['content']['id'] not in seen]

    for content, item in work:
        ref = '%s#%d' % (content['repository']['nameWithOwner'], content['number'])
        current, is_new = {}, item is None
        if is_new:
            if not args.apply:
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
            print('GAP   %s: %s' % (ref, gap))
        gaps += len(item_gaps)
        for field, value in sorted(want.items()):
            if current.get(field) == value:
                continue
            if args.apply and item is not None:
                set_option(project_id, item['id'], fields[field]['id'],
                           options[field][value])
                print('SET   %s %s: %s -> %s' % (ref, field, current.get(field), value))
            else:
                print('PLAN  %s %s: %s -> %s' % (ref, field, current.get(field), value))
                pending += 1
        if not is_new and 'Status' not in current:
            print('GAP   %s: no Status' % ref)
            gaps += 1

    print('Summary: %d open item(s) checked, %d pending change(s), %d gap(s)%s'
          % (len(work), pending, gaps, '' if args.apply else ' (dry run)'))
    return 1 if pending or gaps else 0


if __name__ == '__main__':
    sys.exit(main())
