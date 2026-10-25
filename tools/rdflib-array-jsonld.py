#!/usr/bin/env python3
"""rdflib-array as a JSON-LD processor for cross-checks (run it with the rdf-array venv's python).

    rdflib-array-jsonld.py tordf FILE.jsonld BASE    print N-Quads-array
    rdflib-array-jsonld.py fromrdf FILE.nq           print expanded JSON-LD
"""
import json
import sys

import rdflib
from rdflib.term import BNode, Literal, Sequence, URIRef

XSD_STRING = 'http://www.w3.org/2001/XMLSchema#string'


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def nt(t):
    if isinstance(t, Sequence):
        return '(' + ' '.join(nt(e) for e in t.elements) + ')' if len(t.elements) else '()'
    if isinstance(t, URIRef):
        return f'<{t}>'
    if isinstance(t, BNode):
        return f'_:{t}'
    if isinstance(t, Literal):
        s = f'"{esc(str(t))}"'
        if t.language:
            return s + '@' + t.language
        if t.datatype and str(t.datatype) != XSD_STRING:
            return s + f'^^<{t.datatype}>'
        return s
    raise ValueError(repr(t))


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == 'tordf':
        ds = rdflib.Dataset()
        ds.parse(path, format='json-ld', publicID=sys.argv[3])
        for s, p, o, g in ds.quads():
            graph = '' if g is None or g == ds.default_context.identifier or str(g) == 'urn:x-rdflib:default' else ' ' + nt(g)
            print(f'{nt(s)} {nt(p)} {nt(o)}{graph} .')
    elif cmd == 'fromrdf':
        ds = rdflib.Dataset()
        ds.parse(path, format='nquads')
        print(ds.serialize(format='json-ld'))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
