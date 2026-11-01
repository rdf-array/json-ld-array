// Nested-sequence examples for the candidate SPARQL and ShEx syntaxes: each is parsed by the
// patched grammars and then run by the small evaluator below, so the results come from the ASTs.
const parseSparql = require('./sparql.js')(require('path').resolve(process.env.WORK, 'sparqljs/lib/SparqlParser.js'));
const shexParsers = { A: require('./shex.js')('A'), C: require('./shex.js')('C'), E: require('./shex.js')('E'), F: require('./shex.js')('F'), G: require('./shex.js')('G') };
const XSD = 'http://www.w3.org/2001/XMLSchema#';
const PRE = 'PREFIX : <http://ex/> PREFIX xsd: <' + XSD + '>\n';

// ---- data: Turtle, read through the patched grammar's INSERT DATA (collections become Seq terms)
const DATA = `
:obs1 :component ( ( "8480-6" "systolic"  ( 120 "mm[Hg]" ) )
                   ( "8462-4" "diastolic" (  80 "mm[Hg]" ) ) ) .
:obs2 :component ( ( "8480-6" "systolic"  ( 150 "mm[Hg]" ) )
                   ( "8462-4" "diastolic" (  95 "mm[Hg]" ) ) ) .
:obs3 :component ( ( "8480-6" "systolic"  ( "high" "mm[Hg]" ) ) ) .
:m1   :matrix ( ( 1 2 3 ) ( 4 5 6 ) ) .
:m2   :matrix ( ( 1 2 3 ) ( 4 5 ) ) .
:poly :points ( ( 0 0 ) ( 3 0 ) ( 3 4 ) ) .
:kv   :pairs  ( "a" 1 "b" 2 "c" 3 ) .
:tree :node   ( "root" ( ( "left" ( ) ) ( "right" ( ( "leaf" ( ) ) ) ) ) ) .`;
const triples = parseSparql(PRE + 'INSERT DATA {' + DATA + '}').updates[0].insert[0].triples;

// ---- terms
const isSeq = t => t && t.termType === 'Seq';
const num = t => t && t.termType === 'Literal' && /#(integer|decimal|double)$/.test(t.datatype.value) ? Number(t.value) : undefined;
const lit = (v) => typeof v === 'number' ? { termType: 'Literal', value: String(v), datatype: { value: XSD + (Number.isInteger(v) ? 'integer' : 'decimal') } }
  : typeof v === 'boolean' ? { termType: 'Literal', value: String(v), datatype: { value: XSD + 'boolean' } }
  : { termType: 'Literal', value: v, datatype: { value: XSD + 'string' } };
function eq(a, b) {
  if (isSeq(a) || isSeq(b)) return isSeq(a) && isSeq(b) && a.members.length === b.members.length && a.members.every((m, i) => eq(m, b.members[i]));
  if (num(a) !== undefined && num(b) !== undefined) return num(a) === num(b);
  return a.termType === b.termType && a.value === b.value && (a.termType !== 'Literal' || a.datatype.value === b.datatype.value);
}
function show(t) {
  if (isSeq(t)) return '(' + t.members.map(show).join(' ') + ')';
  if (t.termType === 'NamedNode') return t.value.replace('http://ex/', ':');
  if (t.termType === 'Literal') return num(t) !== undefined ? t.value : JSON.stringify(t.value);
  if (t.termType === 'Variable') return '?' + t.value;
  if (t.termType === 'Gap') return t.name ? '...?' + t.name : '...';
  return String(t.value);
}

// ---- SPARQL: matching sequence patterns (with ... gaps), UNNEST, BIND, FILTER
function* match(p, t, b) {
  if (p.termType === 'Variable') {
    if (p.value in b) { if (eq(b[p.value], t)) yield b; } else yield { ...b, [p.value]: t };
  } else if (isSeq(p)) {
    if (isSeq(t)) yield* matchMembers(p.members, 0, t.members, 0, b);
  } else if (eq(p, t)) yield b;
}
function* matchMembers(ps, i, ts, j, b) {
  if (i === ps.length) { if (j === ts.length) yield b; return; }
  if (ps[i].termType === 'Gap') {   // a gap takes any run; a named gap (...?v) also binds ?v to that run
    for (let k = j; k <= ts.length; k++) {
      if (!ps[i].name) yield* matchMembers(ps, i + 1, ts, k, b);
      else for (const b2 of match({ termType: 'Variable', value: ps[i].name }, { termType: 'Seq', members: ts.slice(j, k) }, b)) yield* matchMembers(ps, i + 1, ts, k, b2);
    }
    return;
  }
  if (j < ts.length) for (const b2 of match(ps[i], ts[j], b)) yield* matchMembers(ps, i + 1, ts, j + 1, b2);
}
function evalExpr(e, b) {
  if (e.termType === 'Variable') { if (!(e.value in b)) throw 'unbound'; return b[e.value]; }
  if (e.termType) return e;
  const a = () => e.args.map(x => evalExpr(x, b)), o = e.operator;
  if (o === 'seq') return { termType: 'Seq', members: a() };
  if (o === 'index') { const [s, i] = a(); if (!isSeq(s) || !(num(i) >= 1 && num(i) <= s.members.length)) throw 'index'; return s.members[num(i) - 1]; }
  if (o === 'slice') {   // s[m...n], closed and 1-based; a missing end is the sequence's; clamped, as in SQL, Cypher and Python
    const s = evalExpr(e.args[0], b), m = e.args[1] ? num(evalExpr(e.args[1], b)) : 1, n = e.args[2] ? num(evalExpr(e.args[2], b)) : Infinity;
    if (!isSeq(s) || !(m >= 1) || !(n >= 0)) throw 'slice';
    return { termType: 'Seq', members: s.members.slice(m - 1, n) };
  }
  if (o === 'seqlen') { const [s] = a(); if (!isSeq(s)) throw 'type'; return lit(s.members.length); }
  if (o === 'floor') { const [x] = a(); if (num(x) === undefined) throw 'type'; return lit(Math.floor(num(x))); }
  if (o === 'isseq') return lit(isSeq(a()[0]));
  if (o === 'inseq' || o === 'notinseq') { const [x, s] = a(); if (!isSeq(s)) throw 'type'; return lit(s.members.some(m => eq(m, x)) === (o === 'inseq')); }
  if (o === '&&' || o === '||') { const [x, y] = a().map(ebv); return lit(o === '&&' ? x && y : x || y); }
  const [x, y] = a();
  if (o === '=') return lit(eq(x, y)); if (o === '!=') return lit(!eq(x, y));
  if ('+-*/'.includes(o)) { if (num(x) === undefined || num(y) === undefined) throw 'type'; return lit({ '+': num(x) + num(y), '-': num(x) - num(y), '*': num(x) * num(y), '/': num(x) / num(y) }[o]); }
  if ((num(x) === undefined) !== (num(y) === undefined) || isSeq(x) || isSeq(y)) throw 'type';
  const [p, q] = num(x) !== undefined ? [num(x), num(y)] : [x.value, y.value];
  return lit({ '<': p < q, '>': p > q, '<=': p <= q, '>=': p >= q }[o]);
}
const ebv = t => t.datatype && t.datatype.value === XSD + 'boolean' ? t.value === 'true' : !!t.value;
function evalWhere(patterns) {
  let sols = [{}];
  for (const pat of patterns) {
    if (pat.type === 'bgp') for (const tp of pat.triples)
      sols = sols.flatMap(b => triples.flatMap(t => [...match(tp.subject, t.subject, b)].flatMap(b1 =>
        [...match(tp.predicate, t.predicate, b1)].flatMap(b2 => [...match(tp.object, t.object, b2)]))));
    else if (pat.type === 'unnest') sols = sols.flatMap(b => {
      let s; try { s = evalExpr(pat.expression, b); } catch (e) { return []; }
      return isSeq(s) ? s.members.map((m, k) => ({ ...b, [pat.variable.value]: m, ...(pat.position ? { [pat.position.value]: lit(k + 1) } : {}) })) : [];
    });
    else if (pat.type === 'bind') sols = sols.map(b => { try { return { ...b, [pat.variable.value]: evalExpr(pat.expression, b) }; } catch (e) { return b; } });
    else if (pat.type === 'filter') sols = sols.filter(b => { try { return ebv(evalExpr(pat.expression, b)); } catch (e) { return false; } });
    else throw new Error('pattern ' + pat.type);
  }
  return sols;
}

// ---- ShEx: ListShape over Member / EachOf / OneOf, with min/max on any of them
const shapes = {};
function conforms(se, t) {
  if (typeof se === 'string') return conforms(shapes[se], t);
  switch (se.type) {
    case 'ShapeAnd': return se.shapeExprs.every(s => conforms(s, t));
    case 'ShapeOr': return se.shapeExprs.some(s => conforms(s, t));
    case 'ShapeNot': return !conforms(se.shapeExpr, t);
    case 'Shape': return !se.expression;                      // only `.` is needed here
    case 'NodeConstraint':
      if (se.datatype) return t.termType === 'Literal' && t.datatype.value === se.datatype;
      if (se.values) return se.values.some(v => eq(t, typeof v === 'string' ? { termType: 'NamedNode', value: v } : { termType: 'Literal', value: v.value, datatype: { value: v.type || XSD + 'string' } }));
      if (se.nodeKind === 'literal') return t.termType === 'Literal';
      throw new Error('constraint ' + JSON.stringify(se));
    case 'ListShape':
      if (!isSeq(t)) return false;
      if (se.member) return t.members.length >= (se.min ?? 0) && (se.max === undefined || se.max === -1 || t.members.length <= se.max) && t.members.every(m => conforms(se.member, m));
      return ends(se.expression, t.members, 0).has(t.members.length);
  }
  throw new Error('shape ' + se.type);
}
function ends(e, ms, i) {   // the set of positions where e can stop matching ms, starting at i
  const once = j => e.type === 'Member' ? new Set(j < ms.length && conforms(e.shapeExpr, ms[j]) ? [j + 1] : [])
    : e.type === 'OneOf' ? new Set(e.exprs.flatMap(x => [...ends(x, ms, j)]))
    : e.exprs.reduce((s, x) => new Set([...s].flatMap(k => [...ends(x, ms, k)])), new Set([j]));
  const min = e.min ?? 1, max = e.max === undefined ? 1 : e.max === -1 ? Infinity : e.max;
  let cur = new Set([i]), out = new Set(min === 0 ? [i] : []);
  for (let n = 1; n <= max && cur.size; n++) {
    const next = new Set([...cur].flatMap(j => [...once(j)].filter(k => k > j || e.type !== 'Member')));
    if (n >= min) next.forEach(k => out.add(k));
    if ([...next].every(k => cur.has(k))) break;               // no progress: stop repeating
    cur = next;
  }
  return out;
}
function compact(se) {   // ShExJ -> ShExC-like text, to show how the parser grouped things
  if (typeof se === 'string') return '@<' + se.replace('http://ex/', '') + '>';
  const card = x => x.min === undefined ? '' : ({ '0,1': '?', '0,-1': '*', '1,-1': '+' })[x.min + ',' + x.max] || ('{' + x.min + (x.max === x.min ? '' : ',' + (x.max === -1 ? '*' : x.max)) + '}');
  switch (se.type) {
    case 'ListShape': return se.member ? 'LIST' + (se.min !== undefined ? card(se) : '') + '<' + compact(se.member) + '>' : 'LIST(' + compact(se.expression) + ')';
    case 'Member': return compact(se.shapeExpr) + card(se);
    case 'EachOf': return '[' + se.exprs.map(compact).join(' ; ') + ']' + card(se);
    case 'OneOf': return '[' + se.exprs.map(compact).join(' | ') + ']' + card(se);
    case 'NodeConstraint': return se.datatype ? se.datatype.replace(XSD, 'xsd:') : JSON.stringify(se);
    case 'ShapeAnd': return '(' + se.shapeExprs.map(compact).join(' AND ') + ')';
    case 'ShapeOr': return '(' + se.shapeExprs.map(compact).join(' OR ') + ')';
    case 'ShapeNot': return 'NOT ' + compact(se.shapeExpr);
    case 'Shape': return !se.expression ? '.' : se.expression.type === 'TripleConstraint'
      ? '{ ' + se.expression.predicate.replace('http://ex/', ':') + ' ' + compact(se.expression.valueExpr) + ' ' + card(se.expression) + ' }' : '{…}';
  }
  return JSON.stringify(se);
}

const s2 = s => s.shapes.map(d => '<' + d.id.replace('http://ex/', '') + '> ' + compact(d.shapeExpr)).join('  ');
module.exports = { parseSparql, shexParsers, PRE, DATA, triples, evalWhere, conforms, compact, shapes, show, XSD };

if (require.main === module) {
  const out = [];
  const say = s => out.push(s);
  say('## Data\n```turtle' + DATA + '\n```');
  for (const [title, q] of require('./examples.js').sparql) {
    say('\n### ' + title + '\n```sparql\n' + q.trim() + '\n```');
    let ast; try { ast = parseSparql(PRE + q); } catch (e) { say('PARSE ERROR: ' + e.message.split('\n').slice(0, 3).join(' / ')); continue; }
    const vars = ast.variables.map(v => v.value);
    const rows = evalWhere(ast.where).map(b => vars.map(v => b[v] ? show(b[v]) : '').join(' | '));
    say('| ' + vars.join(' | ') + ' |\n|' + vars.map(() => '---').join('|') + '|\n' + (rows.length ? rows.map(r => '| ' + r + ' |').join('\n') : '| (no rows) |'));
  }
  for (const [title, variant, schema, focus] of require('./examples.js').shex) {
    say('\n### ' + title + ' (variant ' + variant + ')\n```shex\n' + schema.trim() + '\n```');
    let s; try { s = shexParsers[variant](PRE + schema, 'http://ex/'); } catch (e) { say('PARSE ERROR: ' + e.message.split('\n').slice(0, 3).join(' / ')); continue; }
    for (const d of s.shapes) { shapes[d.id] = d.shapeExpr; say('parsed `<' + d.id.replace('http://ex/', '') + '>` as `' + compact(d.shapeExpr) + '`'); }
    for (const [subject, predicate, shape] of focus) {
      for (const t of triples.filter(t => t.subject.value === 'http://ex/' + subject && t.predicate.value === 'http://ex/' + predicate))
        say(`- ${show(t.object)} → <${shape}>: **${conforms('http://ex/' + shape, t.object) ? 'conforms' : 'fails'}**`);
    }
  }
  say('\n## Edge cases');
  for (const [title, lang, text, expect] of require('./examples.js').edges) {
    let r;
    try {
      if (lang === 'sparql') { const a = parseSparql(PRE + text); r = JSON.stringify(a.where || a.template, (k, v) => v && v.termType && v.termType !== 'Literal' || (v && v.termType === 'Literal') ? show(v) : v); }
      else r = s2(shexParsers[lang](PRE + text, 'http://ex/'));
    } catch (e) { r = 'REJECTED: ' + e.message.split('\n').slice(0, 4).join(' ').replace(/\s+/g, ' ').slice(0, 160); }
    say('- ' + title + ' (' + lang + '; expected: ' + expect + ')\n  `' + text.trim() + '`\n  → ' + r);
  }
  console.log(out.join('\n'));
}
