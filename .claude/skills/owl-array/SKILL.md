---
name: owl-array
description: Port the OWL API (and then Protégé) to OWL-array, OWL 2 over rdf-array — the OWLSequence individual term equal by its elements, OWL's own lists read and written as sequences, the node-ID stopgap for the syntaxes without a spelling, the built-in ra: vocabulary, the reasoner expansion as a decorator around HermiT or JFact, and the tests. Use when working in owlapi-array, on a Protégé fork, or on another OWL implementation's rdf-array reading.
---

# Porting an OWL implementation to OWL-array

[owl-array.md](../../../owl-array.md) is the definition and is normative here: §2 (OWL's lists are
sequences), §3 (a data sequence is an individual with the built-in `ra:` properties), §4 (how each
syntax writes a sequence), §5 (what is deliberately left out), §6 (the expansion that gives a stock
reasoner the semantics), §7 (tests). Do not change its semantics from inside a fork; a question it
does not answer is a `spec` issue in rdf-array/rdf-array (`fork-array` §8). The vocabulary ontology is
[vocab/owl-array.ttl](../../../vocab/owl-array.ttl). The general fork formula (naming, remotes,
banner, notes, commits, Pages, issues) is the `fork-array` skill, and the tests follow `array-tests`;
this skill is what is specific to OWL.

Decisions already taken, with their reasons in owl-array.md §9, so do not reopen them: a sequence is
an individual, not a data value and not syntax only; it has no IRI and no label, and is equal by its
elements; there is no `ra:rest` and no suffix property; nothing is materialised into the ontology or
a companion ontology, the expansion lives inside a reasoner decorator; the constraint vocabulary is
nested restrictions on the built-in properties, not a new restriction kind.

## 1. owlapi-array: OWL API 4.5.29

The fork is `~/checkouts/rdf-array/owlapi-array`, branch `rdf-sequences` from the `OWLAPI 4.5.29`
commit, `origin` the fork and `upstream` owlcs/owlapi. OWL API 4 is the line Protégé 5.6 loads, and
it compiles to Java 8 (`maven-compiler-plugin` source/target 1.8), so interface default methods are
available and are what keeps unmodified Protégé code compiling. Build with `mvn -q -DskipTests
install` at the root (modules in order: api, impl, tools, parsers, oboformat, fixers, rio,
compatibility, apibinding, contract; a JDK 21 is installed, and if javadoc or enforcer plugins
object add `-Dmaven.javadoc.skip=true`); run one module's tests with
`mvn -q -pl contract test -Dtest=<pattern>`.

### 1.1 The term

- `api/.../model/OWLSequence.java`: `public interface OWLSequence extends OWLAnonymousIndividual`
  with `List<OWLPropertyAssertionObject> getElements()` (the common supertype of `OWLIndividual` and
  `OWLLiteral`, so an element is a named individual, an anonymous individual, a literal or a nested
  `OWLSequence`). Making it a kind of anonymous individual is the compatibility decision: every
  visitor, renderer and Protégé class that handles anonymous individuals handles a sequence
  unchanged until it is taught better.
- `impl/.../OWLSequenceImpl.java`, modelled on `OWLAnonymousIndividualImpl`: `equals`, `hashCode` and
  `compareTo` by the element list, never by the node ID; `getID()` returns the node ID of §1.2;
  `isAnonymous()` true; the OWLObject plumbing (signature, anonymous individuals, nested class
  expressions) walks the elements.
- `OWLDataFactory.getOWLSequence(List<? extends OWLPropertyAssertionObject>)` in the API interface,
  `OWLDataFactoryImpl` and `OWLDataFactoryInternals`.
- Visitors: add `default void visit(OWLSequence s) { visit((OWLAnonymousIndividual) s); }` (and the
  `Ex` form) to `OWLIndividualVisitor`, `OWLIndividualVisitorEx`, `OWLObjectVisitor`,
  `OWLObjectVisitorEx`, `OWLAnnotationValueVisitor(Ex)` and `OWLAnnotationSubjectVisitor(Ex)`;
  `OWLSequenceImpl.accept` calls `visit(this)`, which resolves to the sequence overload. The 35
  implementors in the tree then need touching only where a sequence should render or be collected
  differently: `AbstractTranslator` (RDF), `FunctionalSyntaxObjectRenderer`,
  `ManchesterOWLSyntaxObjectRenderer`, `OWLXMLObjectRenderer`, `SimpleRenderer`, `LatexObjectVisitor`,
  `OWLObjectDuplicator`, `OWLObjectDesharer`, `HashCode`, `StructureWalker`, `OWLEntityCollector`,
  `OWLObjectComponentCollector`, `OWLAnonymousIndividualsWithMultipleOccurrences` (a sequence may
  occur many times; it is a value, not a shared blank node).
- Vocabulary constants: an enum beside `OWLRDFVocabulary`, `RDFArrayVocabulary`, with the `ra:` IRIs
  of owl-array.md §3.2 and the namespace `https://rdf-array.github.io/rdf-array/vocab#`.

### 1.2 The node ID stopgap

Until the Functional-style, OWL/XML and Manchester grammars have the spellings of owl-array.md §4,
a sequence travels through them as an anonymous individual whose node ID is reversible: a legal
blank node label (`_:seq_` followed by base64url of the sequence's N-Triples-array spelling, UTF-8,
is the suggestion), the same for equal sequences, decoded back to the `OWLSequence` by every parser
that reads node IDs: `OWLFunctionalSyntaxParser.jj`'s `AnonymousIndividual()` production,
`ManchesterOWLSyntaxParserImpl` where it tests `startsWith("_:")`, `OWLXMLParserHandler`'s
`AnonymousIndividual` element. A sequence whose elements include an ordinary anonymous individual
carries that individual's own node ID inside the encoding, and its decoding yields the same
anonymous individual the rest of the document uses. Put the encoder and decoder in one utility
(`SequenceNodeID`) with its own tests; the decoder is a small N-Triples-array term reader (IRIs,
literals, `_:` labels, nested `( … )`). Record in `doc/rdf-array.md` that the proper spellings are
the second step.

### 1.3 Parsers: a collection is one node

Both parts of owl-array.md meet here: OWL's own lists and data sequences arrive through the same
code.

- **Turtle.** `parsers/.../rdf/turtle/parser/TurtleParser.jj`: `parseCollection` / `parseItemList`
  emit `rdf:first`/`rdf:rest`/`rdf:nil` triples today. Instead collect the element nodes (IRIs,
  blank node IRIs, literals, nested sequences) and hand the `TripleHandler` one sequence node for
  the collection. The handler interface is IRI-based, so a sequence node is represented to the
  consumer by its node-ID IRI (as blank nodes are, via `NodeID`), and the consumer keeps the
  `IRI → OWLSequence` table. `()` is a sequence, not `rdf:nil`.
- **RDF/XML.** `parsers/.../rdf/rdfxml/parser/StartRDF.java`: the `ParseTypeCollectionElement`
  state, entered where a property element's `rdf:parseType` equals
  `RDFConstants.PARSE_TYPE_COLLECTION`, builds a ladder; make it collect the node elements and emit
  one sequence node. `rdf:li` is no longer numbered into
  `rdf:_n` (it stays the property `rdf:li`).
- **OWLRDFConsumer** (`parsers/.../rdf/rdfxml/parser/`): `addFirst`, `addRest`, `getFirstResource`,
  `getFirstLiteral`, `getRest` and the ladder walks in `OptimisedListTranslator.translateList`,
  `Translators` (the list item translators, around the `RDF_FIRST`/`RDF_REST` reads) and
  `TripleHandlers` (the `rdf:first`/`rdf:rest` predicate handlers) are replaced by one
  `getSequence(IRI)` that returns the elements. The OWL constructs of owl-array.md §2 then take their
  arguments from the sequence; a ladder spelled in triples is left as unconsumed triples, which is
  what makes the document not OWL 2 DL, exactly as a list in the data did before.
- **Data sequences.** Wherever the consumer turns a node IRI into an `OWLIndividual`
  (`getOWLIndividual` and the translators of class assertions, property assertions and
  annotations), a sequence IRI yields its `OWLSequence`; blank-node elements are anonymous
  individuals whose own triples parse as usual, literals are `OWLLiteral`s, nested sequences
  nested `OWLSequence`s. A sequence as the subject of a triple is an individual subject.
- **Rio** (`rio` module, Sesame/RDF4J for N-Triples, TriG, JSON-LD and the rest) is not touched in
  the first cut: those parsers build ladders, which the consumer now leaves unconsumed. Say so under
  "Not done" in the notes.

### 1.4 Renderers

- `parsers/.../rdf/model/AbstractTranslator.translateList` builds ladders for every OWL list and
  `AbstractTranslator`'s `visit(OWLAnonymousIndividual)` path handles individuals; both produce one
  sequence node in the `RDFNode` graph. Add `RDFResourceSequence extends RDFResource` (beside
  `RDFResourceBlankNode` in `api/.../io/`) holding `List<RDFNode>`.
- `RDFRendererBase` (the `rdf:first`/`rdf:rest` lookahead that pretty-prints lists) and
  `TurtleRenderer` write `( … )`, nested, `()` when empty, for OWL's lists and for data sequences
  alike. `RDFXMLRenderer` writes `rdf:parseType="Collection"` for a sequence whose elements are all
  resources; RDF/XML has no node-level literal, so a sequence with a literal element (a `DataOneOf`,
  a data sequence) has no RDF/XML-array spelling. File that as a `cross-repo` `open-question` issue
  (rdflib-array refuses too) and, until it is decided, throw an `OWLRendererException` naming the
  axiom so the user saves as Turtle.
- Functional-style, OWL/XML and Manchester renderers write the node ID (§1.2) in the first cut and
  the spellings of owl-array.md §4 in the second.

### 1.5 The reasoner expansion

A package `org.semanticweb.owlapi.rdfarray` (in `tools`, or a module of its own if the reasoner
dependencies should not reach `tools`):

- `SequenceAxioms`: owl-array.md §6 as code. Given an ontology's imports closure, collect every
  `OWLSequence` (walking into nested sequences and into annotations), map each to its expansion
  individual (a named individual with a canonical IRI derived from the spelling when the sequence
  holds no ordinary anonymous individual, else a fresh anonymous individual), and emit the class
  assertion, `ra:length`, `ra:member`/`ra:memberValue`, `ra:first`/`ra:last` and their value forms,
  and the closure axioms (`ra:member only {…}` or `ra:member max 0`; `ra:memberValue only
  DataOneOf(…)` or `max 0`). Expansion is linear in the number of elements. Keep the `OWLSequence ↔
  expansion individual` map for mapping results back.
- `SequenceAwareReasonerFactory implements OWLReasonerFactory`, wrapping a delegate factory:
  `createReasoner(ontology)` builds an in-memory ontology holding the closure's axioms with every
  sequence replaced by its expansion individual, the expansion axioms and the vocabulary ontology's
  axioms, and hands it to the delegate. `SequenceAwareReasoner implements OWLReasoner` delegates
  every call, maps expansion individuals back to sequences in results, and rebuilds on `flush()`
  when the source ontology changed (an `OWLOntologyChangeListener`). For an EL delegate omit the
  closure axioms.
- Test reasoners: JFact 4.0.x (`net.sourceforge.owlapi:jfact`) or the HermiT build for OWL API 4
  (1.4.3.x, the one Protégé 5 bundles) as test-scoped dependencies; check the artifact exists on
  Maven Central before pinning, and ELK (`org.semanticweb.elk:elk-owlapi`) for the EL cases.

### 1.6 Tests

- Follow `array-tests`: inventory the `contract` module's RDF round-trip tests whose expectations
  spell `rdf:first`/`rdf:rest`, re-record them as sequences, and flag with the reason any test whose
  point was the ladder; list both in `doc/rdf-array.md`.
- New tests, as owl-array.md §7 lists them: parsing `( … )` nested, empty and holding a blank node
  property list, in Turtle and RDF/XML; `OWLSequence` equality by elements and inequality with the
  ladder it replaces; rendering and round trips through Turtle, RDF/XML, Functional-style, OWL/XML
  and Manchester, including the node-ID stopgap; every §2 construct read from a sequence; the §3.3
  examples with a reasoner through the decorator, as entailments (`ex:ada a foaf:Agent`, `ex:p a
  ex:BigPaper`, `ex:p dc:creator ex:ada`) and as inconsistencies (the three-point ring, the
  two-member RGB); the two §3.5 caveats as tests that `ra:member min 3` is not entailed and that
  `ra:member only C` holds of a literal-only sequence.
- Record counts, skipped tests with reasons and the suites not run in `doc/rdf-array.md`.

### 1.7 Conventions and record

As `fork-array` §2–§7: set the default branch to `rdf-sequences` after the first push and the
description `rdf-array: the OWL API for OWL-array …`; the README banner and icon (owlcs's avatar
between brackets); `doc/rdf-array.md` with the stack table (OWL API 4.5.29, no forked dependencies),
what a sequence does here, what changed file by file, the tests, the decisions and what is not done;
commits `rdf-array: …` with the session's attribution trailer; push to `origin` only. The repository
is already in repos.json as `owlapi-array` (anchor `owlapi`, a Java stack) and the target `owl-api`
is marked done; run `python3 tools/manifest-check.py` in rdf-array/rdf-array after the description
and default branch are set, and add a row to owl-array.md §8 and rdf-array.md's implementations
table when the status changes.

## 2. Protégé

Protégé 5.6 loads the OWL API as the OSGi bundle built by the `osgidistribution` module. The first
experiment is to build owlapi-array's bundle with the upstream symbolic name and version so that
Protégé's manifest resolves it, replace the bundle in a Protégé installation, open an ontology
holding a sequence (it displays by its node ID until the Manchester renderer is taught `( … )`), and
run HermiT through a `ProtegeOWLReasonerInfo` plugin that wraps HermiT's factory in
`SequenceAwareReasonerFactory`. A `protege-array` fork (`fork-array`) is warranted only if the
editor itself must change; the reasoner plugin can be a small repository of its own.

## 3. Another OWL implementation

An implementation with its own RDF parser does §1.3 and §1.4 in its own terms; one that reads OWL
through an RDF library already forked (jena-array for Java, rdflib-array for Python, oxigraph-array
for Rust) gets the sequence term from the library and does only the consumer, the renderer and the
expansion. The expansion (owl-array.md §6) is the same everywhere and is what owl-tests-contrib will
check, once a second implementation exists.
