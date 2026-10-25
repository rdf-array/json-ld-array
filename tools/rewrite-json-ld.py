#!/usr/bin/env python3
"""Rewrite JSON-LD test suites (json-ld-api-array, json-ld-streaming-array) for rdf-array.

    python3 rewrite-json-ld.py TESTS-DIR [--write]

toRdf-style tests (toRdf, html, stream-toRdf manifests): when the expected N-Quads spell an
rdf:first/rdf:rest ladder, fold it into a sequence and require agreement with what
jsonld-streaming-parser-array reads from the input (HTML inputs, which that parser cannot read,
are folded without the cross-check and listed). fromRdf tests: fold the input N-Quads with
JSON-LD 1.1's own list well-formedness rule (rdfarray.py fold --json-ld), so a well-formed ladder
becomes the sequence the expected @list stands for and a malformed or partial one keeps exactly the
triples the expected output already shows as properties. A JSON report goes to stdout.
"""
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rdfarray as ra  # noqa: E402

# Disagreements reviewed by hand and not about lists: the folded expectation is kept.
KNOWN_PARSER_DIFFERENCES = {
    '#tdi03': 'jsonld-streaming-parser-array writes "ar"^^rdf:dirLangString for an @direction list value '
              'without rdfDirection; the specification drops the direction, as the expectation does',
}

LADDER = re.compile(r'22-rdf-syntax-ns#(first|rest|nil)')


def parse_jsonld(path, base, option):
    out = subprocess.run(['node', str(HERE / 'parse-jsonld-array.js'), str(path), base, json.dumps(option)],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip()[-300:])
    return ra.parse(out.stdout)


def leading_comments(path):
    keep = []
    for line in path.read_text(encoding='utf-8').splitlines(keepends=True):
        if line.startswith('#') or not line.strip():
            keep.append(line)
        else:
            break
    return ''.join(keep)


def main():
    root = pathlib.Path(sys.argv[1]).expanduser().resolve()
    write = '--write' in sys.argv
    report = {'toRdf-rewritten': [], 'toRdf-unchecked': [], 'toRdf-review': [], 'fromRdf-rewritten': [],
              'fromRdf-unchanged': [], 'error': []}
    for manifest in sorted(root.glob('*manifest.jsonld')):
        m = json.loads(manifest.read_text(encoding='utf-8'))
        base_iri = m.get('baseIri', '')
        kind = 'fromRdf' if 'fromRdf' in manifest.name else 'toRdf' if re.search(r'toRdf|html', manifest.name) else None
        if not kind:
            continue
        for t in m.get('sequence', []):
            option = t.get('option', {})
            if kind == 'fromRdf':
                inp = root / t['input']
                if not inp.name.endswith(('.nq', '.nt')) or not LADDER.search(inp.read_text(encoding='utf-8')):
                    continue
                original = ra.read(inp)
                folded = ra.fold(original, json_ld=True)
                entry = {'manifest': manifest.name, 'test': t['@id'], 'file': t['input']}
                if folded != original:
                    report['fromRdf-rewritten'].append(entry)
                    if write:
                        inp.write_text(leading_comments(inp) + ra.write(folded), encoding='utf-8')
                else:
                    report['fromRdf-unchanged'].append(entry)
                continue
            exp = t.get('expect')
            if not exp or not exp.endswith(('.nq', '.nt')):
                continue
            expp = root / exp
            if not expp.exists() or not LADDER.search(expp.read_text(encoding='utf-8')):
                continue
            original = ra.read(expp)
            folded = ra.fold(original, holes=True)
            entry = {'manifest': manifest.name, 'test': t['@id'], 'file': exp}
            inp = root / t['input']
            if inp.suffix == '.html':
                report['toRdf-unchecked'].append(entry)
                ok = True
            else:
                try:
                    parsed = parse_jsonld(inp, base_iri + t['input'], option)
                except Exception as e:  # noqa: BLE001
                    entry['error'] = str(e)
                    report['error'].append(entry)
                    continue
                ok = ra.isomorphic(folded, parsed)
                if not ok and t['@id'] in KNOWN_PARSER_DIFFERENCES:
                    entry['note'] = KNOWN_PARSER_DIFFERENCES[t['@id']]
                    report['toRdf-unchecked'].append(entry)
                    ok = True
                elif not ok:
                    entry['folded'] = ra.write(folded)
                    entry['parsed'] = ra.write(parsed)
                    report['toRdf-review'].append(entry)
            if ok and folded != original:
                if inp.suffix != '.html':
                    report['toRdf-rewritten'].append(entry)
                if write:
                    expp.write_text(leading_comments(expp) + ra.write(folded), encoding='utf-8')
    json.dump(report, sys.stdout, indent=1)
    print()


if __name__ == '__main__':
    main()
