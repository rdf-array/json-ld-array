# json-ld-array: the JSON-LD-array specification

**JSON-LD-array** is a mapping language that turns conventional JSON — the JSON an API already
produces, with no `@` keywords in it — into **rdf-array**, RDF whose data model has sequences as
terms: a JSON array is one sequence term `( e1 e2 … )`, nested arrays are nested sequences and `[]`
is the empty sequence, instead of an `rdf:first`/`rdf:rest` ladder. The mapping is a document of its
own, shaped like a JSON-LD context but with prefixes, property maps (inline or named, like the rules
of a grammar), type maps, lexically scoped bases and templates each in their own place.

- [json-ld-array.md](json-ld-array.md): the specification, a design sketch, rendered with ReSpec at
  <https://rdf-array.github.io/json-ld-array/> ([json-ld-array.html](json-ld-array.html)).
- [json-ld-array-brief.md](json-ld-array-brief.md): the summary for implementers.
- [md-to-respec.py](md-to-respec.py) regenerates the HTML:
  `python3 md-to-respec.py json-ld-array.md json-ld-array.html`.
- The implementation is [jsonld.js-array](https://github.com/rdf-array/jsonld.js-array),
  `jsonld.arrayToRDF`, with a playground at <https://rdf-array.github.io/jsonld.js-array/>.

Part of the [rdf-array](https://github.com/rdf-array) project, whose other syntaxes are Turtle-array,
SPARQL-array and ShEx-array.
