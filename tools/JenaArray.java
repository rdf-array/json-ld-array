import java.io.*;
import java.nio.file.*;
import java.nio.file.Files;
import org.apache.jena.query.*;
import org.apache.jena.riot.*;
import org.apache.jena.sparql.core.DatasetGraph;
import org.apache.jena.sparql.core.DatasetGraphFactory;
import org.apache.jena.sparql.resultset.ResultsFormat;

/** Drive jena-array for test-suite rewriting.
 *  parse FILE [BASE]               -> N-Quads-array on stdout
 *  query QUERY DATA|- [NAMED...]   -> SPARQL JSON results (or N-Quads-array for CONSTRUCT/DESCRIBE)
 *  update UPDATE DATA|-            -> N-Quads-array of the dataset after the update
 *  shacl SHAPES DATA               -> the SHACL-array validation report as N-Triples-array */
public class JenaArray {
    static boolean hasSeq(org.apache.jena.graph.Node n) {
        if (n.isNodeSeq()) return true;
        if (n.isNodeTriple()) { var t = n.getTriple(); return hasSeq(t.getSubject()) || hasSeq(t.getObject()); }
        return n.getClass().getSimpleName().equals("Node_SeqIndex");
    }
    public static void main(String... a) throws Exception {
        org.apache.jena.sys.JenaSystem.init();
        switch (a[0]) {
            case "parse" -> {
                DatasetGraph dsg = DatasetGraphFactory.createTxnMem();
                RDFParser.source(a[1]).base(a.length > 2 ? a[2] : Path.of(a[1]).toUri().toString()).parse(dsg);
                RDFDataMgr.write(System.out, dsg, Lang.NQUADS);
            }
            case "query" -> {
                Dataset ds = DatasetFactory.createTxnMem();
                if (!a[2].equals("-")) RDFParser.source(a[2]).base(Path.of(a[2]).toUri().toString()).parse(ds.asDatasetGraph().getDefaultGraph());
                for (int i = 3; i < a.length; i++)
                    RDFParser.source(a[i]).base(Path.of(a[i]).toUri().toString()).parse(ds.asDatasetGraph().getGraph(org.apache.jena.graph.NodeFactory.createURI(Path.of(a[i]).toUri().toString())));
                Query q = QueryFactory.read(a[1], null, Syntax.syntaxARQ);
                try (QueryExecution qe = QueryExecutionFactory.create(q, ds)) {
                    if (q.isSelectType()) ResultSetFormatter.outputAsJSON(System.out, qe.execSelect());
                    else if (q.isAskType()) ResultSetFormatter.outputAsJSON(System.out, qe.execAsk());
                    else RDFDataMgr.write(System.out, q.isConstructType() ? qe.execConstruct() : qe.execDescribe(), Lang.NTRIPLES);
                }
            }
            case "update" -> {
                DatasetGraph dsg = DatasetGraphFactory.createTxnMem();
                if (!a[2].equals("-")) RDFParser.source(a[2]).base(Path.of(a[2]).toUri().toString()).parse(dsg.getDefaultGraph());
                org.apache.jena.update.UpdateAction.readExecute(a[1], dsg);
                RDFDataMgr.write(System.out, dsg, Lang.NQUADS);
            }
            case "inspect" -> {
                // print "seq" when a query, update or data file holds a sequence term (or position pattern)
                for (int i = 1; i < a.length; i++) {
                    String f = a[i];
                    boolean seq;
                    try {
                        if (f.endsWith(".rq")) {
                            Query q = QueryFactory.read(f, null, Syntax.syntaxARQ);
                            String alg = org.apache.jena.sparql.algebra.Algebra.compile(q).toString();
                            seq = alg.contains("seqterm") || alg.contains("seqpos")
                                || (q.getConstructTemplate() != null && q.getConstructTemplate().getTriples().stream()
                                    .anyMatch(t -> hasSeq(t.getSubject()) || hasSeq(t.getObject())));
                        } else if (f.endsWith(".ru")) {
                            String u = org.apache.jena.update.UpdateFactory.read(f, Syntax.syntaxARQ).toString();
                            seq = u.contains("seqterm") || java.util.regex.Pattern.compile("(?s)\\(\\s*(\\)|[?<_\"0-9:])").matcher(u.replaceAll("FILTER\\s*\\(|BIND\\s*\\(|\\b[A-Za-z]+\\s*\\(", "")).find();
                        } else {
                            DatasetGraph dsg = DatasetGraphFactory.createTxnMem();
                            RDFParser.source(f).parse(dsg);
                            seq = java.util.stream.StreamSupport.stream(java.util.Spliterators.spliteratorUnknownSize(dsg.find(), 0), false)
                                .anyMatch(qd -> hasSeq(qd.getSubject()) || hasSeq(qd.getObject()));
                        }
                    } catch (Exception e) { System.out.println("error\t" + f + "\t" + e.getMessage().replace('\n', ' ')); continue; }
                    System.out.println((seq ? "seq" : "none") + "\t" + f);
                }
            }
            case "shex" -> {
                // shex SCHEMA DATA FOCUS SHAPE [BASE]: print conformant or nonconformant
                String base = a.length > 5 ? a[5] : Path.of(a[1]).toUri().toString();
                org.apache.jena.shex.ShexSchema schema = a[1].endsWith(".shex")
                    ? org.apache.jena.shex.Shex.readSchema(a[1], base)
                    : org.apache.jena.shex.Shex.schemaFromStringShExR(Files.readString(Path.of(a[1])), base);
                org.apache.jena.graph.Graph g = RDFParser.source(a[2]).base(Path.of(a[2]).toUri().toString()).toGraph();
                var report = org.apache.jena.shex.ShexValidator.getNew(java.util.List.of())
                    .validate(g, schema, org.apache.jena.graph.NodeFactory.createURI(a[4]), org.apache.jena.graph.NodeFactory.createURI(a[3]));
                System.out.println(report.conforms() ? "conformant" : "nonconformant");
            }
            case "shacl" -> {
                // shacl SHAPES DATA: the validation report as N-Triples-array, or "error: …" when the
                // shapes graph is ill-formed (jena-shacl must be on the classpath)
                org.apache.jena.graph.Graph shapes = RDFParser.source(a[1]).base(Path.of(a[1]).toUri().toString()).toGraph();
                org.apache.jena.graph.Graph data = a[2].equals(a[1]) ? shapes
                    : RDFParser.source(a[2]).base(Path.of(a[2]).toUri().toString()).toGraph();
                try {
                    var report = org.apache.jena.shacl.ShaclValidator.get().validate(shapes, data);
                    RDFDataMgr.write(System.out, report.getGraph(), Lang.NTRIPLES);
                } catch (RuntimeException ex) {
                    System.out.println("error: " + ex.getMessage());
                }
            }
            default -> throw new IllegalArgumentException(a[0]);
        }
    }
}
