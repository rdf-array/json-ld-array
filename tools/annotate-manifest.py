#!/usr/bin/env python3
"""Add an rdfs:comment "rdf-array: ..." to tests in a W3C Turtle manifest.

    python3 annotate-manifest.py MANIFEST.ttl LOCALNAME "comment" [LOCALNAME "comment" ...]
    python3 annotate-manifest.py --json FILE    # [{"manifest": ..., "test": localname, "comment": ...}, ...]

The comment goes on the line after the test's mf:name, so the test keeps its name and everything
else; a test already carrying an rdf-array comment is left alone. LOCALNAME is the test IRI's
fragment or local name (collection_object for <#collection_object>, trs:collection_object, ...).
An rdfs: prefix is declared when the manifest has none.
"""
import json
import pathlib
import re
import sys

RDFS_PREFIX = '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n'


def annotate(path, local, comment):
    path = pathlib.Path(path)
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    subject = re.compile(r'^\s*(?:<#?' + re.escape(local) + r'>|[A-Za-z_][\w-]*:' + re.escape(local) + r'|:' + re.escape(local) + r')\s+(?:rdf:type|a)\s')
    for i, line in enumerate(lines):
        if not subject.match(line):
            continue
        # the test block runs to the line ending with ' .'
        j = i
        while j < len(lines) and not re.search(r'\s\.\s*$|^\s*\.\s*$', lines[j]):
            j += 1
        block = lines[i:j + 1]
        if any('rdf-array:' in b for b in block):
            return False
        for k in range(i, j + 1):
            if re.search(r'\bmf:name\b', lines[k]):
                indent = re.match(r'\s*', lines[k]).group(0) or '    '
                if k == i:  # mf:name on the subject line
                    indent = '    '
                quoted = comment.replace('\\', '\\\\').replace('"', '\\"')
                lines.insert(k + 1, f'{indent}rdfs:comment "rdf-array: {quoted}" ;\n')
                out = ''.join(lines)
                if not re.search(r'(?im)^\s*(@prefix|prefix)\s+rdfs:', out):
                    out = RDFS_PREFIX + out
                path.write_text(out, encoding='utf-8')
                return True
        raise ValueError(f'{path}: no mf:name in the block of {local}')
    raise ValueError(f'{path}: test {local} not found')


def main(argv):
    if argv[1] == '--json':
        done = 0
        for e in json.load(open(argv[2])):
            done += annotate(e['manifest'], e['test'], e['comment'])
        print(f'{done} tests annotated')
        return
    path, rest = argv[1], argv[2:]
    for local, comment in zip(rest[::2], rest[1::2]):
        annotate(path, local, comment)


if __name__ == '__main__':
    main(sys.argv)
