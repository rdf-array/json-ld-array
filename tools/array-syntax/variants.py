"""Write ShExC grammar variants for array syntaxes. usage: variants.py ShExJison.jison outdir"""
import re, sys, os
src, outdir = open(sys.argv[1]).read(), sys.argv[2]
ATOMS = ('shapeAtom', 'shapeAtomNoRef', 'inlineShapeAtom')  # not extendsShapeAtom: EXTENDS LIST IRI { would be ambiguous

# B0: ShExC without the ((x))[m,n] strawman and the precedence that resolved it
b0 = '\n'.join(l for l in src.split('\n') if "'(' '(' " not in l)
b0 = re.sub(r'^%nonassoc .*\n', '', b0, flags=re.M).replace(' %prec PAREN_SHAPE_EXPR', '')
b0 = b0.replace("IT_LITERAL              [Ll][Ii][Tt][Ee][Rr][Aa][Ll]",
                "IT_LITERAL              [Ll][Ii][Tt][Ee][Rr][Aa][Ll]\nIT_LIST                 [Ll][Ii][Ss][Tt]")
b0 = b0.replace("{IT_LITERAL}            return 'IT_LITERAL';",
                "{IT_LITERAL}            return 'IT_LITERAL';\n{IT_LIST}               return 'IT_LIST';")

def with_list(rules):
    g = b0
    for a in ATOMS:   # every shape-atom flavour gets `| listShape`
        g = re.sub(r'^(%s:\n)' % a, r'\1      listShape\n    | ', g, count=1, flags=re.M)
    return g + '\n' + rules

COMMON = r'''
listOneOf:
      listEachOf	-> $1
    | listOneOf '|' listEachOf	-> $1.type === "OneOf" && !$1.min ? ($1.exprs.push($3), $1) : { type: "OneOf", exprs: [$1, $3] }
    ;
listEachOf:
      listUnary	-> $1
    | listEachOf ';' listUnary	-> $1.type === "EachOf" && !$1.closed ? ($1.exprs.push($3), $1) : { type: "EachOf", exprs: [$1, $3] }
    ;
listUnary:
      listMember	-> $1
    | listMember cardinality	-> "min" in $1 ? Object.assign({ type: "EachOf", exprs: [$1] }, $2) : Object.assign($1, $2)
    ;
'''
GROUP = r'''    | '(' listOneOf ')'	-> Object.assign($2, { closed: true })
    ;
'''
V = {}   # the variants of the note's table; G is the one it proposes
V['B0'] = b0
V['A'] = with_list(r'''
listShape:
      IT_LIST listBoundsOpt inlineShapeAtom	-> Object.assign({ type: "ListShape", member: $3 }, $2)
    ;
listBoundsOpt:
      	-> {}
    | REPEAT_RANGE	-> yy.parser.parse ? cardOf($1) : {}
    ;
''')
V['B'] = with_list(r'''
listShape:
      IT_LIST '(' listOneOf ')'	-> { type: "ListShape", expression: $3 }
    ;
listMember:
      inlineShapeExpression	-> { type: "Member", shapeExpr: $1 }
''' + GROUP + COMMON)
C_MEMBER = r'''
listMember:
      listMemberOr	-> { type: "Member", shapeExpr: $1 }
''' + GROUP + r'''
/* an inline shape expression whose first atom is not parenthesised: inside LIST ( ), '(' is a group */
listMemberOr:
      listMemberAnd _Q_O_QIT_OR_E_S_QinlineShapeAnd_E_C_E_Star	-> shapeJunction("ShapeOr", $1, $2)
    ;
listMemberAnd:
      listMemberNot _Q_O_QIT_AND_E_S_QinlineShapeNot_E_C_E_Star	-> shapeJunction("ShapeAnd", $1, $2)
    ;
listMemberNot:
      listMemberAtom
    | IT_NOT inlineShapeAtom	-> { type: "ShapeNot", "shapeExpr": nonest($2) }
    ;
listMemberAtom:
      nonLitInlineNodeConstraint _QinlineShapeOrRef_E_Opt	-> $2 ? { type: "ShapeAnd", shapeExprs: [ extend({ type: "NodeConstraint" }, $1), $2 ] } : $1
    | litInlineNodeConstraint
    | inlineShapeOrRef _QnonLitInlineNodeConstraint_E_Opt	-> $2 ? { type: "ShapeAnd", shapeExprs: [ extend({ type: "NodeConstraint" }, $1), $2 ] } : $1
    | listShape
    | '.'	-> yy.EmptyShape
    ;
''' + COMMON
V['C'] = with_list(r'''
listShape:
      IT_LIST '(' listOneOf ')'	-> { type: "ListShape", expression: $3 }
    ;
''' + C_MEMBER)
V['D'] = with_list(r'''
listShape:
      IT_LIST inlineShapeAtom listFacets	-> Object.assign({ type: "ListShape", member: $2 }, $3)
    ;
listFacets:
      	-> {}
    | listFacets IT_MINLENGTH INTEGER	-> Object.assign($1, { min: parseInt($3, 10) })
    | listFacets IT_MAXLENGTH INTEGER	-> Object.assign($1, { max: parseInt($3, 10) })
    ;
''')
V['E'] = with_list(r'''
listShape:
      IT_LIST '(' listOneOf ')'	-> { type: "ListShape", expression: $3 }
    | IT_LIST REPEAT_RANGE inlineShapeAtom	-> { type: "ListShape", expression: Object.assign({ type: "Member", shapeExpr: $3 }, cardOf($2)) }
    ;
''' + C_MEMBER)
V['F'] = with_list(r'''
listShape:
      IT_LIST '(' listOneOf ')'	-> { type: "ListShape", expression: $3 }
    | IT_LIST REPEAT_RANGE inlineShapeAtom	-> { type: "ListShape", expression: Object.assign({ type: "Member", shapeExpr: $3 }, cardOf($2)) }
    | IT_LIST listMemberAtom	-> { type: "ListShape", expression: { type: "Member", shapeExpr: $2, min: 0, max: UNBOUNDED } }
    ;
''' + C_MEMBER)
V['G'] = with_list(r'''
listShape:
      IT_LIST '(' listOneOf ')'	-> { type: "ListShape", expression: $3 }
    | IT_LIST cardinality inlineShapeAtom	-> { type: "ListShape", expression: Object.assign({ type: "Member", shapeExpr: $3 }, $2) }
    ;
''' + C_MEMBER)
CARD = r'''
  function cardOf (rr) { // {m}, {m,}, {m,*}, {m,n} -> { min, max }
    const nums = rr.match(/(\d+)/g), m = parseInt(nums[0], 10);
    return { min: m, max: nums.length === 2 ? parseInt(nums[1], 10) : rr.indexOf(',') === -1 ? m : UNBOUNDED };
  }
%}'''
for k, g in V.items():
    g = g.replace('yy.parser.parse ? cardOf($1) : {}', 'cardOf($1)')
    g = g.replace('\n%}', CARD, 1)
    open(os.path.join(outdir, k + '.jison'), 'w').write(g)
