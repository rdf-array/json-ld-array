#!/usr/bin/env python3
"""Rewrite shacl-shacl (the SHACL shapes graph for SHACL shapes graphs) for SHACL-array.

    python3 tools/rewrite-shacl-shacl.py ~/checkouts/rdf-array/data-shapes-array [--write]

SHACL-array (shacl-array.md) reads every SHACL list as a sequence term, so shacl-shacl can no longer
walk lists with rdf:rest*/rdf:first. Its list checks become SHACL 1.2's list constraints, which SHACL
1.2's own shacl-shacl already uses for most list-valued parameters:

- shsh:ListShape ("a well-formed list") is sh:minListLength 0: any sequence, and nothing else.
  shsh:ListNodeShape, which described the cells of a ladder, goes.
- A member check reached through ( p [ sh:zeroOrMorePath rdf:rest ] rdf:first ) becomes
  sh:path p ; sh:memberShape [ … ].
- shsh:ShapesListShape's members are checked with sh:memberShape.
- A sequence path is a sequence term, not a blank node: its branch of shsh:PathNodeShape checks
  sh:memberShape shsh:PathShape and sh:minListLength 2 (as SHACL 1.2 already did, without the
  sh:nodeKind sh:BlankNode); shsh:PathListWithAtLeast2Members is sh:minListLength 2.
- _:PathPath, the path that reaches nested path nodes, loses its two list walks: sh:memberShape
  reaches a sequence path's members instead.

Applied to the SHACL 1.0 and 1.2 vocabularies (shacl/shacl-shacl.ttl, shacl12-vocabularies/shacl-shacl.ttl)
and to the copies the test suites validate against themselves (tests/core/complex/shacl-shacl-data-shapes.ttl).
Without --write it reports what would change. Each rewrite must apply exactly where expected.
"""

import re
import sys
from pathlib import Path

FILES = [
    'shacl/shacl-shacl.ttl',
    'data-shapes-test-suite/tests/core/complex/shacl-shacl-data-shapes.ttl',
    'shacl12-vocabularies/shacl-shacl.ttl',
    'shacl12-test-suite/tests/core/complex/shacl-shacl-data-shapes.ttl',
]

LIST_SHAPE = '''shsh:ListShape
\ta sh:NodeShape ;
\trdfs:label "List shape"@en ;
\trdfs:comment "rdf-array: a SHACL list is a sequence term, ( ... ), and an rdf:first/rdf:rest ladder is triples, not a list (https://rdf-array.github.io/rdf-array/shacl-array.html). shsh:ListNodeShape, which described the cells of a ladder, is gone."@en ;
\trdfs:seeAlso <https://www.w3.org/TR/shacl/#syntax-rule-SHACL-list> ;
\tsh:minListLength 0 .
'''


def rewrite(text):
    """Return the rewritten text and the names of the rewrites applied."""
    applied = []

    def sub(name, pattern, repl, count=1, optional=False):
        nonlocal text
        new, n = re.subn(pattern, repl, text, flags=re.S)
        if n != count and not (optional and n == 0):
            raise SystemExit(f'{name}: expected {count} match(es), found {n}')
        if n:
            applied.append(name)
        text = new

    # shsh:ListShape and shsh:ListNodeShape (ends at the sh:or list's closing ") .")
    sub('ListShape', r'shsh:ListShape\n.*?\nshsh:ListNodeShape\n.*?\t\t\t\] \) \.\n', LIST_SHAPE)

    # member checks through rdf:rest*/rdf:first (1.0 only; 1.2 already uses sh:memberShape)
    sub('ignoredProperties-members',
        r'sh:path \( sh:ignoredProperties \[ sh:zeroOrMorePath rdf:rest \] rdf:first \) ;\n(\t+)sh:nodeKind sh:IRI ;(\s*)# ignoredProperties-members-nodeKind',
        r'sh:path sh:ignoredProperties ;\n\1sh:memberShape [ sh:nodeKind sh:IRI ] ;\2# ignoredProperties-members-nodeKind (rdf-array: sh:memberShape)',
        optional=True)
    sub('languageIn-members',
        r'sh:path \( sh:languageIn \[ sh:zeroOrMorePath rdf:rest \] rdf:first \) ;\n(\t+)sh:datatype xsd:string ;(\s*)# languageIn-members-datatype',
        r'sh:path sh:languageIn ;\n\1sh:memberShape [ sh:datatype xsd:string ] ;\2# languageIn-members-datatype (rdf-array: sh:memberShape)',
        optional=True)
    sub('ShapesListShape',
        r'\tsh:property \[\n\t\tsh:path \( \[ sh:zeroOrMorePath rdf:rest \] rdf:first \) ;\n\t\tsh:node shsh:ShapeShape ;\n\t\] \.',
        '\tsh:memberShape shsh:ShapeShape .        # rdf-array: was the path ( [ sh:zeroOrMorePath rdf:rest ] rdf:first )',
        optional=True)

    # _:PathPath: the list walks go
    sub('PathPath',
        r'\t\t\( \[ sh:zeroOrMorePath rdf:rest \] rdf:first \)\n\t\t\( sh:alternativePath \[ sh:zeroOrMorePath rdf:rest \] rdf:first \)\n',
        '\t\t# rdf-array: the members of sequence and alternative paths are checked with sh:memberShape\n')

    # shsh:PathNodeShape's sequence and alternative branches
    sub('sequence-path-1.0',
        r'\[ sh:nodeKind sh:BlankNode ;    # 2\.3\.1\.2: Sequence path\n\t\t\t  sh:node shsh:PathListWithAtLeast2Members ;\n\t\t\t\]',
        '[                                 # 2.3.1.2: Sequence path (rdf-array: a sequence term)\n\t\t\t  sh:memberShape shsh:PathShape ;\n\t\t\t  sh:minListLength 2 ;\n\t\t\t]',
        optional=True)
    sub('alternative-path-1.0',
        r'sh:path sh:alternativePath ;\n\t\t\t    sh:node shsh:PathListWithAtLeast2Members ;',
        'sh:path sh:alternativePath ;\n\t\t\t    sh:memberShape shsh:PathShape ;\n\t\t\t    sh:minListLength 2 ;',
        optional=True)
    sub('PathListWithAtLeast2Members',
        r'shsh:PathListWithAtLeast2Members\n\ta sh:NodeShape ;\n\tsh:node shsh:ListShape ;\n\tsh:property \[\n\t\tsh:path \[ sh:oneOrMorePath rdf:rest \] ;\n\t\tsh:minCount 2 ;    # 1 other list node plus rdf:nil\n\t\] \.',
        'shsh:PathListWithAtLeast2Members\n\ta sh:NodeShape ;\n\tsh:minListLength 2 .    # rdf-array: a sequence of two or more members',
        optional=True)
    sub('sequence-path-1.2',
        r'\[ sh:nodeKind sh:BlankNode ;    # 2\.3\.1\.2: Sequence path\n',
        '[                                 # 2.3.1.2: Sequence path (rdf-array: a sequence term, not a blank node)\n',
        optional=True)
    return text, applied


def main():
    root = Path(sys.argv[1])
    write = '--write' in sys.argv
    for name in FILES:
        path = root / name
        text = path.read_text()
        new, applied = rewrite(text)
        left = re.findall(r'rdf:rest|rdf:first', new)
        print(f'{name}: {", ".join(applied)}; rdf:first/rdf:rest left: {len(left)}')
        if write and new != text:
            path.write_text(new)


if __name__ == '__main__':
    main()
