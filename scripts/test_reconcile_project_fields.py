#!/usr/bin/env python3
"""Tests for scripts/reconcile_project_fields.py against a fake GraphQL backend."""
import contextlib
import io
import sys
import unittest

import reconcile_project_fields as rec


def option(id_, name, color='BLUE', description='kept'):
    return {'id': id_, 'name': name, 'color': color, 'description': description}


def content(id_, number, title, state='OPEN', labels=('yeoman',), repo='o/r'):
    return {'id': id_, 'number': number, 'title': title, 'state': state,
            'repository': {'nameWithOwner': repo},
            'labels': {'nodes': [{'name': l} for l in labels]}}


def item(id_, node, values=()):
    nodes = [{'name': v, 'field': {'name': f}} for f, v in values]
    return {'id': id_, 'type': 'ISSUE', 'content': node, 'fieldValues': {'nodes': nodes}}


class FakeProject:
    """Answers the script's queries and records its mutations."""

    def __init__(self, open_items, closed_items, project_items, sprints):
        self.fields = [
            {'id': 'F-init', 'name': 'Initiative',
             'options': [option('I-y', 'yeoman'), option('I-p', 'portshift')]},
            {'id': 'F-sprint', 'name': 'Sprint', 'options': list(sprints)},
            {'id': 'F-status', 'name': 'Status', 'options': [option('S-d', 'Done')]},
        ]
        self.open, self.closed, self.items = open_items, closed_items, project_items
        self.mutations = []

    def __call__(self, query, **variables):
        if 'projectV2(number' in query:
            return {'user': {'projectV2': {
                'id': 'P', 'fields': {'nodes': self.fields},
                'repositories': {'nodes': [{'nameWithOwner': 'o/r'}]}}}}
        if 'items(first' in query:
            return {'node': {'items': {'nodes': self.items,
                                       'pageInfo': {'hasNextPage': False}}}}
        if 'repository(owner' in query:
            kind = 'issues' if 'issues(' in query else 'pullRequests'
            nodes = self.closed if 'CLOSED' in query else self.open
            if kind == 'pullRequests':
                nodes = []
            return {'repository': {kind: {'nodes': nodes, 'pageInfo': {'hasNextPage': False}}}}
        if 'updateProjectV2Field' in query:
            self.mutations.append(('options', variables['options']))
            options = [dict(o, id=o.get('id') or 'S-new-' + o['name'])
                       for o in variables['options']]
            self.fields[1]['options'] = options
            return {'updateProjectV2Field': {'projectV2Field': dict(self.fields[1], options=options)}}
        if 'addProjectV2ItemById' in query:
            self.mutations.append(('add', variables['content']))
            return {'addProjectV2ItemById': {'item': {'id': 'new-' + variables['content']}}}
        if 'updateProjectV2ItemFieldValue' in query:
            self.mutations.append(('set', variables['item'], variables['field'], variables['option']))
            return {'updateProjectV2ItemFieldValue': {'projectV2Item': {'id': variables['item']}}}
        raise AssertionError('unexpected query: ' + query[:80])


def run(fake, apply):
    rec.graphql = fake
    argv, out = sys.argv, io.StringIO()
    sys.argv = ['reconcile'] + (['--apply'] if apply else [])
    try:
        with contextlib.redirect_stdout(out):
            status = rec.main()
    finally:
        sys.argv = argv
    return status, out.getvalue()


class HelperTests(unittest.TestCase):
    fields = {'Initiative': {'options': [option('I-y', 'yeoman')]},
              'Sprint': {'options': [option('S-b', 'backlog')]}}

    def test_sprint_id(self):
        self.assertEqual(rec.sprint_id('yeoman-2: Add the gate'), 'yeoman-2')
        self.assertIsNone(rec.sprint_id('Add the gate'))
        self.assertIsNone(rec.sprint_id('see yeoman-2: later'))

    def test_missing_sprints_needs_known_codeword(self):
        titles = ['yeoman-3: a', 'yeoman-3: b', 'phase-4: legacy', 'backlog-1: x', 'plain']
        self.assertEqual(rec.missing_sprints(titles, self.fields), ['yeoman-3'])

    def test_merged_options_preserves_existing(self):
        existing = [option('S-1', 'backlog', 'GRAY', ''), option('S-2', 'yeoman-1', 'GREEN', 'done')]
        merged = rec.merged_options(existing, ['yeoman-2', 'yeoman-1'])
        self.assertEqual(merged[:2], existing)
        self.assertEqual(merged[2:], [{'name': 'yeoman-2', 'color': 'GRAY', 'description': ''}])

    def test_merged_options_fills_missing_description(self):
        merged = rec.merged_options([{'id': 'S-1', 'name': 'a', 'color': 'RED', 'description': None}], [])
        self.assertEqual(merged, [option('S-1', 'a', 'RED', '')])


class EndToEndTests(unittest.TestCase):
    def project(self):
        sprints = [option('S-b', 'backlog'), option('S-p3', 'portshift-3')]
        open_new = content('C1', 1, 'yeoman-2: Open work')
        closed_in = content('C2', 2, 'yeoman-2: Done work', state='CLOSED')
        closed_out = content('C3', 3, 'portshift-3: Old work', state='CLOSED', labels=('portshift',))
        closed_plain = content('C4', 4, 'TEST ISSUE', state='CLOSED', labels=())
        items = [item('IT2', closed_in, [('Status', 'Done')])]
        return FakeProject([open_new], [closed_in, closed_out, closed_plain], items, sprints)

    def test_dry_run_changes_nothing(self):
        fake = self.project()
        status, out = run(fake, apply=False)
        self.assertEqual(fake.mutations, [])
        self.assertEqual(status, 1)
        self.assertIn('PLAN  Sprint options to add: yeoman-2', out)
        self.assertIn('ADD   o/r#1 (not in the Project)', out)
        self.assertIn('ADD   o/r#3 (not in the Project)', out)
        self.assertNotIn('o/r#4', out)
        self.assertNotIn('GAP', out)

    def test_apply_creates_option_keeps_ids_and_sets_fields(self):
        fake = self.project()
        status, out = run(fake, apply=True)
        kind, options = fake.mutations[0]
        self.assertEqual(kind, 'options')
        self.assertEqual([o.get('id') for o in options], ['S-b', 'S-p3', None])
        self.assertEqual(options[0], option('S-b', 'backlog'))
        sets = {(m[1], m[2], m[3]) for m in fake.mutations if m[0] == 'set'}
        self.assertEqual(sets, {
            ('new-C1', 'F-init', 'I-y'), ('new-C1', 'F-sprint', 'S-new-yeoman-2'),
            ('IT2', 'F-init', 'I-y'), ('IT2', 'F-sprint', 'S-new-yeoman-2'),
            ('new-C3', 'F-init', 'I-p'), ('new-C3', 'F-sprint', 'S-p3'),
        })
        self.assertEqual({m[1] for m in fake.mutations if m[0] == 'add'}, {'C1', 'C3'})
        self.assertEqual(status, 0)
        self.assertIn('OPTION Sprint: added yeoman-2', out)

    def test_second_apply_is_a_no_op(self):
        fake = self.project()
        run(fake, apply=True)
        fake.items = [item('IT%d' % n, c, [('Initiative', l), ('Sprint', s), ('Status', 'Done')])
                      for n, c, l, s in ((1, fake.open[0], 'yeoman', 'yeoman-2'),
                                         (2, fake.closed[0], 'yeoman', 'yeoman-2'),
                                         (3, fake.closed[1], 'portshift', 'portshift-3'))]
        fake.mutations = []
        status, out = run(fake, apply=True)
        self.assertEqual(fake.mutations, [])
        self.assertEqual(status, 0)

    def test_lost_option_id_stops(self):
        fake = self.project()
        original = fake.__call__

        def dropping(query, **variables):
            data = original(query, **variables)
            if 'updateProjectV2Field' in query:
                field = data['updateProjectV2Field']['projectV2Field']
                field['options'] = field['options'][1:]
            return data
        with self.assertRaises(SystemExit) as stop:
            run(dropping, apply=True)
        self.assertIn('Sprint option IDs changed', str(stop.exception))

    def test_closed_gap_does_not_fail_the_run(self):
        fake = self.project()
        fake.closed.append(content('C5', 5, 'yeoman-2: Unlabelled', state='CLOSED', labels=()))
        status, out = run(fake, apply=True)
        self.assertIn('GAP   o/r#5 (closed): no codeword label', out)
        self.assertEqual(status, 0)

    def test_open_gap_fails_the_run(self):
        fake = self.project()
        fake.open.append(content('C6', 6, 'Untitled work', labels=()))
        status, out = run(fake, apply=True)
        self.assertIn('GAP   o/r#6: no codeword label', out)
        self.assertEqual(status, 1)


if __name__ == '__main__':
    unittest.main()
