import java.io.File;
import java.util.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.rdfarray.SequenceAwareReasoner;
import org.semanticweb.owlapi.rdfarray.SequenceAwareReasonerFactory;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.owlapi.util.*;
import org.semanticweb.owlapi.util.mansyntax.ManchesterOWLSyntaxParser;
import org.semanticweb.owlapi.expression.ShortFormEntityChecker;

/** rdf-array: loads subjects.ttl through its catalog, reasons with HermiT behind the OWL-array decorator,
 *  and runs the DL queries of README.md, comparing with the expected instances. */
public class FhirReasoning {
    static final Map<String, String> PREFIXES = new LinkedHashMap<>();
    static {
        PREFIXES.put("fhir", "http://hl7.org/fhir/");
        PREFIXES.put("sct", "http://snomed.info/id/");
        PREFIXES.put("loinc", "https://loinc.org/rdf/");
        PREFIXES.put("ra", "https://rdf-array.github.io/rdf-array/vocab#");
        PREFIXES.put("xsd", "http://www.w3.org/2001/XMLSchema#");
        PREFIXES.put("", "https://rdf-array.github.io/rdf-array/examples/fhir/arthritis.ttl#");
        PREFIXES.put("bp", "https://rdf-array.github.io/rdf-array/examples/fhir/blood-pressure.ttl#");
        PREFIXES.put("amy", "https://rdf-array.github.io/rdf-array/examples/fhir/subject-amy.ttl#");
        PREFIXES.put("bob", "https://rdf-array.github.io/rdf-array/examples/fhir/subject-bob.ttl#");
        PREFIXES.put("sue", "https://rdf-array.github.io/rdf-array/examples/fhir/subject-sue.ttl#");
    }

    static String qname(IRI iri) {
        String s = iri.toString();
        for (Map.Entry<String, String> e : PREFIXES.entrySet()) {
            if (s.startsWith(e.getValue())) return e.getKey() + ":" + s.substring(e.getValue().length());
        }
        return "<" + s + ">";
    }

    static int failures = 0;

    public static void main(String[] args) throws Exception {
        File dir = new File(args[0]);
        OWLOntologyManager m = OWLManager.createOWLOntologyManager();
        // catalog-v001.xml, as Protégé reads it
        Document cat = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(new File(dir, "catalog-v001.xml"));
        NodeList uris = cat.getElementsByTagName("uri");
        for (int i = 0; i < uris.getLength(); i++) {
            Element u = (Element) uris.item(i);
            m.getIRIMappers().add(new SimpleIRIMapper(IRI.create(u.getAttribute("name")),
                IRI.create(new File(dir, u.getAttribute("uri")).getCanonicalFile().toURI().toString())));
        }
        long t0 = System.currentTimeMillis();
        OWLOntology o = m.loadOntologyFromOntologyDocument(new File(dir, "subjects.ttl"));
        System.out.println("loaded " + o.getImportsClosure().size() + " ontologies, "
            + o.getAxiomCount(org.semanticweb.owlapi.model.parameters.Imports.INCLUDED) + " axioms in " + (System.currentTimeMillis() - t0) + " ms");
        for (OWLOntology x : o.getImportsClosure()) System.out.println("  " + x.getOntologyID().getOntologyIRI().get() + " (" + x.getAxiomCount() + ")");

        // any ladder left? rdf:first in the signature would mean a list was read as triples
        boolean ladder = false;
        for (OWLOntology x : o.getImportsClosure())
            for (OWLEntity e : x.getSignature()) if (e.getIRI().toString().startsWith("http://www.w3.org/1999/02/22-rdf-syntax-ns#first")) ladder = true;
        System.out.println("rdf:first in signature: " + ladder);

        t0 = System.currentTimeMillis();
        OWLReasonerFactory rf = new SequenceAwareReasonerFactory(new org.semanticweb.HermiT.ReasonerFactory());
        SequenceAwareReasoner r = (SequenceAwareReasoner) rf.createReasoner(o);
        System.out.println("reasoner: " + r.getReasonerName() + "; consistent: " + r.isConsistent() + " (" + (System.currentTimeMillis() - t0) + " ms)");
        OWLDataFactory df = m.getOWLDataFactory();
        OWLClass raSequence = df.getOWLClass(IRI.create(PREFIXES.get("ra") + "Sequence"));
        Set<OWLSequence> seqs = r.getSequenceInstances(raSequence, false);
        System.out.println("sequences in the data: " + seqs.size());
        t0 = System.currentTimeMillis();
        r.precomputeInferences(InferenceType.CLASS_HIERARCHY, InferenceType.CLASS_ASSERTIONS);
        System.out.println("classified in " + (System.currentTimeMillis() - t0) + " ms; unsatisfiable: "
            + r.getUnsatisfiableClasses().getEntitiesMinusBottom().size());

        // a Manchester parser with the prefixes above, as Protégé's DL Query tab parses
        ManchesterOWLSyntaxParser p = OWLManager.createManchesterParser();
        p.setDefaultOntology(o);
        ShortFormProvider sfp = new ShortFormProvider() {
            public String getShortForm(OWLEntity e) { return qname(e.getIRI()); }
            public void dispose() {}
        };
        p.setOWLEntityChecker(new ShortFormEntityChecker(new BidirectionalShortFormProviderAdapter(m, o.getImportsClosure(), sfp)));

        String[][] queries = {
            { "fhir:Observation and fhir:code some sct:Rheumatoid_arthritis-disorder", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { "fhir:Observation and fhir:code some sct:69896004", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { ":Observation-of-Rheumatoid_arthritis", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { ":Observation-of-Seronegative_rheumatoid_arthritis", "bob:Obs1" },
            { ":Observation-of-Seropositive_rheumatoid_arthritis", "sue:Obs1" },
            { "fhir:Observation and fhir:code some sct:Arthritis-disorder", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { ":Observation-of-inflammatory_musculoskeletal_disorder", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { "fhir:Observation and fhir:code some (sct:Inflammatory_disorder-disorder and sct:role_group-attr some (sct:Associated_morphology-attr some sct:Inflammatory_morphology-morph and sct:Finding_site-attr some sct:Structure_of_musculoskeletal_system-body))", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { "fhir:Observation and fhir:code some (fhir:coding some (ra:member some :Coding-in-ICD-10))", "amy:Obs1 bob:Obs1 sue:Obs1" },
            { "fhir:Observation and fhir:code some (fhir:coding some (ra:member some :Coding-of-icd10-M05.9))", "sue:Obs1" },
            { ":Patient_with_rheumatoid_arthritis", "amy:asPatient bob:asPatient sue:asPatient" },
            { "fhir:Patient and inverse fhir:l some (inverse fhir:subject some :Observation-of-Seronegative_rheumatoid_arthritis)", "bob:asPatient" },
            { ":Observation-coded-first-in-SNOMED", "amy:Obs1" },
            { "fhir:Observation and fhir:code some (fhir:coding some (ra:first some :Coding-in-SNOMED))", "amy:Obs1" },
            { "fhir:Observation and fhir:code some (fhir:coding some (ra:last some :Coding-in-SNOMED))", "amy:Obs2 bob:Obs1" },
            { ":Observation-with-several-codings", "amy:Obs1 amy:Obs2 bob:Obs1" },
            { "fhir:Observation and fhir:code some (fhir:coding some (ra:length value 1))", "sue:Obs1" },
            { "bp:Observation-of-blood-pressure", "amy:Obs2" },
            { "bp:Observation-of-elevated-blood-pressure", "amy:Obs2" },
            { "bp:Two-component-blood-pressure", "amy:Obs2" },
            { "bp:Complete-blood-pressure", "amy:Obs2" },
            { "fhir:Observation and fhir:component some (ra:member some (fhir:value some (fhir:value some (fhir:v some xsd:decimal[>= 160]))))", "" },
            { "fhir:Patient and fhir:name some (ra:member some (fhir:given some (ra:length some xsd:integer[>= 2])))", "sue:asPatient" },
            { "fhir:Observation and fhir:code some (fhir:coding some ra:EmptySequence)", "" },
        };
        System.out.println();
        for (String[] q : queries) {
            String got;
            try {
                p.setStringToParse(q[0]);
                OWLClassExpression ce = p.parseClassExpression();
                TreeSet<String> names = new TreeSet<>();
                for (OWLNamedIndividual i : r.getInstances(ce, false).getFlattened()) names.add(qname(i.getIRI()));
                got = String.join(" ", names);
            } catch (Exception e) {
                got = "ERROR " + e.getClass().getSimpleName() + ": " + e.getMessage().replace('\n', ' ');
            }
            TreeSet<String> expected = new TreeSet<>(Arrays.asList(q[1].isEmpty() ? new String[0] : q[1].split(" ")));
            boolean ok = got.equals(String.join(" ", expected));
            if (!ok) failures++;
            System.out.println((ok ? "PASS " : "FAIL ") + q[0] + "\n      -> " + (got.isEmpty() ? "(none)" : got)
                + (ok ? "" : "\n      expected " + (q[1].isEmpty() ? "(none)" : q[1])));
        }

        // What the reasoner knows of a list term. Every FHIR list holds blank nodes (a Coding is one), so its
        // expansion individual is anonymous and no object closure is written (rdf-array/rdf-array#20): a
        // universal over the members holds when an axiom gives it, not from the list's own elements.
        System.out.println();
        OWLObjectProperty coding = df.getOWLObjectProperty(IRI.create(PREFIXES.get("fhir") + "coding"));
        OWLObjectProperty member = df.getOWLObjectProperty(IRI.create(PREFIXES.get("ra") + "member"));
        OWLClass codingClass = df.getOWLClass(IRI.create(PREFIXES.get("fhir") + "Coding"));
        OWLClass inSnomed = df.getOWLClass(IRI.create(PREFIXES.get("") + "Coding-in-SNOMED"));
        OWLClass inIcd = df.getOWLClass(IRI.create(PREFIXES.get("") + "Coding-in-ICD-10"));
        OWLSequence amyCodings = null;
        for (OWLAxiom ax : o.getAxioms(org.semanticweb.owlapi.model.parameters.Imports.INCLUDED)) {
            if (ax instanceof OWLObjectPropertyAssertionAxiom) {
                OWLObjectPropertyAssertionAxiom pa = (OWLObjectPropertyAssertionAxiom) ax;
                if (pa.getProperty().equals(coding) && pa.getObject() instanceof OWLSequence && ((OWLSequence) pa.getObject()).getLength() == 2
                    && o.getImportsClosure().stream().anyMatch(x -> x.getOntologyID().getOntologyIRI().get().toString().endsWith("subject-amy.ttl") && x.containsAxiom(ax))) {
                    OWLSequence s = (OWLSequence) pa.getObject();
                    // amy:Obs1's list: SNOMED then ICD-10 (amy:Obs2's lists are LOINC then SNOMED)
                    if (r.isEntailed(df.getOWLClassAssertionAxiom(df.getOWLObjectSomeValuesFrom(member, inIcd), s))) { amyCodings = s; break; }
                }
            }
        }
        System.out.println("amy:Obs1's coding list ( SNOMED ICD-10 ):");
        System.out.println("  ra:Sequence                                        " + r.isEntailed(df.getOWLClassAssertionAxiom(raSequence, amyCodings)));
        System.out.println("  ra:length value 2                                  " + r.isEntailed(df.getOWLClassAssertionAxiom(df.getOWLDataHasValue(df.getOWLDataProperty(IRI.create(PREFIXES.get("ra") + "length")), df.getOWLLiteral("2", org.semanticweb.owlapi.vocab.OWL2Datatype.XSD_NON_NEGATIVE_INTEGER)), amyCodings)));
        System.out.println("  ra:member some :Coding-in-SNOMED                   " + r.isEntailed(df.getOWLClassAssertionAxiom(df.getOWLObjectSomeValuesFrom(member, inSnomed), amyCodings)));
        System.out.println("  ra:first some :Coding-in-SNOMED                    " + r.isEntailed(df.getOWLClassAssertionAxiom(df.getOWLObjectSomeValuesFrom(df.getOWLObjectProperty(IRI.create(PREFIXES.get("ra") + "first")), inSnomed), amyCodings)));
        System.out.println("  ra:member only fhir:Coding   (from fhir-min's axiom) " + r.isEntailed(df.getOWLClassAssertionAxiom(df.getOWLObjectAllValuesFrom(member, codingClass), amyCodings)));
        boolean closed = r.isEntailed(df.getOWLClassAssertionAxiom(df.getOWLObjectAllValuesFrom(member, df.getOWLObjectUnionOf(inSnomed, inIcd)), amyCodings));
        System.out.println("  ra:member only (:Coding-in-SNOMED or :Coding-in-ICD-10) " + closed + (closed ? "" : "  <- true of the term, not entailed: no closure for a list holding blank nodes (#20)"));
        // the same gap as a DL query: observations all of whose codings are ICD-10 (sue:Obs1, if lists were closed)
        p.setStringToParse("fhir:Observation and fhir:code some (fhir:coding some (ra:member only :Coding-in-ICD-10))");
        System.out.println("  DL query 'all codings in ICD-10' -> " + r.getInstances(p.parseClassExpression(), false).getFlattened().size() + " instances (sue:Obs1 if lists were closed; #20)");

        // fhir.ttl's own axiom for the repeating element, `fhir:coding only fhir:Coding`, types the list; with
        // fhir:Base disjoint from ra:Sequence (fhir-min.ttl) the data becomes inconsistent.
        OWLOntology fhirMin = m.getOntology(IRI.create("https://rdf-array.github.io/rdf-array/examples/fhir/fhir-min.ttl"));
        OWLClass codeableConcept = df.getOWLClass(IRI.create(PREFIXES.get("fhir") + "CodeableConcept"));
        OWLAxiom fhirTtlAxiom = df.getOWLSubClassOfAxiom(codeableConcept, df.getOWLObjectAllValuesFrom(coding, codingClass));
        m.addAxiom(fhirMin, fhirTtlAxiom);
        r.flush();
        boolean inconsistent = !r.isConsistent();
        System.out.println("with fhir.ttl's `fhir:CodeableConcept SubClassOf fhir:coding only fhir:Coding` added: consistent = " + !inconsistent
            + (inconsistent ? " (as expected: the list is not a Coding)" : " (UNEXPECTED)"));
        if (!inconsistent) failures++;
        m.removeAxiom(fhirMin, fhirTtlAxiom);
        r.flush();
        System.out.println("removed again: consistent = " + r.isConsistent());
        System.out.println();
        System.out.println(failures == 0 ? "ALL PASS" : failures + " FAILURE(S)");
        r.dispose();
    }
}
