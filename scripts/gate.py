#!/usr/bin/env python3
"""Checks for the always-run PR gate (docs/code-review.md).

Subcommands:
- whitespace: no trailing whitespace, no CR, one final newline in text files.
- links: relative Markdown links resolve to a file and, if given, a heading.
- public-safety: no cloud account or organization identifiers, ARNs, keys or
  tokens, GitHub App identifiers, local or log paths, chat webhook or channel
  identifiers, or private names in tracked files, or in extra text passed with
  --text (PR title, body, commit messages, branch name).

Private names are kept as SHA-256 hashes of lowercase tokens in
scripts/public_safety_denylist.sha256, so the list itself discloses nothing
directly. Add one with: printf %s NAME | sha256sum

Exit status: 0 when clean, 1 when any finding is reported.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
DENYLIST = 'scripts/public_safety_denylist.sha256'
SELF = 'scripts/gate.py'
BINARY_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip'}

PATTERNS = [
    ('cloud account ID', r'(?<![\w.-])\d{12}(?![\w-])'),
    ('cloud resource ARN', r'\barn:aws[a-z-]*:'),
    ('cloud organization ID', r'\b(?:o-[a-z0-9]{10,32}|ou-[a-z0-9]{4,32}-[a-z0-9]{8,32}|r-[a-z0-9]{4,32})\b'),
    ('cloud access key', r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    ('private key', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('GitHub token', r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})'),
    ('GitHub App identifier', r'(?i)\b(?:app|installation|client)[ _-]?id\b\W{0,3}[A-Za-z0-9.]*\d'),
    ('GitHub App client ID', r'\bIv[0-9a-z]{2}\.?[0-9a-zA-Z]{16}\b'),
    ('local or log path', r'(?<![\w.])(?:/Users/|/home/|/var/log/|/private/var/|[A-Za-z]:\\\\?Users)'),
    ('chat webhook', r'(?i)discord(?:app)?\.com/api/webhooks'),
    ('chat or platform numeric ID', r'(?<![\w.-])\d{17,20}(?![\w-])'),
]
TOKEN = re.compile(r'[a-z0-9][a-z0-9._-]*[a-z0-9]')
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
FENCE = re.compile(r'^\s*(```|~~~)')


def tracked_files():
    output = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT)
    files = [ROOT / f for f in output.decode().split('\0') if f]
    return [f for f in files if f.is_file() and f.suffix.lower() not in BINARY_SUFFIXES]


def rel(path):
    return path.relative_to(ROOT).as_posix()


def check_whitespace(files):
    findings = []
    for path in files:
        data = path.read_bytes()
        if not data:
            continue
        if b'\r' in data:
            findings.append('%s: carriage return' % rel(path))
        if not data.endswith(b'\n') or data.endswith(b'\n\n'):
            findings.append('%s: must end with exactly one newline' % rel(path))
        for number, line in enumerate(data.split(b'\n'), 1):
            if line.rstrip(b' \t\r') != line.rstrip(b'\r'):
                findings.append('%s:%d: trailing whitespace' % (rel(path), number))
    return findings


def slug(text):
    """GitHub heading anchor: lowercase, drop punctuation, spaces to hyphens."""
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[^\w\- ]', '', text.lower())
    return text.replace(' ', '-')


def markdown_lines(path):
    """Yield (number, line) outside fenced code blocks."""
    fenced = False
    for number, line in enumerate(path.read_text().split('\n'), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            yield number, line


def anchors(path):
    seen, result = {}, set()
    for _, line in markdown_lines(path):
        match = HEADING.match(line)
        if match:
            base = slug(match.group(2))
            count = seen.get(base, 0)
            seen[base] = count + 1
            result.add(base if count == 0 else '%s-%d' % (base, count))
    return result


def check_links(files):
    findings = []
    for path in (f for f in files if f.suffix == '.md'):
        for number, line in markdown_lines(path):
            for target in LINK.findall(re.sub(r'`[^`]*`', '', line)):
                if re.match(r'[a-z][a-z0-9+.-]*:', target, re.I):
                    continue
                file_part, _, anchor = target.partition('#')
                resolved = (path.parent / urllib.parse.unquote(file_part)).resolve() if file_part else path
                where = '%s:%d: %s' % (rel(path), number, target)
                if not resolved.exists():
                    findings.append(where + ' (missing file)')
                elif anchor and resolved.suffix == '.md' and anchor not in anchors(resolved):
                    findings.append(where + ' (missing heading)')
    return findings


def load_denylist():
    path = ROOT / DENYLIST
    if not path.exists():
        return set()
    lines = (l.split('#', 1)[0].strip() for l in path.read_text().split('\n'))
    return {l for l in lines if l}


def scan_text(label, text, denylist):
    findings = []
    for number, line in enumerate(text.split('\n'), 1):
        for name, pattern in PATTERNS:
            if re.search(pattern, line):
                findings.append('%s:%d: %s' % (label, number, name))
        for token in TOKEN.findall(line.lower()):
            if hashlib.sha256(token.encode()).hexdigest() in denylist:
                findings.append('%s:%d: private name' % (label, number))
    return findings


def check_public_safety(files, texts):
    denylist = load_denylist()
    findings = []
    for path in files:
        if rel(path) not in (SELF, DENYLIST):
            findings += scan_text(rel(path), path.read_text(errors='replace'), denylist)
    for label, text in texts:
        findings += scan_text(label, text, denylist)
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('check', choices=['whitespace', 'links', 'public-safety'])
    parser.add_argument('--text', nargs=2, action='append', default=[], metavar=('LABEL', 'FILE'),
                        help='also scan FILE (public-safety only), reported as LABEL')
    args = parser.parse_args()
    files = tracked_files()
    if args.check == 'whitespace':
        findings = check_whitespace(files)
    elif args.check == 'links':
        findings = check_links(files)
    else:
        texts = [(label, Path(name).read_text(errors='replace')) for label, name in args.text]
        findings = check_public_safety(files, texts)
    for finding in findings:
        print(finding)
    print('%s: %s' % (args.check, 'FAIL, %d finding(s)' % len(findings) if findings else 'PASS'))
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
