#!/usr/bin/env python3
"""Tests for scripts/gate.py. Samples are built at runtime so this file passes its own scan."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import gate


def scan(text, denylist=()):
    return gate.scan_text('t', text, set(denylist))


class PublicSafetyTests(unittest.TestCase):
    def test_flags_identifiers(self):
        samples = {
            'cloud account ID': 'account ' + '1234' * 3,
            'cloud resource ARN': 'arn' + ':aws:iam::x:role/y',
            'cloud organization ID': 'o' + '-abcd123456',
            'cloud access key': 'AK' + 'IA' + 'A' * 16,
            'private key': '-----BEGIN ' + 'RSA PRIVATE KEY-----',
            'GitHub token': 'gh' + 'p_' + 'a' * 36,
            'GitHub App identifier': 'App' + ' ID: 123456',
            'local or log path': 'see ' + '/Us' + 'ers/someone/x',
            'chat webhook': 'https://discord' + '.com/api/web' + 'hooks/1/x',
            'chat or platform numeric ID': 'channel ' + '1' * 18,
        }
        for name, text in samples.items():
            with self.subTest(name=name):
                self.assertIn('t:1: ' + name, scan(text))

    def test_private_name_by_hash(self):
        name = 'private' + '-repo-name'
        digest = hashlib.sha256(name.encode()).hexdigest()
        self.assertEqual(scan('see owner/%s now' % name.upper(), [digest]), ['t:1: private name'])
        self.assertEqual(scan('a private repo name', [digest]), [])

    def test_ordinary_text_is_clean(self):
        for text in ['Version 1.2.3, issue #24, 2026-10-24', 'per-repo rules', 'a 12-step plan',
                     'https://github.com/kevtruo/homelab/pull/21', 'the app identity']:
            with self.subTest(text=text):
                self.assertEqual(scan(text), [])


class FileCheckTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.addCleanup(self.dir.cleanup)
        gate.ROOT = self.root

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())
        return path

    def test_whitespace(self):
        files = [self.write('ok.md', 'a\n'), self.write('trail.md', 'a \n'),
                 self.write('nofinal.md', 'a'), self.write('extra.md', 'a\n\n'),
                 self.write('crlf.md', 'a\r\n')]
        self.assertEqual(gate.check_whitespace(files), [
            'trail.md:1: trailing whitespace',
            'nofinal.md: must end with exactly one newline',
            'extra.md: must end with exactly one newline',
            'crlf.md: carriage return',
        ])

    def test_links(self):
        self.write('docs/b.md', '# Title\n\n## Sprint review\n\n## Sprint review\n')
        page = self.write('docs/a.md', '\n'.join([
            '[ok](b.md) [ok](b.md#sprint-review) [ok](b.md#sprint-review-1) [ok](#local)',
            '# Local',
            '[web](https://example.com/x) [mail](mailto:a@example.com)',
            '[bad](missing.md) [bad](b.md#nope)',
            '`[code](ignored.md)`',
            '```', '[fenced](ignored.md)', '```', '']))
        self.assertEqual(gate.check_links([page]), [
            'docs/a.md:4: missing.md (missing file)',
            'docs/a.md:4: b.md#nope (missing heading)',
        ])

    def test_slug(self):
        self.assertEqual(gate.slug('Tracking'), 'tracking')
        self.assertEqual(gate.slug('`yeoman` (Change Control)'), 'yeoman-change-control')
        self.assertEqual(gate.slug('E0a: entry steps'), 'e0a-entry-steps')


if __name__ == '__main__':
    unittest.main()
