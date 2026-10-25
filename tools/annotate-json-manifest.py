#!/usr/bin/env python3
"""Add an "rdfArrayNote" to tests in a JSON-LD test manifest, keeping the file's formatting.

    python3 annotate-json-manifest.py MANIFEST.jsonld '#t0004' "note" ['#t0005' "note" ...]

The note goes on the line after the test's "purpose" (or "name"); a test with a note keeps it.
JSON-LD processors ignore the key (it is not in the manifest context); people and runners can read it.
"""
import json
import pathlib
import re
import sys


def annotate(path, test_id, note):
    path = pathlib.Path(path)
    text = path.read_text(encoding='utf-8')
    m = re.search(r'"@id":\s*"' + re.escape(test_id) + r'"', text)
    if not m:
        raise ValueError(f'{test_id} not in {path}')
    end = text.find('"@id": "#', m.end())
    block = text[m.start(): end if end > 0 else len(text)]
    if 'rdfArrayNote' in block:
        return False
    anchor = re.search(r'\n([ \t]*)"purpose":[^\n]*\n', block) or re.search(r'\n([ \t]*)"name":[^\n]*\n', block)
    line = f'{anchor.group(1)}"rdfArrayNote": {json.dumps("rdf-array: " + note)},\n'
    pos = m.start() + anchor.end()
    text = text[:pos] + line + text[pos:]
    json.loads(text)
    path.write_text(text, encoding='utf-8')
    return True


if __name__ == '__main__':
    args = sys.argv[2:]
    for tid, note in zip(args[::2], args[1::2]):
        annotate(sys.argv[1], tid, note)
