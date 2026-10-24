# rdf-array

**rdf-array** is RDF with one more kind of term, the **sequence**: `(1 2 3)` in Turtle is one term
holding three literals in order, `()` is the empty sequence, and a sequence may hold terms of any
kind, sequences included. Nothing else about RDF changes. The organisation holds forks of RDF
implementations that teach them the term, one stack per language, and this repository is its
meta-repository: the documents below and the list of the forks.

## Documents

| Document | Rendered | What it is |
|---|---|---|
| [rdf-array.md](rdf-array.md) | [rdf-array.html](https://rdf-array.github.io/rdf-array/rdf-array.html) | the change from RDF to rdf-array: the data model, the syntaxes, the implementations, the conventions, the open questions |
| [json-ld-array.md](json-ld-array.md) | [json-ld-array.html](https://rdf-array.github.io/rdf-array/json-ld-array.html) | the JSON-LD-array specification: conventional JSON to rdf-array through a mapping document |
| [json-ld-array-brief.md](json-ld-array-brief.md) | — | the summary of JSON-LD-array written for implementers |
| [targets.md](targets.md) | — | further `-array` targets (Oxigraph, rudof, QLever, SHACL-array, …) assessed for impact and utility, with a recommended order |

The rendered documents are listed at <https://rdf-array.github.io/rdf-array/html-index.html>, the
repository's homepage. `python3 md-to-respec.py <doc>.md <doc>.html` regenerates a rendering
(ReSpec, unofficial draft); the Pages workflow refuses a push whose HTML is older than its Markdown.

## Repositories

Every fork is named `<project>-array`, elided below, and works on its `rdf-sequences` branch, which
is its default branch. The first entry of each group is the project the stack was forked for; nested
under it are the dependencies that had to learn the term, pinned from the dependent fork. A
dependency shared by several stacks is listed once, under the first, with the others named.

- **Java**
  - [jena](https://github.com/rdf-array/jena-array) ([apache/jena](https://github.com/apache/jena)) —
    Apache Jena with the `Node_Seq` term: Turtle-array, SPARQL-array with position patterns and
    functions, ShEx-array, and the `jena-rdfminus` demo server. No forked dependencies.
- **JavaScript**
  - [shex.js](https://github.com/rdf-array/shex.js-array) ([shexjs/shex.js](https://github.com/shexjs/shex.js)) —
    ShEx validation and semantic actions in TypeScript, with the ShEx-array Collection shape
    expression `((shapeExpr))[min, max]`; site at <https://rdf-array.github.io/shex.js-array/>.
    - [N3.js](https://github.com/rdf-array/N3.js-array) ([rdfjs/N3.js](https://github.com/rdfjs/N3.js)) —
      Turtle, TriG, N-Triples, N-Quads and N3 with sequences as terms (also comunica and jsonld.js).
    - [types](https://github.com/rdf-array/types-array) ([rdfjs/types](https://github.com/rdfjs/types)) —
      `@rdfjs/types` with the `Sequence` term in `Term`, `Quad_Subject` and `Quad_Object` (also comunica).
    - [lezer-turtle](https://github.com/rdf-array/lezer-turtle-array) ([ericprud/lezer-turtle](https://github.com/ericprud/lezer-turtle)) —
      the Turtle editor grammar, emitting collections as sequence terms.
    - [lezer-shexc](https://github.com/rdf-array/lezer-shexc-array) ([shexjs/lezer-shexc](https://github.com/shexjs/lezer-shexc)) —
      the ShExC editor grammar with the Collection shape expression.
    - [n3writer-wrapper](https://github.com/rdf-array/n3writer-wrapper-array) ([ericprud/n3writer-wrapper](https://github.com/ericprud/n3writer-wrapper)) —
      readable N3.js Turtle output: nested `[ ]`, uniform indentation, long strings.
  - [comunica](https://github.com/rdf-array/comunica-array) ([comunica/comunica](https://github.com/comunica/comunica)) —
    the SPARQL-array engine: sequence patterns with variables, ordering, CONSTRUCT, the result
    formats, Turtle, JSON-LD and RDF/XML sources, remote endpoints.
    - [traqula](https://github.com/rdf-array/traqula-array) ([comunica/traqula](https://github.com/comunica/traqula)) —
      the SPARQL parser, generator and algebra, with a collection as one sequence term.
    - [rdf-data-factory](https://github.com/rdf-array/rdf-data-factory-array) ([rubensworks/rdf-data-factory.js](https://github.com/rubensworks/rdf-data-factory.js)) —
      `DataFactory.sequence()` and the `Sequence` term.
    - [rdf-string](https://github.com/rdf-array/rdf-string-array) ([rubensworks/rdf-string.js](https://github.com/rubensworks/rdf-string.js)) and
      [rdf-string-ttl](https://github.com/rdf-array/rdf-string-ttl-array) ([rubensworks/rdf-string-ttl.js](https://github.com/rubensworks/rdf-string-ttl.js)) —
      spelling and reading `(e1 e2 …)`.
    - [rdf-terms](https://github.com/rdf-array/rdf-terms-array) ([rubensworks/rdf-terms.js](https://github.com/rubensworks/rdf-terms.js)) —
      the nested-term helpers, descending into sequences as into quoted triples.
    - [jsonld-streaming-parser](https://github.com/rdf-array/jsonld-streaming-parser-array) ([rubensworks/streaming-jsonld-parser.js](https://github.com/rubensworks/streaming-jsonld-parser.js)) —
      a JSON-LD `@list` as one sequence.
    - [jsonld-streaming-serializer](https://github.com/rdf-array/jsonld-streaming-serializer-array) ([rubensworks/jsonld-streaming-serializer.js](https://github.com/rubensworks/jsonld-streaming-serializer.js)) —
      a sequence as `@list`.
    - [rdfxml-streaming-parser](https://github.com/rdf-array/rdfxml-streaming-parser-array) ([rdfjs/rdfxml-streaming-parser.js](https://github.com/rdfjs/rdfxml-streaming-parser.js)) —
      `rdf:parseType="Collection"` as one sequence; `rdf:li` no longer numbered.
    - [sparqljson-parse](https://github.com/rdf-array/sparqljson-parse-array) ([rubensworks/sparqljson-parse.js](https://github.com/rubensworks/sparqljson-parse.js)) and
      [sparqlxml-parse](https://github.com/rdf-array/sparqlxml-parse-array) ([rubensworks/sparqlxml-parse.js](https://github.com/rubensworks/sparqlxml-parse.js)) —
      `{"type": "seq"}` and `<seq>` bindings in the results of remote endpoints.
  - [jsonld.js](https://github.com/rdf-array/jsonld.js-array) ([digitalbazaar/jsonld.js](https://github.com/digitalbazaar/jsonld.js)) —
    JSON-LD-array: `jsonld.arrayToRDF`, writers for N-Quads-array and Turtle-array, and the
    [playground](https://rdf-array.github.io/jsonld.js-array/). No forked dependencies.
- **Python**
  - [PyShEx](https://github.com/rdf-array/PyShEx-array) ([linkml/PyShEx](https://github.com/linkml/PyShEx)) —
    ShEx validation over RDFLib, with the Collection shape expression.
    - [rdflib](https://github.com/rdf-array/rdflib-array) ([RDFLib/rdflib](https://github.com/RDFLib/rdflib)) —
      `rdflib.term.Sequence`; Turtle, N-Triples, N3, JSON-LD and SPARQL read and write it, RDF/XML,
      TriX and HexTuples refuse it.
    - [grammar-python-antlr-linkml](https://github.com/rdf-array/grammar-python-antlr-linkml-array) ([ericprud/grammar-python-antlr-linkml](https://github.com/ericprud/grammar-python-antlr-linkml), from [linkml/grammar-python-antlr-linkml](https://github.com/linkml/grammar-python-antlr-linkml)) —
      the `pyshexc` ShExC parser with the Collection shape expression.
    - [ShExJSG](https://github.com/rdf-array/ShExJSG-array) ([linkml/ShExJSG](https://github.com/linkml/ShExJSG)) —
      the ShExJ schema objects with the Collection shape expression.
    - [CFGraph](https://github.com/rdf-array/CFGraph-array) ([linkml/CFGraph](https://github.com/linkml/CFGraph)) —
      the closed-first graph wrapper, flattening sequence terms as well as `rdf:first`/`rdf:rest` ladders.

## Skills and tools

The formula the forks follow is written down as skills, in `.claude/skills/`, for the sessions
that make the next ones:

- [fork-array](.claude/skills/fork-array/SKILL.md): forking a project into the organisation and
  teaching it the term, layer by layer, with the naming, remotes, banner, notes, pinning and Pages
  conventions.
- [array-tests](.claude/skills/array-tests/SKILL.md): transforming a project's tests, flagging the
  ladder-dependent ones, folding ladder expectations into sequences with
  [tools/rewrite-ladders.py](tools/rewrite-ladders.py), and the cases every fork must pass.
- [w3c-test-suites](.claude/skills/w3c-test-suites/SKILL.md): which W3C and community suites apply,
  what rdf-array changes in each, how to fork them as `<suite>-array`, and how each implementation
  runs them.
- [readme-manifest](.claude/skills/readme-manifest/SKILL.md): keeping the repository list above in
  step with GitHub, checked by [tools/manifest-check.py](tools/manifest-check.py).

## Conventions

A fork's README opens with a banner, "`<project>-array`: `<project>` for rdf-array", beside an icon
that puts the original's avatar between big `[` `]` brackets; its notes live in `doc/rdf-array.md`;
its commit messages start with `rdf-array:` (older ones with `RDF-:`); a test that depends on
`rdf:first`/`rdf:rest` ladders is flagged with the reason, never silently dropped. The rest is in
[rdf-array.md](rdf-array.md).
