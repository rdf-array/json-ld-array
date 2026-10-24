# rdf-array: RDF with sequences as terms

*An overview, 2026-10-23. rdf-array was called RDF- ("RDF minus") until October 2026, and its
syntaxes Turtle-, SPARQL-, ShEx- and JSON-LD-; the forks were always `<project>-array`. Everything
here is a working spike, not a standard.*

rdf-array is RDF whose data model has one more kind of term, the **sequence**: `(1 2 3)` in Turtle
is one term holding three literals in order, `()` is the empty sequence, and a sequence may hold
terms of any kind, sequences included. Nothing else about RDF changes. This page says what changes
and what does not, how each syntax spells it, what the implementations do, and what is still open.
The organisation's [README](https://github.com/rdf-array/rdf-array) lists the repositories; each
fork has its own `doc/rdf-array.md` with the detail.

## Why

RDF 1.1 has no ordered collection in its data model. Turtle's `( … )` is sugar for a ladder of blank
nodes joined by `rdf:first` and `rdf:rest` and closed by `rdf:nil`: two triples and a blank node per
element, which SPARQL reaches with a property path (`rdf:rest*/rdf:first`) that forgets the order,
which SHACL (`sh:in`), OWL (`owl:unionOf`) and SKOS each had to interpret for themselves, which
JSON-LD can only produce from `@list`, and which the `rdf:Seq`, `rdf:Bag` and `rdf:Alt` containers
tried to do instead with numbered properties `rdf:_1`, `rdf:_2`, … The spike asks what RDF, its
syntaxes and its tools look like when the ordered collection is a term in its own right, as the
triple term became one in RDF 1.2.

## What changes

### The data model

- **Terms.** IRIs, blank nodes, literals, triple terms (RDF 1.2) and sequences. A sequence is a
  finite, ordered, possibly empty list of terms of any kind, sequences included. It is a value, as a
  literal is: two sequences are equal when their elements are equal, pairwise; it has no identity of
  its own, no triples are *about* it, and no blank node stands for it.
- **Positions.** A sequence may be the subject or the object of a triple, and an element of a
  sequence. It may not be a predicate or a graph name.
- **`rdf:first`, `rdf:rest`, `rdf:nil`.** They keep no special meaning: they are ordinary IRIs, and a
  triple using them is an ordinary triple. `()` is the empty sequence, not `rdf:nil`. The container
  vocabulary (`rdf:Seq`, `rdf:Bag`, `rdf:Alt`, `rdf:_n`, `rdfs:member`) is likewise plain IRIs; no
  syntax numbers membership properties any more (RDF/XML's `rdf:li` stays the property `rdf:li`).
- **Ordering.** Where terms are ordered (SPARQL `ORDER BY`, `<`), sequences come after literals and
  triple terms and are compared element by element, a shorter prefix first.
- **Blank nodes inside sequences** are ordinary blank nodes: `( [ :p 1 ] )` is a sequence holding a
  blank node that also has a triple. Graph isomorphism has to canonicalize blank nodes inside
  sequences too, which stock tools do not yet (see [Open questions](#open-questions)).

### The sequence in code

| Implementation | The term | Making one | Spelling of `value` |
|---|---|---|---|
| Apache Jena ([jena-array](https://github.com/rdf-array/jena-array)) | `Node_Seq`, a fifth `Node` kind | the sequence node factory | — |
| RDF/JS ([types-array](https://github.com/rdf-array/types-array), [rdf-data-factory-array](https://github.com/rdf-array/rdf-data-factory-array), [N3.js-array](https://github.com/rdf-array/N3.js-array)) | `{ termType: "Sequence", elements: readonly Term[], value }`, a member of `Term`, `Quad_Subject` and `Quad_Object` | `DataFactory.sequence(elements)` | `(e1 e2 …)`, the elements in N-Triples spelling: `(<http://a> "x" (1 2))` |
| RDFLib ([rdflib-array](https://github.com/rdf-array/rdflib-array)) | `rdflib.term.Sequence`, with `.elements` | `Sequence(elements)` | the Turtle spelling |

The RDF/JS helpers that recurse into triple terms (`rdf-terms`'s `*Nested` functions, `rdf-string`'s
`termToString` and `stringToTerm`) recurse into sequences the same way; a nested path key may be a
quad component name or an element index.

### SPARQL results

| Format | A sequence binding |
|---|---|
| SPARQL Results JSON | `{ "type": "seq", "value": [ …one binding object per element… ] }` |
| SPARQL Results XML | `<seq>` with one child element per element (`<uri>`, `<literal>`, `<bnode>`, `<triple>`, a nested `<seq>`) |
| CSV | the sequence as one cell, `("1" http://a.example/o (…))`, quoted once |
| TSV | the Turtle spelling |

### Concrete syntaxes

**Turtle-array, TriG-array, N-Triples-array, N-Quads-array.** `( e1 e2 … )` is a term wherever a
subject or an object may stand, nested freely; `()` is the empty sequence. N-Triples and N-Quads use
the same spelling on one line. A Turtle document written for RDF 1.1 therefore means something new
under rdf-array: its collections are sequences, not ladders.

**SPARQL-array.** A collection in a triple pattern, a CONSTRUCT template or INSERT/DELETE DATA is one
sequence term. A variable inside a pattern's sequence is bound from the corresponding element of a
matching sequence, nested sequences included, and a repeated variable must match equal elements. A
**position pattern** reaches elements by index:

```sparql
SELECT ?x ?o WHERE { ?s :p (?x (2 3) ?o) }    # binds ?x and ?o from a matching sequence
SELECT ?s WHERE { ?s :p () }                     # the empty sequence is a term
?s :p ((?e))[2]                                  # the 2nd element (1-based)
?s :p ((?e))[?i]                                 # every element, ?i bound to its position
?s :p ((?e))[*]                                  # every element
?s :p ((((?e))[1]))[2]                           # nested: the first element of the second
FILTER(isSEQ(?x) && SEQLEN(?x) = 3)              # functions, with SEQ(e1, …) and expr[i]
```

In expressions a sequence is a term of its own kind: `isIRI`, `isBlank`, `isLiteral` and `isTriple`
are false for it, `=` and `!=` compare whole sequences, `<` orders them as above, `STR()` spells
`(e1 e2 …)`. jena-array has all of this; comunica-array has the patterns, the ordering and the result
formats, not yet the functions. Whether an application wants a sequence or repeated properties is a
question about the RDF, answered by an update rather than by a syntax:

```sparql
DELETE { ?s :tags ?seq }  INSERT { ?s :tags ?tag }
WHERE  { ?s :tags ?seq . ?s :tags ((?tag))[*] }
```

**ShEx-array.** The **Collection shape expression** `((shapeExpr))[min, max]` matches a sequence
whose every element conforms to `shapeExpr` and whose length is within the bounds:

```shex
:Colour   { :rgb ((xsd:integer MININCLUSIVE 0 MAXINCLUSIVE 255))[3] }
:Polygon  { :points ((( xsd:decimal ))[2])[3,*] }
:Playlist { :tracks ((@<Track>))[1,*] }
:Anything { :seq ((.))[0,*] }
```

The shex.js, PyShEx and Jena ShEx implementations have it, with test-suite examples in
shex.js-array's webapp manifest.

**JSON-LD-array.** A mapping language for conventional JSON, specified in
[json-ld-array.md](json-ld-array.html): a JSON array is one sequence term, nested arrays nested
sequences, so JSON-LD's `@list` and `@set` containers are not needed; property maps, type maps,
lexically scoped bases and templates replace the flat `@context`. Implemented in
[jsonld.js-array](https://github.com/rdf-array/jsonld.js-array), which has a
[playground](https://rdf-array.github.io/jsonld.js-array/).

**JSON-LD as it is.** For the RDF/JS stack, the jsonld-streaming-parser fork reads a JSON-LD `@list`
as one sequence (nested lists as nested sequences) and the jsonld-streaming-serializer fork writes a
sequence as `@list`. jsonld.js's own `toRDF` is unchanged and still makes ladders; Components.js, the
dependency injection comunica is built with, reads its configuration lists through it.

**RDF/XML.** `rdf:parseType="Collection"` is one sequence, `()` when empty, and `rdf:ID` reification
or `rdf:annotation` applies to that one triple; `rdf:li` is no longer numbered into `rdf:_1`, `rdf:_2`,
…. RDFLib's RDF/XML, TriX and HexTuples writers refuse sequence terms rather than invent a spelling.

**Not touched.** SHACL (a sequence-valued `sh:in` has no reading yet), RDFa (`inlist` still builds a
ladder), the canonicalization algorithm RDFC-1.0 (no sequence term), N3 formulas (fine in RDFLib).

### Converting between RDF and rdf-array

Nothing converts automatically. Parsing an RDF 1.1 document with an rdf-array parser gives sequences
where it had collections and leaves any explicit `rdf:first`/`rdf:rest` triples as they are; parsing
an rdf-array document with an RDF 1.1 parser fails on `( … )` in the places RDF 1.1 does not allow it,
or silently makes a ladder. Folding ladders into sequences is beyond a single SPARQL-array update
(the fold recurses); CFGraph-array flattens both for ShEx validation, and a dedicated converter is
still to be written. Spreading a sequence into repeated properties is the update above; gathering
repeated properties back needs an aggregate.

## What does not change

Triples, graphs, datasets and their semantics; IRIs, blank nodes and literals; SPARQL's algebra apart
from the term kind and its position patterns; ShEx apart from the Collection shape expression; JSON-LD
1.1 itself (JSON-LD-array is a different mapping language, not a change to JSON-LD). An rdf-array
graph with no sequences is an RDF graph.

## Implementations

| Language | Project | What the fork does |
|---|---|---|
| Java | [jena-array](https://github.com/rdf-array/jena-array) | Apache Jena with the `Node_Seq` term: Turtle-array, SPARQL-array (patterns, position patterns, functions, results), ShEx-array; the `jena-rdfminus` demo server and page; `RDF-SEQUENCES-HANDOFF.md` tabulates the flagged tests |
| JavaScript | [shex.js-array](https://github.com/rdf-array/shex.js-array) with [N3.js-array](https://github.com/rdf-array/N3.js-array), [types-array](https://github.com/rdf-array/types-array), [lezer-turtle-array](https://github.com/rdf-array/lezer-turtle-array), [lezer-shexc-array](https://github.com/rdf-array/lezer-shexc-array) | ShEx-array validation in the browser and Node, with the Turtle-array and ShExC-array editor grammars; <https://rdf-array.github.io/shex.js-array/> |
| JavaScript | [comunica-array](https://github.com/rdf-array/comunica-array) with [traqula-array](https://github.com/rdf-array/traqula-array), [rdf-data-factory-array](https://github.com/rdf-array/rdf-data-factory-array), [rdf-string-array](https://github.com/rdf-array/rdf-string-array), [rdf-string-ttl-array](https://github.com/rdf-array/rdf-string-ttl-array), [rdf-terms-array](https://github.com/rdf-array/rdf-terms-array), [jsonld-streaming-parser-array](https://github.com/rdf-array/jsonld-streaming-parser-array), [jsonld-streaming-serializer-array](https://github.com/rdf-array/jsonld-streaming-serializer-array), [rdfxml-streaming-parser-array](https://github.com/rdf-array/rdfxml-streaming-parser-array), [sparqljson-parse-array](https://github.com/rdf-array/sparqljson-parse-array), [sparqlxml-parse-array](https://github.com/rdf-array/sparqlxml-parse-array) | the SPARQL-array engine over Turtle, JSON-LD and RDF/XML sources and remote endpoints, with the result formats; comunica-array's `doc/rdf-array.md` has the stack table |
| JavaScript | [jsonld.js-array](https://github.com/rdf-array/jsonld.js-array) | JSON-LD-array: `jsonld.arrayToRDF`, writers for N-Quads-array and Turtle-array, the [playground](https://rdf-array.github.io/jsonld.js-array/) |
| Python | [PyShEx-array](https://github.com/rdf-array/PyShEx-array) with [rdflib-array](https://github.com/rdf-array/rdflib-array), [grammar-python-antlr-linkml-array](https://github.com/rdf-array/grammar-python-antlr-linkml-array) (the `pyshexc` parser), [ShExJSG-array](https://github.com/rdf-array/ShExJSG-array), [CFGraph-array](https://github.com/rdf-array/CFGraph-array) | ShEx-array validation over RDFLib with `rdflib.term.Sequence`; RDFLib's Turtle, N-Triples, N3, JSON-LD and SPARQL read and write sequences |
| Specification | [rdf-array](https://github.com/rdf-array/rdf-array) | this overview, the JSON-LD-array specification and its brief |

## Conventions of the organisation

- A fork is named `<project>-array` and works on a branch `rdf-sequences`, which is its default
  branch; `origin` is the fork and `upstream` the original.
- Its README opens with a banner, "`<project>-array`: `<project>` for rdf-array", beside an icon that
  puts the original's avatar between big `[` `]` brackets (`.github/rdf-array-logo.{png,svg}`), and
  its notes live in `doc/rdf-array.md`.
- Commit messages start with `rdf-array:` (older ones with `RDF-:`); repository descriptions likewise.
- A test that depends on `rdf:first`/`rdf:rest` ladders is flagged with the reason, never silently
  dropped, and gets an rdf-array counterpart where one makes sense.
- Dependencies that had to learn the term are forked too and pinned from the dependent fork (yarn
  `resolutions`, npm `overrides`, `[tool.uv.sources]`); JavaScript forks commit their compiled output
  so that a git dependency installs without a build.

## Open questions

- **A placeholder element.** JSON `null` inside an array leaves no element, which shifts the
  positions after it; rdf-array has no term to hold a place.
- **Blank nodes inside sequences.** `rdf-isomorphic` and the canonicalization algorithms do not look
  inside sequences, so two graphs that differ only in blank node labels inside sequences are not
  recognised as isomorphic; tests compare such cases by hand.
- **Sequences as subjects** are allowed; JSON-LD-array cannot write them (no `@id` for a value), and
  nothing yet needs them.
- **Containers.** `rdf:Seq`, `rdf:Bag` and `rdf:Alt` keep their vocabulary but lose the only syntax
  that produced them (`rdf:li`); whether a sequence should ever be read as a bag or an alternative is
  open.
- **SHACL, OWL, SKOS.** Each reads collections as ladders; their rdf-array readings are not written.
- **Specification test suites.** The W3C SPARQL, JSON-LD, RDF/XML and Turtle suites spell ladders in
  their expected output; the forks skip or re-record those tests with an rdf-array reason, and no
  suite expresses the rdf-array expectations yet.
- **Interchange with RDF 1.1 systems.** Until a converter exists, an rdf-array document is readable
  only by rdf-array tools; the same was true of RDF-star documents for a while.
