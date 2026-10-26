# Further `-array` targets: impact and utility

*An assessment, 2026-10-24, of which other RDF implementations are worth teaching the sequence
term, and in what order. Written from the experience of the existing forks and from what the
candidate code bases looked like at the time of writing; the "where the term goes" lists are what to
verify first when a fork starts.*

**Impact** here is what a fork has to change: how many places the term must reach (data model,
parsers, storage or index, query engine, result formats, language bindings), how invasive each is,
and how far the fork drifts from upstream, which is what it costs to keep rebasing. **Utility** is
what the fork buys rdf-array: users reached, capabilities shown for the first time, gaps closed, and
how much it unblocks. Both are scored 1 (small) to 5 (large). The forks so far cost roughly: a term
in a data-model library, days; a parser or serializer, days; a SPARQL engine, weeks.

## The list

The targets, ticked as their forks appear and in the recommended order, are listed in the
README under [Not yet forked](README.md#not-yet-forked); the forks that exist are the README's
[Repositories](README.md#repositories). The table this section held, with each target's language,
impact, utility, needed forks and order, was moved there on 2026-10-25. Done so far: Oxigraph
(oxigraph-array, 2026-10-24) and rudof (rudof-array, 2026-10-25). The sections below are the
assessment as it was written.

Two things that are not implementations rank above most of the list: a **conformance suite**
(impact 3, utility 5) assembled from the tests the forks already carry, so that the next port does
not re-derive its expectations from jena-array's and comunica-array's test files; and a
**converter** between ladders and sequences (impact 2, utility 4), without which rdf-array data
cannot meet RDF 1.1 systems at all (the open question in [rdf-array.md](rdf-array.html)). The
conformance suite now exists, as the `*-contrib` repositories, which jena, comunica, N3.js,
shex.js, jsonld.js, rdflib, PyShEx, oxigraph and rudof run (2026-10-25); the converter does not.

## Oxigraph: the foundation for Rust, Python and WASM

Oxigraph is a family of crates whose boundaries match the JavaScript forks one to one, which is why
it is the cheapest large win: `oxrdf` is types-array and rdf-data-factory-array (a `Term` enum of
`NamedNode`, `BlankNode`, `Literal` and, with the `rdf-12` feature, `Triple`), `oxttl` is
N3.js-array (Turtle, TriG, N-Triples, N-Quads, N3 parsers and writers), `oxrdfxml` and `oxjsonld`
are the RDF/XML and JSON-LD forks, `oxrdfio` the format dispatcher, `spargebra` is traqula-array
(SPARQL parser and algebra, with `TermPattern` and `GroundTerm` enums), `sparesults` is
sparqljson-parse-array and sparqlxml-parse-array (JSON, XML, CSV, TSV readers and writers),
`sparopt` the optimizer, and `oxigraph` is comunica-array plus a store: an in-memory or RocksDB
quad store with an `EncodedTerm` representation in which RDF-star's `Triple` already shows how a
compound term is nested into keys. rudof pins the family at oxigraph 0.5.9 and oxrdf 0.3.3.

Where the term goes:

- `oxrdf`: a `Term::Sequence(Vec<Term>)` variant, `Subject::Sequence`, the N-Triples-style
  `Display`, equality and ordering by elements; the compiler then lists every `match` to update,
  which is the opposite of the JavaScript experience, where a missed case is a runtime surprise.
- `oxttl`: the Turtle and TriG state machines build a sequence where they now emit the ladder;
  N-Triples and N-Quads accept `( … )` as a term; the writers print it.
- `oxrdfxml`, `oxjsonld`: what rdfxml-streaming-parser-array and the jsonld-streaming forks did.
- `spargebra`: `TermPattern::Sequence(Vec<TermPattern>)`, the algebra translation of a collection
  (today a blank node ladder in the BGP), position patterns `((?e))[i]` as a new pattern kind.
- `sparesults`: the `seq` binding in JSON and XML, the CSV and TSV spellings.
- `oxigraph`: `EncodedTerm::Sequence` encoded into keys as `Triple` is; matching a pattern that
  holds a sequence with variables by scanning with that position open and matching elements
  afterwards, as comunica-array does; ordering in `ORDER BY`; the SPARQL functions `isSEQ`,
  `SEQLEN`, `expr[i]` if wanted. SPARQL Update comes for free once the parser and store know the
  term.
- `pyoxigraph` and the JS/WASM package: a `Sequence` class in each binding and the conversions.

Impact 4: eleven crates, but the change is the same shape in each, and the `Triple` variant is a
worked precedent for every one of them. Utility 5: one fork gives Rust, Python (pyoxigraph is the
fastest RDF library many Python users have) and the browser a SPARQL-array engine with a persistent
store and Update, and it is the ground rudof stands on.

## rudof: ShEx-array and SHACL-array in Rust

rudof (`~/checkouts/rudof-project/rudof`, a workspace of `shex_ast`, `shex_validation`,
`shex_testsuite`, `shacl`, `rbe`, `rudof_rdf`, `rudof_lib`, `rudof_cli`, `shapemap_oxgraph`,
`shapes_converter`, `dctap`, `sparql_service` and Python, WASM and Emacs `bindings`, among others)
reads RDF through the Oxigraph crates and validates ShEx with its regular bag expression engine
`rbe`. The
ShEx-array part is what shex.js-array and PyShEx-array did: the Collection shape expression
`((shapeExpr))[min, max]` in the ShExC parser and the ShExJ structures, and a validation rule that
takes a sequence-valued node, checks the bounds and validates each element against the inner
expression. The rest is wiring the forked `oxrdf` term through rudof's RDF abstraction. The `shacl`
crate is the natural second home of SHACL-array (below). Impact 3; utility 4, since rudof ships a
CLI, Python bindings and a WASM playground, and because it is the implementation whose maintainers
the project already works with. It cannot start before oxrdf and oxttl are forked; it does not need
the store.

## SHACL-array: a reading, then a cheap first implementation

Every SHACL shapes graph is built on RDF lists: `sh:path ( … )` for sequence paths, `sh:in`,
`sh:languageIn`, `sh:and`, `sh:or`, `sh:xone`, `sh:ignoredProperties`. Written in Turtle-array, those
lists are sequences, and no SHACL engine can read them; written in RDF 1.1 Turtle they are ladders
and no rdf-array tool recognises them. SHACL-array therefore needs a definition before an
implementation: the shapes-graph lists read as sequences (mechanical), and a constraint for
sequence-valued data, the counterpart of ShEx-array's Collection shape expression — a shape for the
elements with `sh:minCount`-like bounds, which SHACL's vocabulary does not have. The first
implementation is cheapest in jena-array, whose `jena-shacl` module is untouched so far and whose
data model already has the term: impact 2 there, 2–3 in pySHACL (over rdflib-array) and in
rdf-validate-shacl (over the RDF/JS forks), 2 in rudof's `shacl` crate once rudof-array exists.
Utility 5: SHACL is where most validation happens, and the gap is total today.

## Canonicalization and isomorphism

RDFC-1.0 (rdf-canonize in JavaScript, rdf-canon in Python, Jena's and Oxigraph's own) hashes quads
as N-Quads strings and issues blank node labels by hashing their neighbourhoods; a sequence must
be hashed through its elements, and a blank node inside a sequence must take part in the issuance
and be relabelled on output. rdf-isomorphic, which the JavaScript tests use, has the same blind
spot and is why four JSON-LD parser tests compare by hand. Impact 2 for rdf-isomorphic, 3 for
rdf-canonize (the algorithm's hashing steps, and its `rdf-canonize-native` twin); utility 4, both
for the test infrastructure of every JavaScript fork and for signing rdf-array data (verifiable
credentials are canonicalized before signing).

## QLever: the scale showcase

QLever is a C++ engine that builds a compressed index from Turtle or N-Triples and answers SPARQL
over it at Wikidata scale. Its design is what makes the fork big: terms are 64-bit ids with
datatype tags (vocabulary index, local vocabulary, int, double, date, bool, blank node, geo point,
text record), the vocabulary is a sorted, compressed string table whose order defines term
ordering, triples live in six permutations of compressed blocks, the Turtle parser is its own, the
SPARQL parser is an ANTLR grammar with a visitor that expands collections into ladders, and query
results are exported by its own writers. The term would go into the vocabulary as its canonical
spelling, so whole-sequence equality, joins and `ORDER BY` fall out once the comparator orders `(`
after literals; but reaching *inside* a sequence — `?s :p (?x 2)`, `((?e))[?i]` — needs either
decoding vocabulary strings at query time, which is slow, or an auxiliary permutation of (sequence,
position, element) built at index time, which is a new index structure in the planner. There is no
RDF-star precedent to follow. Impact 5; utility 4: the only way to show rdf-array at the scale
where people stop asking whether ladders really cost anything, with an HTTP endpoint and a UI
(QLever UI) on top. A project of its own, best started once the model has stopped moving.

## RDF4J

The other Java stack: a `Value` hierarchy with `Triple` for RDF-star, Rio parsers and writers,
JavaCC SPARQL parser, the SAIL storage layer (memory, native, LMDB) with its own value encodings,
ShaclSail, and GraphDB and other products built on it. Everything jena-array touched has a
counterpart, and the SAIL encodings add what jena-array did not have to do. Impact 4–5; utility 3:
Java is already served, so the gain is RDF4J's users and ShaclSail, worth it only after SHACL-array
is defined and if an RDF4J-based tool asks for it.

## The second RDF/JS stack, and rdflib.js

Zazuko's packages (`@rdfjs/data-model`, `@rdfjs/dataset`, `rdf-ext`, `@zazuko/env`, `clownface`,
`rdf-validate-shacl`, `barnard59`) are the other way JavaScript does RDF; each is small, most reuse
N3.js for parsing, and types-array already declares the term. Impact 2 per package over perhaps a
dozen packages; utility 3, chiefly for rdf-validate-shacl, which would be SHACL-array in JavaScript.
rdflib.js, Solid's library, is a special case: it already has a `Collection` term kind, kept for
N3's sake, which its parser builds and its serializer prints as `( … )`; making it a term that is
never expanded is closer to the model than any other library starts. Impact 3 (its own parsers and
store), utility 3 (the Solid ecosystem).

## Mappings, clients and user interfaces

Morph-KGC is the RML engine over RDFLib; RML-CC's `rml:gatherAs` names the collection or container
to build, and `rdf-array:Sequence` as a further value would make RML the second mapping language
into rdf-array, through rdflib-array, at impact 2. SPARQLWrapper needs almost nothing, since
rdflib-array already reads `seq` bindings, and Yasgui would need the position-pattern tokens in
Yasqe and a `seq` renderer in Yasr; both matter once there is an endpoint to point them at, which
jena-array's Fuseki can provide today for the cost of deploying it.

## Not targets

Virtuoso, GraphDB, Stardog, AllegroGraph and Neptune are commercial, closed or both; Blazegraph is
unmaintained; Raptor and Redland are C libraries whose users have moved on; the OWL API and Protégé
would be a large fork for a language whose lists (`owl:unionOf`, `owl:intersectionOf`,
`owl:oneOf`) do deserve an rdf-array reading, but not before SHACL has one. Sophia duplicates what
Oxigraph gives Rust.

## What to do first

1. ~~Extract a conformance suite from the forks' tests (Turtle-array, SPARQL-array, ShEx-array,
   JSON-LD-array, results formats), so that each port below starts from shared expectations.~~
   Done: rdf-tests-contrib, json-ld-api-contrib and shexTest-contrib, run by jena, comunica,
   N3.js, shex.js, jsonld.js, rdflib, PyShEx, oxigraph and rudof (2026-10-25; each fork's notes
   have its counts and skips). The W3C suite forks and the parser forks' runners still to wire
   are tracked in [rdf-array#3](https://github.com/rdf-array/rdf-array/issues/3).
2. ~~Fork the Oxigraph family, data model and parsers first, then `spargebra` and `sparesults`, then
   the store; publish pyoxigraph-array and the WASM package.~~ Done: oxigraph-array (2026-10-24);
   the Python and WASM packages build from it but are not published.
3. ~~Fork rudof on top of it, with ShEx-array;~~ done: rudof-array (2026-10-25). Define SHACL-array
   and implement it in jena-shacl, then in rudof's `shacl`, whose lists rudof-array already reads as
   sequences.
4. Fork rdf-isomorphic and rdf-canonize, and switch the JavaScript forks' tests to them.
5. Deploy a Fuseki-array endpoint and point Yasgui and SPARQLWrapper at it.
6. Fork QLever when the model is stable enough to carry a C++ index design.
