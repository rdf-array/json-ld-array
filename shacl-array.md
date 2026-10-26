# SHACL-array: SHACL over rdf-array

*Definition, 2026-10-25. Implemented in [jena-array](https://github.com/rdf-array/jena-array)'s
`jena-shacl`. This document is [shacl-array.md](https://github.com/rdf-array/rdf-array) in the
organisation's meta-repository, rendered at
<https://rdf-array.github.io/rdf-array/shacl-array.html>; [rdf-array.md](rdf-array.html) describes
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
   counterpart of ShEx-array's Collection shape expression, `((shapeExpr))[min, max]`.

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

An RGB colour, in ShEx-array `((xsd:integer MININCLUSIVE 0 MAXINCLUSIVE 255))[3]`:

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
  them. SPARQL-array's position patterns (`((?e))[2]`, `[*]`) have no SHACL path counterpart, and
  SHACL-SPARQL constraints can use them where the engine has them.
- **No positional constraints.** Neither SHACL 1.2 nor SHACL-array can say "the first member is a
  string, the rest are integers". ShEx-array cannot say it either; it is an open question for both.
- **No new results vocabulary.** A sequence value appears in a report as itself: `sh:value ( 255 192 )`.

## 4. Tests

The W3C SHACL suites (`w3c/data-shapes`) are read with lists as sequences. These tests depend on
ladders, or on `rdf:nil` being the empty list. The SHACL 1.0 core ones are flagged in jena-array and
rudof-array; the SHACL 1.2 ones, which jena-shacl does not carry and rudof does not yet pass, need
rdf-array counterparts:

| Test | Why |
|---|---|
| `core/path/path-strange-001`, `-002` | the `sh:path` is an explicit `rdf:first`/`rdf:rest` ladder |
| `core/complex/shacl-shacl` | shacl-shacl's list shapes walk `rdf:rest*/rdf:first` over the shapes graph's lists, which are sequences |
| SHACL 1.2 `core/{node,property}/memberShape-001`, `maxListLength-001`, `uniqueMembers-001` | the data spells some lists as ladders, written with `rdf:first` and ending in `( … )` |
| SHACL 1.2 `core/{node,property}/minListLength-001`, `maxListLength-001`, `uniqueMembers-001` | `rdf:nil` as the empty list, which conforms to `sh:maxListLength` and `sh:uniqueMembers` there |
| SHACL 1.2 `node-expr/list` | expects `()` to be the constant `rdf:nil` |

Still to do: a `data-shapes-array` fork of w3c/data-shapes with these tests re-recorded and
shacl-shacl's list shapes rewritten with `sh:memberShape` over sequences. Its contrib sibling would
take the shared cases (as rdf-tests-contrib does for the syntaxes), starting from jena-array's
`jena-shacl/src/test/files/local/rdf-array/` manifests: sequence paths, `sh:in` and `sh:or`
sequences, the four list constraints, a ladder as a value, and `rdf:nil` as a value.

## 5. Implementations

| Implementation | Lists as sequences | List constraints | Notes |
|---|---|---|---|
| [jena-array](https://github.com/rdf-array/jena-array) `jena-shacl` | yes, sequences only | `sh:memberShape`, `sh:minListLength`, `sh:maxListLength`, `sh:uniqueMembers` | no `sh:detail`; compact syntax builds sequences; the W3C core suite passes except the three flagged tests |
| [rudof-array](https://github.com/rdf-array/rudof-array) `shacl` | yes, sequences only | not yet (rudof's own TODO) | flags `path-strange-001/002`, `shacl-shacl`, `node-expr/list` |
| pySHACL over rdflib-array, rdf-validate-shacl over the RDF/JS forks | not forked | — | [targets.md](https://github.com/rdf-array/rdf-array/blob/main/targets.md) |

[SHACL]: https://www.w3.org/TR/shacl/
[SHACL 1.2 Core]: https://www.w3.org/TR/shacl12-core/
