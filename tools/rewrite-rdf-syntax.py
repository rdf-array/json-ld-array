#!/usr/bin/env python3
"""Rewrite the RDF syntax suites of rdf-tests-array for rdf-array.

    python3 rewrite-rdf-syntax.py ~/checkouts/rdf-array/rdf-tests-array [--write] [--parser jena|rdfxml]

For every evaluation test (rdft:Test{Turtle,TriG,NTriples,NQuads,XML}Eval) in the manifests under
rdf/rdf11 and rdf/rdf12, read the expected result. When it mentions rdf:first, rdf:rest or rdf:nil,
or (RDF/XML) an rdf:_n membership property, compute two readings:

  folded  the expected result with its ladders folded into sequences (tools/rdfarray.py fold);
  parsed  what an rdf-array parser reads from the test's action, with the test's base
          (jena-array for Turtle, TriG, N-Triples, N-Quads; rdfxml-streaming-parser-array for RDF/XML).

When they are isomorphic, the folded reading is the new expectation. When they differ, the test is
reported for review: the difference is either explicit use of the ladder vocabulary in the input
(nothing to rewrite), rdf:li no longer numbered (the parsed reading is right), or a bug.
With --write, agreed rewrites are written in place and a report goes to stdout.
"""
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rdfarray as ra  # noqa: E402

MF = 'http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#'
RDFT = 'http://www.w3.org/ns/rdftest#'
EVAL = {RDFT + t for t in ('TestTurtleEval', 'TestTrigEval', 'TestNTriplesEval', 'TestNQuadsEval', 'TestXMLEval')}
JAVA = '/opt/homebrew/opt/openjdk@21/bin/java'
JT = os.environ.get('JENA_ARRAY_TOOL', str(HERE.parent / '.tools'))  # dir holding JenaArray.class + cp.txt
RDFXML_JS = HERE / 'parse-rdfxml-array.js'


def jena_parse(path, base):
    cp = open(os.path.join(JT, 'cp.txt')).read().strip()
    out = subprocess.run([JAVA, '-cp', f'{JT}:{cp}', 'JenaArray', 'parse', str(path), base],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip().splitlines()[-1] if out.stderr.strip() else 'parse failed')
    return ra.parse(out.stdout)


def rdfxml_parse(path, base):
    out = subprocess.run(['node', str(RDFXML_JS), str(path), base], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip()[-300:])
    return ra.parse(out.stdout)


def manifests(root):
    for sub in ('rdf/rdf11', 'rdf/rdf12'):
        for p in sorted((root / sub).rglob('manifest.ttl')):
            yield p


def tests_of(manifest):
    quads = jena_parse(manifest, manifest.as_uri())
    by = {}
    base = None
    for s, p, o, g in quads:
        by.setdefault(s, {}).setdefault(p[1], []).append(o)
        if p[1] == MF + 'assumedTestBase':
            base = o[1]
    for node, props in by.items():
        types = {t[1] for t in props.get(ra.TYPE, [])}
        if not (types & EVAL) or MF + 'result' not in props:
            continue
        action = props[MF + 'action'][0][1]
        result = props[MF + 'result'][0][1]
        yield node[1], types, action, result, base


def local(uri):
    assert uri.startswith('file://'), uri
    return pathlib.Path(uri[len('file://'):])


def mentions(path):
    text = path.read_text(encoding='utf-8')
    return any(x in text for x in ('22-rdf-syntax-ns#first', '22-rdf-syntax-ns#rest', '22-rdf-syntax-ns#nil')) \
        or '22-rdf-syntax-ns#_' in text


def leading_comments(path):
    """The comment block a W3C file starts with (copyright, provenance), kept on rewrite."""
    keep = []
    for line in path.read_text(encoding='utf-8').splitlines(keepends=True):
        if line.startswith('#') or not line.strip():
            keep.append(line)
        else:
            break
    return ''.join(keep)


def li_fix(quads, parsed):
    import itertools
    def numbered_iri(t):
        return t[0] == 'iri' and t[1].startswith(ra.RDF + '_')
    li = ra.iri(ra.RDF + 'li')
    # a numbered predicate, or the rdf:predicate of a reification naming one
    numbered = [i for i, q in enumerate(quads)
                if numbered_iri(q[1]) or (q[1] == ra.iri(ra.RDF + 'predicate') and numbered_iri(q[2]))]
    for k in range(1, len(numbered) + 1):
        for subset in itertools.combinations(numbered, k):
            trial = [(s, li if numbered_iri(p) else p, li if numbered_iri(o) and p == ra.iri(ra.RDF + 'predicate') else o, g)
                     if i in subset else (s, p, o, g)
                     for i, (s, p, o, g) in enumerate(quads)]
            if ra.isomorphic(trial, parsed):
                return trial
    return None


def main():
    root = pathlib.Path(sys.argv[1]).expanduser().resolve()
    write = '--write' in sys.argv
    report = {'rewritten': [], 'review': [], 'error': []}
    for manifest in manifests(root):
        mdir = manifest.parent
        for test, types, action, result, base in tests_of(manifest):
            res = local(result)
            if not res.exists() or not mentions(res):
                continue
            act = local(action)
            rel = act.relative_to(mdir).as_posix()
            test_base = (base or '') + rel
            is_xml = RDFT + 'TestXMLEval' in types
            try:
                parsed = rdfxml_parse(act, test_base) if is_xml else jena_parse(act, test_base)
            except Exception as e:  # noqa: BLE001
                report['error'].append({'test': test, 'error': str(e)})
                continue
            original = ra.read(res)
            folded = ra.fold(original)
            entry = {'test': test, 'result': res.relative_to(root).as_posix()}
            if is_xml and not ra.isomorphic(folded, parsed):
                # rdf:li is no longer numbered: find which rdf:_n triples the parser reads as rdf:li
                folded = li_fix(folded, parsed) or folded
            if ra.isomorphic(folded, parsed):
                if folded != original:
                    report['rewritten'].append(entry)
                    if write:
                        res.write_text(leading_comments(res) + ra.write(folded), encoding='utf-8')
            elif ra.isomorphic(original, parsed):
                entry['note'] = 'unchanged: the input uses the ladder vocabulary explicitly'
                report['review'].append(entry)
            else:
                entry['folded'] = ra.write(folded)
                entry['parsed'] = ra.write(parsed)
                report['review'].append(entry)
    json.dump(report, sys.stdout, indent=1)
    print()


if __name__ == '__main__':
    main()
