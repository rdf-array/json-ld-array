---
name: owl-array
description: Port the OWL API (and then Protégé) to OWL-array, OWL 2 over rdf-array — the OWLSequence individual term equal by its elements, OWL's own lists read and written as sequences, the node-ID stopgap for the syntaxes without a spelling, the built-in ra: vocabulary, the reasoner expansion as a decorator around HermiT or JFact, and the tests. Use when working in owlapi-array, on a Protégé fork, or on another OWL implementation's rdf-array reading.
---

# Porting an OWL implementation to OWL-array

[owl-array.md](../../../docs/owl-array.md) is the definition and is normative here: §2 (OWL's lists are
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

### 1.8 The FHIR example, and what it found

[examples/fhir](../../../examples/fhir/README.md) is the SWAT4LS 2016 FHIR reasoning process over
today's FHIR RDF (lists everywhere, `fhir:v`/`fhir:l`, concept IRIs), run through owlapi-array and
HermiT 1.4.5.456 by `examples/fhir/FhirReasoning.java` (its `pom.xml` gives the classpath): 10
ontologies, 1171 axioms, 16 sequences, 24 DL queries with their expected answers, one inconsistency.
Make it a test, `contract/.../rdfarray/FhirReasoningTestCase`: copy the example files unchanged under
`contract/src/test/resources/rdfarray/fhir/` (say in `doc/rdf-array.md` that they are copies of
rdf-array's), read the catalog as `FhirReasoning.java` does, one test per query of its table, one for
the inconsistency. The run found four things to act on or record:

- **HermiT reads `ClassAssertion(C, _:b)` existentially**: `isEntailed(ClassAssertion(fhir:Observation,
  _:fresh))` is true because some Observation exists. With an anonymous expansion individual,
  `getSequenceInstances(fhir:Observation)` therefore returns every list that holds a blank node (all 16),
  and `isEntailed` of a class assertion on such a list answers for some individual, not this one. Every
  FHIR list holds blank nodes. The decision is rdf-array#20 (the recommendation there: name the
  anonymous individuals inside the expansion); until it is taken, `getSequenceInstances` must not ask
  `isEntailed` of an anonymous expansion individual.
- **The change listener outlives an undisposed reasoner** and `markDirty` throws when the source
  ontology has been removed from its manager (`getImportsClosure` on a removed ontology); guard it.
- **JFact 4.0.4 calls the closure inconsistent** where HermiT does not; the verdict goes away without
  the data property assertions or without the cardinality restrictions, so it is JFact's datatype
  reasoning over `fhir:v exactly 1` with literals of several datatypes. HermiT is the reference.
- **`xsd:date` stops HermiT at load** (not in the OWL 2 datatype map); FHIR dates are `xsd:date`,
  `gYear`, `gYearMonth`, `time`. The example carries no birthDate for that reason; real FHIR data will,
  so the Protégé plugin's documentation must say so, and a rewrite option is worth considering later.

## 2. Protégé

Protégé 5.6.9 (released 2026-03-07; tag `5.6.9` of protegeproject/protege; Java 11) loads the OWL API
4.5.29 as one OSGi bundle, `bundles/owlapi-osgidistribution.jar` (protege-desktop's
`dependency-sets.xml` names every bundle `artifactId.extension`), symbolic name
`org.semanticweb.owl.owlapi`, version 4.5.29. HermiT is the plugin
`plugins/org.semanticweb.hermit-1.4.3.456.jar` (protege-distribution's pom), an OSGi bundle with
`Bundle-Category: protege` that exports the package `org.semanticweb.HermiT` and whose `plugin.xml`
registers the reasoner:

```xml
<extension id="HermiT.reasoner.factory" point="org.protege.editor.owl.inference_reasonerfactory">
    <name value="HermiT 1.4.3.456"/>
    <label value="HermiT 1.4.3.456"/>
    <class value="org.semanticweb.HermiT.ProtegeReasonerFactory"/>
</extension>
```

Protégé 6.0.0-alpha-1 (2026-09-28) moves to OWL API 5.5.1 and breaks every 5.x plugin; owlapi-array is
on the 4.5 line for 5.6.9, and following Protégé 6 means a `version5` port of the fork. Three steps, in
order; the first two need no fork of Protégé.

1. **The bundle.** With the modules installed (`mvn install -pl '!distribution' -Dmaven.javadoc.skip
   -Dno-javadoc=true -Dgpg.skip -Dmaven.repo.local=…`), `mvn -pl osgidistribution package -DskipTests
   -Dmaven.javadoc.skip=true -Dgpg.skip -Dmaven.repo.local=…`. The bundle in `osgidistribution/target`
   must be newer than the modules: the one built on 2026-10-26 predated the parsers and the `rdfarray`
   package; rebuilt on 2026-10-27 it carries them and exports `org.semanticweb.owlapi.rdfarray`
   (the `attach-javadoc` execution fails after the bundle goal under JDK 21 unless `-Dno-javadoc=true`
   is passed as well; the jar is complete either way: check `unzip -l` for `rdfarray/` and the
   manifest's `Export-Package`). Download the platform-independent
   zip of the 5.6.9 release, replace `bundles/owlapi-osgidistribution.jar` with that jar, start
   Protégé, open `examples/fhir/subjects.ttl` (the catalog resolves the imports): no triple left
   unparsed, amy:Obs1's description shows `fhir:code` to a blank node, a sequence displays as
   `_:seq_…`. Also open an ontology with `owl:unionOf` and `owl:oneOf` lists, save as Turtle and as
   RDF/XML, reopen. Set the default save format to Turtle, since RDF/XML refuses a list holding a
   literal (rdf-array#18).
2. **The reasoner plugin**, a repository of its own, `rdf-array/protege-owl-array` (kind `tool` in
   repos.json): a Maven bundle built with `maven-bundle-plugin` as elk-protege's pom is
   (`Bundle-SymbolicName` the plugin id, `singleton:=true`; `Bundle-Category: protege`;
   `Export-Package: !*`; `Import-Package` computed by bnd with `org.semanticweb.HermiT;version="[1.4,2)"`
   added; nothing embedded), compiled against `edu.stanford.protege:protege-editor-owl:5.6.6` (the
   last on Central; 5.6.7–5.6.9 are not, and the reasoner API did not change), owlapi-array's
   `owlapi-apibinding` 4.5.29 and HermiT `org.semanticweb.hermit` 1.4.3.456, all `provided`: at run
   time they are the swapped bundle and the HermiT plugin. One class,
   `org.rdfarray.protege.HermiTSequenceReasonerInfo extends AbstractProtegeOWLReasonerInfo` (no
   abstract methods; the interface `ProtegeOWLReasonerInfo` wants `getReasonerFactory()`, here `new
   SequenceAwareReasonerFactory(new org.semanticweb.HermiT.ReasonerFactory())`, and
   `getRecommendedBuffering()`, `BUFFERING`), and a `plugin.xml` as above naming it "HermiT 1.4.3
   (OWL-array)". Drop the jar into `plugins/`, start Protégé, pick it in the Reasoner menu, and do the
   walk-through of examples/fhir §4; record what the DL Query tab shows, with screenshots, in that
   README. A second info class wraps ELK (`io.github.liveontologies:elk-protege` is in the
   distribution) with closure off. The repository also ships a script that assembles "Protégé 5.6.9 +
   the bundle + the plugin" from the stock zip, so a user needs no build, and its README says what the
   example's findings say: `xsd:date` literals stop HermiT, a sequence is never an answer (rdf-array#21).
3. **`protege-array`**, a fork of protegeproject/protege from tag `5.6.9` (`fork-array`), only when the
   editor itself must change: to list sequences where the UI lists individuals (rdf-array#21, which also
   needs the DL Query plugin, protegeproject/dlquery, and a result type the OWL API 4 `OWLReasoner` does
   not have), to render `( … )` where the renderer is Protégé's own rather than the OWL API's, to make
   Turtle the default format. Its pom would pin owlapi-array's bundle, which then needs a version of its
   own (`4.5.29-rdf-array` is the natural Maven spelling; owlapi-array keeps `4.5.29` today and shadows
   upstream in a local repository): decide when the fork starts and record it in both `doc/rdf-array.md`.

**Done 2026-10-27, steps 1 and 2** ([protege-owl-array](https://github.com/rdf-array/protege-owl-array),
examples/fhir §4). What the plan did not foresee:

- **ELK cannot be imported.** elk-protege exports no package, so `ElkSequenceReasonerInfo` takes ELK's
  factory from ELK's own reasoner plugin (`ProtegeOWLReasonerPluginLoader`, the extension id ending
  `elk.reasoner.factory`). ELK then skips anonymous individuals and answers nothing over FHIR data.
- **bnd pins Guava from protege-editor-owl 5.6.6's pom** (33.x) while Protégé 5.6.9 ships 18.0; a bundle
  that touches Guava types needs `com.google.common.*;version="0"` in `Import-Package`.
- **The DL Query tab parses names as Protégé displays them**: by `rdfs:label` when there is one
  (`'sct:Rheumatoid arthritis (disorder)'`), and with the default prefix of the ontology opened, so the
  root document must declare the prefix its users will type (examples/fhir's `subjects.ttl` does).
- **The DL Query tab opens a modal dialog when no reasoner is set**; anything that drives it must start
  the reasoner first.
- **Saving found an owlapi-array bug**: a blank node inside a sequence lost its triples in Turtle and
  RDF/XML (fixed in owlapi-array 1200076f9, with a test).
- **Driving Protégé**: the shell had no screen-recording or accessibility permission, so screenshots
  come from a bundle inside Protégé (`walkthrough/` in protege-owl-array) that paints the window with
  Swing; it needs no permission and can run again.
- **Creating the repository** is the user's: the session cannot create a public repository.

## 3. Another OWL implementation

An implementation with its own RDF parser does §1.3 and §1.4 in its own terms; one that reads OWL
through an RDF library already forked (jena-array for Java, rdflib-array for Python, oxigraph-array
for Rust) gets the sequence term from the library and does only the consumer, the renderer and the
expansion. The expansion (owl-array.md §6) is the same everywhere and is what owl-tests-contrib will
check, once a second implementation exists.
