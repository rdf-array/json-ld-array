---
name: w3c-test-suites
description: Which W3C and community test suites bear on rdf-array implementations (Turtle, TriG, N-Triples, N-Quads, RDF/XML, SPARQL 1.1 and 1.2, JSON-LD 1.1, ShEx, SHACL, RDF canonicalization), how to fork each as <suite>-array with rdf-array expectations and additions, and how every implementation runs them. Use when setting up, extending or re-running conformance testing for a fork.
---

# Test suites for rdf-array implementations

The forks' own tests are handled by the `array-tests` skill. This one covers the shared suites:
which exist, what rdf-array changes in each, how a suite is forked once so that every
implementation runs the same expectations, and how each implementation is pointed at the fork.

## 1. The suites

| Suite | Lives in | Manifests | Bears on |
|---|---|---|---|
| RDF 1.1 syntaxes: Turtle, TriG, N-Triples, N-Quads, RDF/XML, RDF semantics | [w3c/rdf-tests](https://github.com/w3c/rdf-tests) `rdf/rdf11/` | `rdf-turtle/manifest.ttl`, `rdf-trig/`, `rdf-n-triples/`, `rdf-n-quads/`, `rdf-xml/`, `rdf-mt/` | every parser and serializer fork; Jena and RDFLib vendor copies |
| RDF 1.2 syntaxes (triple terms, directional literals) | w3c/rdf-tests `rdf/rdf12/` | the same names | the forks with `rdf-12`/RDF-star support: N3.js, Oxigraph, Jena, traqula |
| SPARQL 1.1 | w3c/rdf-tests `sparql/sparql11/` | `manifest-all.ttl`; `data-sparql11/*/manifest.ttl` (syntax-query, syntax-update, the evaluation directories, `json-res`, `csv-tsv-res`, `protocol`) | traqula (syntax), comunica, Jena, RDFLib, Oxigraph, QLever (evaluation, results formats) |
| SPARQL 1.2 | w3c/rdf-tests `sparql/sparql12/` | likewise | the same, for triple terms with sequences |
| JSON-LD 1.1 API | [w3c/json-ld-api](https://github.com/w3c/json-ld-api) `tests/` | `toRdf-manifest.jsonld`, `fromRdf-manifest.jsonld`, `expand-`, `compact-`, `flatten-`, `html-` | jsonld.js, the jsonld-streaming forks, RDFLib's JSON-LD |
| JSON-LD framing and streaming | w3c/json-ld-framing `tests/`, w3c/json-ld-streaming `tests/` | `frame-manifest.jsonld`, `stream-toRdf-manifest.jsonld` | jsonld.js, jsonld-streaming-parser |
| JSON-LD-star | json-ld/json-ld-star `tests/` | `toRdf-manifest.jsonld` | jsonld-streaming-parser |
| ShEx | [shexSpec/shexTest](https://github.com/shexSpec/shexTest) | `validation/manifest.jsonld`, `schemas/manifest.jsonld`, `negativeSyntax/`, `negativeStructure/` | shex.js, PyShEx, Jena ShEx, rudof |
| SHACL | [w3c/data-shapes](https://github.com/w3c/data-shapes) `data-shapes-test-suite/tests/` | `core/manifest.ttl`, `sparql/manifest.ttl` | jena-shacl, pySHACL, rdf-validate-shacl, rudof — after SHACL-array is defined |
| RDF canonicalization (RDFC-1.0) | [w3c/rdf-canon](https://github.com/w3c/rdf-canon) `tests/` | `manifest.ttl` | rdf-canonize, Jena, Oxigraph — after sequences are canonicalized |
| SPARQL-array, ShEx-array, JSON-LD-array additions | this organisation (§4) | new manifests in the W3C formats | every implementation |

## 2. What rdf-array changes in each suite

The fold is always the same: wherever an expected output spells an `rdf:first`/`rdf:rest` ladder
for a collection, the expectation becomes one sequence term; wherever a test's *meaning* depended
on the ladder, the test is flagged and a counterpart added. Specifically:

- **Turtle, TriG.** Positive and negative syntax tests pass unchanged (a collection in predicate
  position is still an error). Evaluation tests whose expected `.nt` holds a ladder are re-recorded
  with `( … )`; the tests asserting that `()` is `rdf:nil` (and that `( )` yields no triples) are
  re-recorded to the empty sequence. New tests: nested collections, `()` as subject and object,
  a blank node property list inside a collection, a sequence inside a triple term and the reverse.
- **N-Triples, N-Quads.** Unchanged, plus new positive tests for the `( … )` term spelling and
  negative ones for it in predicate and graph positions.
- **RDF/XML.** The `rdf:parseType="Collection"` tests are re-recorded; the `rdf:li` tests, whose
  expected output has `rdf:_1`, `rdf:_2`, …, are re-recorded to `rdf:li` properties or flagged if the
  implementation chose to refuse `rdf:li`; the `rdf:aboutEach` and container tests stay as they are.
- **SPARQL 1.1 syntax.** Unchanged except where a test's point was the ladder expansion (none in
  the syntax suites; traqula-array passes 642 of 647, the five failures being trailing-`VALUES`
  tests that predate the fork). New syntax tests: position patterns, `()` in patterns, collections
  in `CONSTRUCT` templates and `INSERT DATA`.
- **SPARQL 1.1 evaluation.** Tests whose data or query uses a collection change meaning: a
  `rdf:rest*/rdf:first` property path over such data finds nothing. Re-record the result when the
  query still means something (a collection compared whole), flag it and add the position-pattern
  counterpart otherwise. The `json-res` and `csv-tsv-res` directories get `seq` cases. Ordering
  tests (`sort`) get sequence cases.
- **SPARQL 1.2.** As 1.1; add a sequence inside a triple term in patterns and results.
- **JSON-LD toRdf.** Every `@list` test's expected N-Quads is re-recorded as a sequence; the
  list-of-lists tests become ordinary; the tests of holes (a list value that converts to nothing)
  lose the hole. **fromRdf**: the input N-Quads with ladders become sequences and the expected
  JSON-LD keeps `@list`. **expand, compact, flatten, frame**: unchanged (they do not touch RDF).
- **ShEx.** Schemas never use lists, so `schemas/` is unchanged; `validation/` data files written
  with `( … )` now carry sequences, so every test whose shape constrained the ladder (none in the
  suite, the suite avoids lists) is reviewed and the Collection shape expression tests are added
  from shex.js-array's webapp manifest: the RGB colour, the too-short failure, the nested polygon,
  the playlist, `((.))` with `()` and with a non-sequence.
- **SHACL.** Every shapes graph uses lists (`sh:path ( … )`, `sh:in`, `sh:or`); nothing can be
  re-recorded before SHACL-array says how a shapes graph's lists and sequence-valued data read.
  Leave the suite until then.
- **RDF canonicalization.** Add sequence cases (nested, with blank nodes inside) once an algorithm
  exists; the existing tests pass unchanged.

## 3. Forking a suite

One fork per suite, named like the implementation forks and laid out so that existing runners
need only a different base URL:

```bash
gh repo fork w3c/rdf-tests --org rdf-array --fork-name rdf-tests-array --default-branch-only --clone=false
gh repo fork w3c/json-ld-api --org rdf-array --fork-name json-ld-api-array --default-branch-only --clone=false
gh repo fork shexSpec/shexTest --org rdf-array --fork-name shexTest-array --default-branch-only --clone=false
```

On the `rdf-sequences` branch of each: re-record expected files in place (the diff is the
documentation); give every changed test `rdfs:comment "rdf-array: …"` saying what changed and
why, and keep its name; put added tests in a sibling manifest per directory,
`manifest-array.ttl` (or `-array.jsonld`), included from the directory's manifest with
`mf:include`, with `mf:name`s prefixed `rdf-array:` and `rdft:approval rdft:Proposed`; never
delete a test, mark one that cannot hold under rdf-array `rdft:Rejected` with the comment. Serve
the fork with the same Pages workflow as the documents (static, `upload-pages-artifact` of the
tree) so that every implementation reads the suite from one stable base,
`https://rdf-array.github.io/rdf-tests-array/…`, rather than from a local path each.

Jena and RDFLib vendor copies of the suites in-tree (`jena-arq/testing/`, RDFLib's
`test/data/suites/`): re-record those copies from the fork, do not maintain them separately.

## 4. The rdf-array additions

The cases that are new under rdf-array (position patterns, sequence ordering, the results
spellings, the Collection shape expression, JSON-LD-array) belong in one place in the formats the
runners already read: a repository `rdf-array/rdf-array-tests` with `turtle/`, `sparql/`,
`results/`, `shex/`, `json-ld-array/` directories, each a W3C-style manifest (`mf:Manifest`,
`rdft:TestTurtleEval`, `mf:QueryEvaluationTest`, `sht:ValidationTest`), and for JSON-LD-array a
test type of its own, `jla:ToRdfTest`, with `mf:action` the data, `jla:mapping` the mapping and
`mf:result` the N-Quads-array. Seed it from what the forks already test: jena-array's
`RDF-SEQUENCES-HANDOFF.md` tables and SPARQL counterparts, comunica-array's system tests,
shex.js-array's webapp manifest, jsonld.js-array's `tests/array.js`, and §4 of the `array-tests`
skill. Until it exists each fork re-derives the cases; it is the highest-utility item in
[targets.md](../../../targets.md).

## 5. Running a suite against each implementation

| Implementation | Runner | Where the suite URL or path is set |
|---|---|---|
| N3.js-array | `npm run spec` (`spec/run.js`); `npm run spec-1-1-earl` runs `rdf-test-suite` per syntax and writes EARL | the manifest URLs in the `spec-1-1-earl-*` scripts and in `spec/run.js` |
| rdfxml-streaming-parser-array, jsonld-streaming-parser-array, jsonld-streaming-serializer-array, sparqljson-parse-array, sparqlxml-parse-array | `npm run spec` (`rdf-test-suite` with `spec/parser.js`, `-c .rdf-test-suite-cache/`) | the manifest URL in the `spec` script; `-i '{ "streamingProfile": true }'` for the streaming profile |
| jsonld.js-array | `npm run fetch-test-suites` clones the JSON-LD API, framing, json-ld.org and rdf-canon suites into `test-suites/`, then `npm test` (`JSONLD_TESTS=<dir>` for one suite) | the `git clone` URLs in the `fetch-*` scripts |
| traqula-array | `yarn spec:all` (lerna over the parser packages, `rdf-test-suite`) | each package's `spec` script |
| comunica-array | in `engines/query-sparql`: `yarn spec:query-1-1`, `spec:update-1-1`, `spec:csv-tsv-1-1`, `spec:query-1-2` (`rdf-test-suite` with `spec/sparql-engine.js`, each with a `--skip` list of known failures), plus `rdf-test-suite-ldf` | the `spec:base-*` scripts' manifest URLs; add rdf-array skips to the `--skip` lists with a comment |
| jena-array | ARQ: `arq.qtest --earl <manifest>` or the `TS_*` JUnit suites over `jena-arq/testing/`; RIOT: the `testing/RIOT/` manifests | the in-tree copies |
| rdflib-array | `pytest test/test_w3c_spec/` over `test/data/suites/` | the in-tree copies |
| PyShEx-array | the shexTest manifest tests under `tests/`, fetched from GitHub | the branch and URL in the test utilities |
| shex.js-array | the mocha manifest tests over the `shex-test` dependency, `"shex-test": "github:shexSpec/shexTest#main"` in the root `package.json` (the Pages workflow clones the same ref beside the checkout) | that dependency, pointed at `rdf-array/shexTest-array#rdf-sequences`, and the workflow's clone |
| rudof | the `shex_testsuite` crate over a shexTest checkout | its path argument |
| Oxigraph (future) | `testsuite/` crate with its vendored suites | the vendored copies |
| QLever (future) | its own end-to-end tests | — |

A run is recorded as an EARL report where the runner produces one (`rdf-test-suite -o earl
-p spec/earl-meta.json`), kept under `reports/` in the implementation fork, with the counts and the
flagged tests in its `doc/rdf-array.md`.

## 6. Checklist for one implementation and one suite

1. Point the runner at the suite fork (URL or path), not at W3C's copy.
2. Run; sort the failures into: expectation still spells a ladder (fix the suite fork), meaning
   changed (flag in the suite fork, add the counterpart), implementation bug (fix the fork).
3. Add the rdf-array additions (§4) for the layers the implementation has.
4. Record counts, skips and the EARL report; note any test the implementation cannot run and why.
