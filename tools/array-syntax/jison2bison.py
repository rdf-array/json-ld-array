"""Reduce a (non-EBNF) Jison grammar to a bare bison grammar: same rules and precedence
declarations, no actions and no lexer, so bison can report its LALR(1) conflicts.
usage: jison2bison.py in.jison out.y"""
import re, sys
src = open(sys.argv[1]).read()
head, body = src.split('%% /* language grammar */', 1)
head = re.sub(r'%lex.*?/lex', '', re.sub(r'%\{.*?%\}', '', head, flags=re.S), flags=re.S)
lits, toks = {}, []
def lit(q):
    if q not in lits: lits[q] = 'L%d' % len(lits)
    return lits[q]
def tokenize(s):
    i, out = 0, []
    while i < len(s):
        c = s[i]
        if c.isspace(): i += 1
        elif s.startswith('//', i): i = s.find('\n', i) if '\n' in s[i:] else len(s)
        elif s.startswith('/*', i): i = s.index('*/', i) + 2
        elif s.startswith('->', i): i = s.find('\n', i) if '\n' in s[i:] else len(s)
        elif c in '\'"':
            j = s.index(c, i + 1); out.append(('T', lit(s[i + 1:j]))); i = j + 1
        elif c == '{':                      # skip a balanced action, minding JS strings and comments
            d, i = 1, i + 1
            while d:
                if s[i] in '\'"`':
                    q = s[i]; i += 1
                    while s[i] != q: i += 2 if s[i] == '\\' else 1
                elif s.startswith('//', i): i = s.index('\n', i)
                elif s.startswith('/*', i): i = s.index('*/', i) + 1
                elif s[i] == '{': d += 1
                elif s[i] == '}': d -= 1
                i += 1
        elif c in ':|;': out.append((c, c)); i += 1
        elif s.startswith('%prec', i): out.append(('P', '%prec')); i += 5
        else:
            m = re.match(r'[A-Za-z_][\w]*', s[i:]); out.append(('N', m.group())); i += m.end()
    return out
prec = []
for line in head.split('\n'):
    m = re.match(r'\s*%(left|right|nonassoc)\s+(.*)', line)
    if m: prec.append('%%%s %s' % (m.group(1), ' '.join(lit(t[1:-1]) if t[0] in '\'"' else t for t in m.group(2).split())))
start = re.search(r'%start\s+(\w+)', head).group(1)
rules, lhs, alt, t = [], None, None, tokenize(body)
for k, (kind, v) in enumerate(t):
    if kind == 'N' and k + 1 < len(t) and t[k + 1][0] == ':': lhs = v; alt = []; rules.append((lhs, [alt]))
    elif kind == ':': pass
    elif kind == '|': alt = []; rules[-1][1].append(alt)
    elif kind == ';': pass
    else: alt.append(v)
nonterms = {r[0] for r in rules}
terms = sorted({s for r in rules for a in r[1] for s in a if s not in nonterms and s != '%prec'} - set(lits.values()))
out = ['%token ' + ' '.join(terms + sorted(lits.values(), key=lambda x: int(x[1:])))] + prec + ['%start ' + start, '%%']
for l, alts in rules: out.append('%s: %s ;' % (l, '\n  | '.join(' '.join(a) or '/* empty */' for a in alts)))
open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
