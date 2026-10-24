---
name: array-tests
description: Transform an upstream project's tests for its -array fork — find the tests that depend on rdf:first/rdf:rest ladders or rdf:_n containers, flag them with the rdf-array reason, write rdf-array counterparts, rewrite ladder expectations into sequence terms with tools/rewrite-ladders.py, and add the cases every fork must pass. Use while adapting or extending a fork's test suite.
---

# Transforming a project's tests for rdf-array

The rule the forks follow: a test that depends on ladders or containers is never silently dropped.
It is flagged with the reason, it gets an rdf-array counterpart where one makes sense, and the
fork's `doc/rdf-array.md` lists both. The W3C suites are handled by the `w3c-test-suites` skill;
this one is about the project's own tests.

## 1. Inventory

Find every test that mentions the vocabulary or the syntax:

```bash
grep -rln --include='*.ts' --include='*.js' --include='*.py' --include='*.java' --include='*.rs' \
  -E 'rdf-syntax-ns#(first|rest|nil|_[0-9]|li|Seq|Bag|Alt)|rdf:(first|rest|nil|_[0-9]|li)|RDF\.(first|rest|nil)|@list|parseType="Collection"|Collection\(' tests test src
grep -rln --include='*.ttl' --include='*.nt' --include='*.nq' --include='*.trig' --include='*.jsonld' --include='*.rq' \
  -E 'rdf:(first|rest|nil)|#(first|rest|nil)>|\( ?[^)]' tests test testing fixtures
```

Classify each hit:

| Kind | What to do |
|---|---|
| a parser or serializer test whose *expected output* spells a ladder | re-record the expectation as the sequence term (§3) |
| a query or path test that *walks* a ladder (`rdf:rest*/rdf:first`, `rdf:_1`) | flag it (§2) and write a counterpart that reads the sequence directly (`?s :p ((?e))[*]`, `?s :p ( ?a ?b )`) |
| a test of the removed code (list builders, `rdf:li` numbering, `CommonIRIs.NIL`) | delete it, with a line in the notes |
| a test of a container (`rdf:Seq` with `rdf:_1`) | flag it; the data now carries `rdf:li` properties or plain `rdf:_n` IRIs |
| a fixture whose Turtle uses `( … )` for a list the test then dereferences | re-record the fixture's reading: the collection is one term |
| a JSON-LD test with `@list` | parser: the expected quads hold a sequence; serializer: the sequence is written as `@list` |

## 2. Flagging

Skip with the reason in the test file, in the framework's idiom, and keep the test's body so the
diff shows what changed:

```ts
// RDF-array: skipped, the rdf:rest*/rdf:first path walks a ladder that `fhir:coding ( [ … ] )` no longer is
// eslint-disable-next-line jest/no-disabled-tests
it.skip('should handle zero-or-more paths with lists', …);
```

```python
@pytest.mark.skip(reason="rdf-array: the fixture's collection is one sequence term, not a ladder")
```

```java
@Disabled("rdf-array: rdf:li is no longer numbered into rdf:_n")
```

Write the counterpart beside it, named for what it tests under rdf-array ("should bind a sequence
after a link", "should handle a sequence holding a blank node property list"), over the same data.
List both in `doc/rdf-array.md` under Tests, with the reason; jena-array keeps a table of them in
`RDF-SEQUENCES-HANDOFF.md`.

## 3. Rewriting ladder expectations

Expectations written as quad lists can be folded mechanically: collect the `rdf:first` and
`rdf:rest` triples, find the heads (nodes never the object of a `rdf:rest`), follow each chain to
`rdf:nil`, replace every reference to a head by `sequence([ …elements… ])` and every bare `rdf:nil`
object by `sequence([])`, and drop the ladder triples. Nested lists resolve recursively; a node with
`rdf:rest` but no `rdf:first` (a JSON-LD "hole") contributes no element. `tools/rewrite-ladders.py`
in this repository does this for jest-rdf style expectation arrays (`DF.quad(…)` entries inside
`toBeRdfIsomorphic([ … ])` or `toEqualRdfQuadArray([ … ])`); it skips any block it cannot fold and
reports why, so run it, read the report, then run the tests:

```bash
python3 ~/checkouts/rdf-array/rdf-array/tools/rewrite-ladders.py test/Parser-test.ts
```

Adapt its three regexes (the quad constructor, the `first`/`rest`/`nil` spellings, the matcher
names) for another framework; the chain logic is the same. In the JSON-LD parser fork it rewrote
56 blocks and left 4 to fix by hand.

Re-recording fixtures (expected `.nt`, `.ttl`, `.jsonld` files) is the same fold applied to data:
regenerate with the fork's own serializer once the parser is trusted, and read the diff.

## 4. Cases every fork must pass

Add these, in the fork's own test style, wherever the layer exists; they are what the conformance
suite will contain:

- parse `( 1 2 )`, `()`, `( 1 ( 2 3 ) )`, `( [ :p 1 ] )`, a sequence as subject, as an element of a
  sequence inside a triple term, and the empty sequence against `rdf:nil` (they differ);
- serialize each back and round-trip;
- equality of sequences by elements across implementations' term classes; inequality with the
  ladder it replaces;
- ordering: sequences after literals and triple terms, element-wise, shorter prefix first;
- for a store or engine: match `?s :p ( ?x 2 )`, `?s :p ( ?x ( ?y ?z ) )`, a repeated variable, a
  constant sequence, `()`, and a quoted triple holding a sequence; over every source kind the engine
  has (in-memory, serialized, remote);
- for a query engine: `((?e))[2]`, `[?i]`, `[*]`, nested; `isSEQ`, `SEQLEN`, `expr[i]` if provided;
  CONSTRUCT and INSERT building sequences; `ORDER BY` over sequences;
- results: `{"type": "seq"}`, `<seq>`, the CSV and TSV cells, and reading them back;
- JSON-LD: `@list` → sequence (nested, empty, single non-array value), sequence → `@list`;
- RDF/XML: `rdf:parseType="Collection"` with two nodes, empty, self-closing, reified; `rdf:li`
  staying `rdf:li`;
- ShEx: the Collection shape expression on an RGB colour `((xsd:integer MININCLUSIVE 0 MAXINCLUSIVE 255))[3]`,
  a too-short sequence failing, a nested polygon, a playlist of `@<Track>`, `((.))` with `()`.

## 5. Assertion pitfalls

- `rdf-isomorphic` (jest-rdf's `toBeRdfIsomorphic`) does not canonicalize blank nodes inside
  sequences: compare those cases by hand (find the quad, check `elements` by term type).
- Vanilla `rdf-string` returns `undefined` for a sequence, so isomorphism of sequence-bearing graphs
  passes vacuously until the test dependencies pin `rdf-string-array` (`resolutions`/`overrides`).
- Numbers: a JSON parser that loses the lexical form turns `1.70` into `1.7`; JSON-LD's canonical
  double is `1.0E0`; decide the datatype rule once (rdf-array: `xsd:decimal` for fractions) and test
  the spelling.
- `ExpressionEngine`-style tests compare `NOW()` with a UTC string: run with `TZ=UTC`.
- Coverage thresholds of 100% (comunica, traqula, N3.js, the rubensworks libraries) fail the hook on
  any uncovered branch: cover the error branches (`The data factory has no sequence()`).
- Blank node numbering (`_:b0`, `_:b1`, …) is deterministic in a fork's own writer; tests may rely
  on it, so a change of creation order is a visible change.

## 6. Verification and record

Run the fork's whole suite, the dependency forks' suites, and the applicable W3C suites
(`w3c-test-suites`); put the numbers, the skipped tests with reasons, and the suites not run in
`doc/rdf-array.md`. A fork is done when the only failures left are the flagged ones.
