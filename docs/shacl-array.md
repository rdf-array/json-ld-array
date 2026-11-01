# SHACL-array: SHACL over rdf-array

*Definition, 2026-10-25. Implemented in [jena-array](https://github.com/rdf-array/jena-array)'s
`jena-shacl`. This document is [shacl-array.md](https://github.com/rdf-array/rdf-array) in the
organisation's meta-repository, rendered at
<https://rdf-array.github.io/rdf-array/docs/shacl-array.html>; [rdf-array.md](rdf-array.html) describes
the change from RDF to rdf-array, and [rdf-array#9](https://github.com/rdf-array/rdf-array/issues/9)
holds the discussion this settles.*

SHACL-array is SHACL ([SHACL], with the list constraints of [SHACL 1.2 Core]) over the rdf-array
data model, in which `( … )` is one term, a *sequence*, and `()` is the empty sequence. It changes
two things and adds no vocabulary:

1. **A SHACL list is a sequence term.** Everywhere SHACL reads a list from the shapes graph, it reads
   a sequence. An `rdf:first`/`rdf:rest` ladder spelled out in triples is triples, not a list, and
   `rdf:nil` is an IRI like any other.
2. **SHACL 1.2's list constraints apply to sequence values.** `sh:memberShape`, `sh:minListLength`,
   `sh:maxListLength` and `sh:uniqueMembers` constrain a value node that is a sequence. They are the
   counterpart of ShEx-array's LIST shape expression, `LIST {min,max} shapeExpr`
   ([array-syntax.md](array-syntax.html)).

## 1. Lists in the shapes graph

These parameters take a SHACL list, which in SHACL-array is a sequence term:

| Parameter | In Turtle-array |
|---|---|
| `sh:path` (a sequence path) | `sh:path ( ex:parent ex:name )` |
| `sh:alternativePath` | `sh:path [ sh:alternativePath ( ex:father ex:mother ) ]` |
| `sh:in` | `sh:in ( "red" "green" "blue" )` |
| `sh:languageIn` | `sh:languageIn ( "en" "fr" )` |
| `sh:and`, `sh:or`, `sh:xone` | `sh:or ( [ sh:datatype xsd:string ] [ sh:datatype rdf:langString ] )` |
| `sh:ignoredProperties` | `sh:ignoredProperties ( rdf:type )` |
| SHACL 1.2 list node expressions | `( ex:a ex:b )`, and `()` the empty list |

Written in Turtle-array these are sequences already: the syntax is unchanged, and a shapes graph
written for SHACL reads the same under SHACL-array. Three consequences:

- **A ladder is not a list.** A shapes graph that spells a list as `rdf:first`/`rdf:rest` triples
  (in N-Triples written by an RDF 1.1 tool, say) is ill-formed where a list is expected, and a
  processor reports a shapes-graph error. Convert it first. A ladder read as triples is no longer
  special anywhere in rdf-array.
- **`()` is the empty list; `rdf:nil` is not.** `sh:path ()` is an error, as an empty sequence path
  was before. `sh:path rdf:nil` is the predicate path of the IRI `rdf:nil`.
- **Lists hold no blank-node structure.** A shape inside a list, `sh:or ( [ … ] )`, is a blank node
  that is an element of the sequence; its own triples are ordinary triples of the shapes graph.

The same holds for what a processor writes: `sh:resultPath` of a sequence path is a sequence term,
and SHACL compact syntax arrays (`in=[ 1 2 ]`, `|` alternatives) produce sequences.

## 2. Sequence-valued data

SHACL 1.2 Core defines four constraint components for "SHACL lists" in the data graph. In
SHACL-array a SHACL list in the data is a sequence term, so they constrain sequence values:

| Parameter | A value node conforms when it is a sequence and … |
|---|---|
| `sh:memberShape S` | every member conforms to the node shape `S` |
| `sh:minListLength n` | it has at least `n` members |
| `sh:maxListLength n` | it has at most `n` members |
| `sh:uniqueMembers true` | no member occurs twice (by RDF term equality); `false` constrains nothing |

A value node that is not a sequence violates each of them. That includes an IRI, a literal,
`rdf:nil`, and a blank node at the head of a ladder. Each violating value node gives one result:
`sh:value` is the value node (the sequence) and `sh:resultPath` the path that reached it. SHACL 1.2
also lists the failing members as `sh:detail`; jena-array does not emit `sh:detail` yet.

An RGB colour, in ShEx-array `LIST {3} xsd:integer MININCLUSIVE 0 MAXINCLUSIVE 255`:

```turtle
PREFIX ex:  <http://example/>
PREFIX sh:  <http://www.w3.org/ns/shacl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ex:ColourShape a sh:NodeShape ;
  sh:targetClass ex:Swatch ;
  sh:property [
    sh:path ex:rgb ;
    sh:minCount 1 ; sh:maxCount 1 ;
    sh:minListLength 3 ; sh:maxListLength 3 ;
    sh:memberShape [ sh:datatype xsd:integer ; sh:minInclusive 0 ; sh:maxInclusive 255 ]
  ] .

ex:red  a ex:Swatch ; ex:rgb ( 255 0 0 ) .    # conforms
ex:pink a ex:Swatch ; ex:rgb ( 255 192 ) .    # too short: MinListLength
ex:blue a ex:Swatch ; ex:rgb ( 0 0 256 ) .    # 256 out of range: MemberShape
```

A playlist whose tracks are each a `ex:Track` with a title, and which never repeats a track:

```turtle
ex:PlaylistShape a sh:NodeShape ;
  sh:targetClass ex:Playlist ;
  sh:property [
    sh:path ex:tracks ;
    sh:minListLength 1 ;
    sh:uniqueMembers true ;
    sh:memberShape [ sh:class ex:Track ;
                     sh:property [ sh:path ex:title ; sh:minCount 1 ] ]
  ] .
```

`sh:minCount` and `sh:maxCount` keep counting values: `ex:rgb ( 255 0 0 )` is one value. Nested
sequences are members like any other, so a polygon of points is
`sh:memberShape [ sh:minListLength 2 ; sh:maxListLength 2 ; sh:memberShape [ sh:datatype xsd:decimal ] ]`.

## 3. What SHACL-array does not add

- **No path into a sequence.** SHACL property paths reach value nodes through triples, and a
  sequence's members are not reached through triples. `sh:memberShape` is the way to constrain
  them. SPARQL-array's gaps and `UNNEST` (`( ... ?e ... )`, `UNNEST(?seq AS ?e AT ?i)`) have no SHACL path
  counterpart, and
  SHACL-SPARQL constraints can use them where the engine has them.
- **No positional constraints.** Neither SHACL 1.2 nor SHACL-array can say "the first member is a
  string, the rest are integers". ShEx-array cannot say it either; it is an open question for both.
- **No new results vocabulary.** A sequence value appears in a report as itself: `sh:value ( 255 192 )`.

## 4. Tests

[data-shapes-array](https://github.com/rdf-array/data-shapes-array) is the W3C SHACL 1.0 and 1.2 test
suites (`w3c/data-shapes`) read as SHACL-array, following the rules of the other suite forks: no test
deleted, expectations changed and inputs not, every changed test with an `rdfs:comment "rdf-array: …"`.
A test with nothing left to test is marked `mf:status sht:rejected`, the SHACL test vocabulary's status
for a test not to run. Its `doc/rdf-array.md` has the details:

| Test | Under SHACL-array |
|---|---|
| 1.0 `core/path/path-strange-001` | re-recorded: the ladder on the path node is ordinary triples, so the path is the inverse path `^ex:p` |
| 1.0 `core/path/path-strange-002` | rejected: without the ladder only a one-member sequence path is left, which SHACL does not allow |
| 1.0 and 1.2 `core/complex/shacl-shacl` | shacl-shacl itself rewritten: `sh:memberShape` and `sh:minListLength` instead of `rdf:rest*/rdf:first` (`tools/rewrite-shacl-shacl.py`); the test requires `ra:ShaclListConstraints` |
| 1.2 `core/property/memberShape-001`, `maxListLength-001`, `uniqueMembers-001` | re-recorded: ladders and `rdf:nil` are not lists, so they violate as non-lists |
| 1.2 `core/node/memberShape-001`, `minListLength-001`, `maxListLength-001`, `uniqueMembers-001` | rejected: their focus nodes are IRIs spelled as ladders, and an IRI is never a sequence |
| 1.2 `core/node/in-003`, `xone-003` | rejected: `sh:in rdf:nil` and `sh:xone rdf:nil` make the shapes graph ill-formed |
| 1.2 `node-expr/shnex/list` `list-empty` | re-recorded: `()` is a list expression with no members and outputs nothing |

Its sibling [data-shapes-contrib](https://github.com/rdf-array/data-shapes-contrib) holds 21 tests no W3C
suite has, in the same layout, seeded from jena-array's own: sequence paths (nested in alternative
paths), `rdf:nil` as a predicate path, and ladders and `()` where a list is expected (`sht:Failure`).
Under `sh:in`, `sh:or`, `sh:languageIn` and `sh:ignoredProperties` they hold sequences, and `sh:in ()`
and `sh:xone ()` are the counterparts of the rejected `in-003` and `xone-003`. The four list constraints
appear on property values and on focus nodes that are sequences (the counterparts of the rejected
node-level tests), together with this document's colour, playlist and polygon. Its `bin/build.py` takes
each expectation from jena-array and requires rudof-array to agree wherever it has the feature. The
vocabulary adds [`ra:ShaclListConstraints`](https://rdf-array.github.io/rdf-array/vocab/#ShaclListConstraints)
for tests that need the list constraints.

## 5. Implementations

| Implementation | Lists as sequences | List constraints | Suites |
|---|---|---|---|
| [jena-array](https://github.com/rdf-array/jena-array) `jena-shacl` | yes, sequences only | `sh:memberShape`, `sh:minListLength`, `sh:maxListLength`, `sh:uniqueMembers`; no `sh:detail` | data-shapes-array's SHACL 1.0 core suite and SHACL 1.2's list tests, and data-shapes-contrib: TC_SHACL 272 pass, 5 skipped (the rejected tests); compact syntax builds sequences |
| [rudof-array](https://github.com/rdf-array/rudof-array) `shacl` | yes, sequences only | not yet (rudof's own TODO) | data-shapes-array: path-strange-001 and node-expr `list` pass, `shacl-shacl` and `path-strange-002` ignored; data-shapes-contrib: 6 pass, 15 ignored. Divergences: [rdf-array#17](https://github.com/rdf-array/rdf-array/issues/17) |
| pySHACL over rdflib-array, rdf-validate-shacl over the RDF/JS forks | not forked | — | [targets.md](https://github.com/rdf-array/rdf-array/blob/rdf-sequences/management/targets.md) |

[SHACL]: https://www.w3.org/TR/shacl/
[SHACL 1.2 Core]: https://www.w3.org/TR/shacl12-core/
