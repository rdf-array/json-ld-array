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
| SPARQL-array, ShEx-array, JSON-LD-array additions | the `*-contrib` repositories (§4) | the W3C formats | every implementation |

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

## 3. The forks (done) and how they were rewritten

| Fork | Of | What changed |
|---|---|---|
| [rdf-tests-array](https://github.com/rdf-array/rdf-tests-array) | w3c/rdf-tests | 40 Turtle, TriG and RDF/XML evaluation results; syntax, semantics and SPARQL unchanged (doc/rdf-array.md says why, test by test) |
| [json-ld-api-array](https://github.com/rdf-array/json-ld-api-array) | w3c/json-ld-api | 27 toRdf and 4 html results, 16 fromRdf inputs |
| [json-ld-streaming-array](https://github.com/rdf-array/json-ld-streaming-array) | w3c/json-ld-streaming | 23 stream-toRdf results |
| [shexTest-array](https://github.com/rdf-array/shexTest-array) | shexSpec/shexTest | the 1list schemas as Collections, 1val1 ShExR fixtures, manualList tests switched off, ShExR.shex, ShExJ.jsg, vocabulary and context |

The rules: never delete a test; change expectations, not inputs; derive each rewrite twice and write it
only when the two agree; leave explicit uses of `rdf:first`/`rdf:rest`/`rdf:nil` as ordinary triples;
annotate each changed test (`rdfs:comment "rdf-array: …"` in Turtle manifests, `"rdfArrayNote"` in
JSON-LD ones; ShEx tests that no longer test anything are commented out of the manifest, as shexTest does).
The tools, in this repository's `tools/`:

- `rdfarray.py`: N-Triples-array/N-Quads-array read and write, `fold` (ladders → sequences; `--json-ld`
  applies JSON-LD 1.1's list well-formedness, `--holes` lets a cell without `rdf:first` contribute
  nothing), `iso` (isomorphism with blank nodes inside sequences).
- `rewrite-rdf-syntax.py`: folds the RDF syntax suites' expectations and cross-checks them against
  jena-array (`JenaArray.java`, built into `.tools/` with `cp.txt` holding jena-array's classpath) and
  rdfxml-streaming-parser-array (`parse-rdfxml-array.js`); `--write` applies.
- `rewrite-json-ld.py`: the same for JSON-LD suites, cross-checked by jsonld-streaming-parser-array
  (`parse-jsonld-array.js`).
- `annotate-manifest.py`, `annotate-json-manifest.py`: add the rdf-array notes.
- `JenaArray.java`: `parse`, `query`, `update`, `inspect` (does a file hold a sequence?) and `shex`
  against jena-array's build tree.

For a suite not yet forked (SHACL once SHACL-array is defined, RDF canonicalization once sequences are
canonicalized): fork with `gh repo fork <owner>/<repo> --org rdf-array --fork-name <repo>-array`, branch
`rdf-sequences`, rewrite with the tools above or their like, write `doc/rdf-array.md` with the table of
changed tests and the "unchanged on purpose" list, add the README banner and icon, and publish with the
`rdf-array-pages.yml` workflow the other forks carry (static tree to GitHub Pages).

## 4. The contrib suites (tests no W3C suite has)

Tests that are new under rdf-array do **not** go into the forks: each fork has a sibling `*-contrib`
repository, laid out like it and in the same manifest vocabulary, so that the runner of one walks the
other; shexTest's own `schemas-contrib`/`validation-contrib` directories are the model.

| Contrib | Beside | Contents |
|---|---|---|
| [rdf-tests-contrib](https://github.com/rdf-array/rdf-tests-contrib) | rdf-tests-array | Turtle/TriG/N-Triples/N-Quads-array syntax and evaluation; SPARQL-array evaluation, update, syntax, results formats |
| [json-ld-api-contrib](https://github.com/rdf-array/json-ld-api-contrib) | json-ld-api-array | toRdf and fromRdf with sequences; JSON-LD-array (`ra:JsonLdArrayToRdfTest`) |
| [shexTest-contrib](https://github.com/rdf-array/shexTest-contrib) | shexTest-array | Collection schemas (ShExC/ShExJ/ShExR), validation, negative syntax |

Each holds its cases in `bin/build.py`, which writes every file and manifest and cross-checks every
expectation against at least two implementations where two exist (jena-array and N3.js-array for syntax,
jena-array and comunica-array for SPARQL, jsonld-streaming-parser-array and rdflib-array for JSON-LD,
shex.js-array and jena-array for ShEx); `--check` fails if a rebuild would change anything. To add a test,
add a row to the table there and rebuild; give it its `duplicates` (the implementation tests it reproduces)
and run `tools/contrib-duplicates.py` here, which regenerates [contrib-duplicates.md](../../../contrib-duplicates.md).
Every test that uses the proposed array syntax says so with `mf:requires` (`ra:PositionPatterns`,
`ra:SequenceFunctions`, `ra:CollectionShapeExpression`, from [vocab/vocab.ttl](../../../vocab/vocab.ttl)), and
`tools/array-syntax-uses.py` regenerates [array-syntax-uses.md](../../../array-syntax-uses.md), the list a
change of syntax has to rewrite.

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
| rudof-array | `cargo test -p shex_testsuite` (baselines in `tests/`, `tests/rdf_array_contrib.rs`) and `cargo run -p shex_testsuite -- -m <manifest> -s shexc\|shexj\|shexr` | the `shex_testsuite/shexTest` and `shex_testsuite/shexTest-contrib` submodules, pointed at shexTest-array (`rdf-sequences`) and shexTest-contrib (`main`) |
| oxigraph-array | `cargo test -p oxigraph-testsuite` (`tests/parser.rs`, `tests/sparql.rs`, one function per manifest, each with a skip list) | the `testsuite/` submodules, pointed at the -array forks (branch `rdf-sequences`) and the contrib repositories (`main`); `src/files.rs` maps `https://w3c.github.io/` and `https://rdf-array.github.io/` onto them |
| QLever (future) | its own end-to-end tests | — |

A run is recorded as an EARL report where the runner produces one (`rdf-test-suite -o earl
-p spec/earl-meta.json`), kept under `reports/` in the implementation fork, with the counts and the
flagged tests in its `doc/rdf-array.md`.

## 6. Checklist for one implementation and one suite

1. Point the runner at the suite fork (URL or path), not at W3C's copy, and at its `*-contrib` sibling.
2. Run; sort the failures into: expectation still spells a ladder (fix the suite fork), meaning
   changed (flag in the suite fork, add the counterpart), implementation bug (fix the fork).
3. Add the rdf-array additions (§4) for the layers the implementation has.
4. Record counts, skips and the EARL report; note any test the implementation cannot run and why.
