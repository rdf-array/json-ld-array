---
name: fork-array
description: Fork an RDF implementation into the rdf-array organisation as <project>-array and teach it the sequence term — naming, remotes, branch, banner and icon, notes, where the term goes in each layer, dependency pinning per ecosystem, commits, GitHub Pages, and where issues go (rdf-array/rdf-array, cross-repo or repo-specific). Use when adding a new -array fork or a forked dependency.
---

# Forking a project into rdf-array

rdf-array is RDF with one more kind of term, the sequence (`(1 2 3)`, `()`); see
[rdf-array.md](../../../docs/rdf-array.md). A fork teaches one project that term and removes the code
that built `rdf:first`/`rdf:rest` ladders or numbered `rdf:_n` container members. The formula below
is what every fork so far followed; the [Not yet forked](https://rdf-array.github.io/rdf-array/repos.html#not-yet-forked)
list (`targets` in [repos.json](../../../repos.json)) says which projects are worth it, in order, and [targets.md](../../../targets.md) what each
one's change list looks like.

## 1. Decide the closure first

List what the project must learn, layer by layer, and which of its dependencies carry those layers;
each such dependency is a fork of its own, pinned from the dependent fork. The layers:

| Layer | What changes | Done before in |
|---|---|---|
| data model | a sequence term: constructor, `elements`, equality by elements, the `(e1 e2 …)` spelling, membership in the subject and object positions | types-array, rdf-data-factory-array, jena-array (`Node_Seq`), rdflib-array (`rdflib.term.Sequence`), oxigraph-array (`oxrdf::Sequence`, and a `Subject` enum for triples' subjects) |
| term ↔ string | spelling and reading `( … )`, nested, with the elements' own spellings | rdf-string-array, rdf-string-ttl-array, N3.js-array's `value` |
| parsers | a collection becomes one term, `()` the empty sequence, nested collections nested terms; blank node property lists inside still hoist their triples; JSON-LD `@list`, RDF/XML `rdf:parseType="Collection"`, `rdf:li` no longer numbered | N3.js-array, jsonld-streaming-parser-array, rdfxml-streaming-parser-array, rdflib-array, traqula-array (SPARQL) |
| serializers | print sequences, nested; refuse where the format cannot (RDFLib's RDF/XML, TriX, HexTuples) | N3.js-array, jsonld-streaming-serializer-array, rdflib-array |
| store or index | encode the term (nest it as RDF-star's triple term is nested); match a pattern holding a sequence with variables by fetching with that position open and matching elements afterwards; keep it away from fast paths that do not know it (rdf-stores' `matchBindings`) | comunica-array's `QuerySourceRdfJs`, jena-array's solvers, oxigraph-array's `EncodedTerm::Sequence` and spareval's `TupleSelector::Sequence`/`SequencePosition` |
| query | a collection in a pattern, template or update is a term; variables inside bind element by element; position patterns `((?e))[i]`, `[?i]`, `[*]`; ordering after literals and triple terms, element-wise; `isSEQ`, `SEQLEN`, `SEQ`, `expr[i]`; `STR()` spelling | jena-array, comunica-array, traqula-array |
| results | SPARQL JSON `{"type": "seq", "value": [ … ]}`, XML `<seq>`, CSV one quoted cell, TSV the Turtle spelling; readers of those | comunica-array serializers, sparqljson-parse-array, sparqlxml-parse-array, rdflib-array |
| validation | ShEx-array's Collection shape expression `((shapeExpr))[min, max]`; SHACL-array once defined | shex.js-array, PyShEx-array, jena-array's ShEx |
| bindings | the term in every language binding (Python, WASM) | oxigraph-array (`pyoxigraph.Sequence`, `oxigraph.sequence()`) |

Remove the code dedicated to ladders and containers (`CommonIRIs.FIRST/REST/NIL`, list builders,
`rdf:li` counters); `rdf:first`, `rdf:rest`, `rdf:nil` and `rdf:_n` stay ordinary IRIs with no
special handling.

## 2. Create the fork

```bash
gh repo fork <owner>/<repo> --org rdf-array --fork-name <project>-array --default-branch-only --clone=false
git clone git@github.com:rdf-array/<project>-array.git ~/checkouts/rdf-array/<project>-array
cd ~/checkouts/rdf-array/<project>-array
git remote add upstream https://github.com/<owner>/<repo>.git
git checkout -b rdf-sequences <upstream tag or commit the fork is based on>
```

Conventions: the checkout is `~/checkouts/rdf-array/<project>-array`; `origin` is the fork and
`upstream` the original (three early forks have them the other way round, so check `git remote -v`
before pushing); the branch is `rdf-sequences`, made the default branch after the first push:

```bash
git push -u origin rdf-sequences
gh repo edit rdf-array/<project>-array --default-branch rdf-sequences --description "rdf-array: <one line on what the fork does>"
```

Record the base version (tag or commit) in the notes; the fork is rebased on it, never merged
forward silently.

## 3. Banner and icon

Every fork's README opens with the banner, above the original README unchanged:

```markdown
<img src=".github/rdf-array-logo.png" alt="[<project>]" width="96" align="right">

# <project>-array: <project> for rdf-array

**rdf-array** fork of [<project>](<upstream url>): <what the term changes here, in two or three
sentences, naming the API the fork adds or the syntax it reads>. Part of the
[rdf-array](https://github.com/rdf-array/rdf-array) organisation; notes in doc/rdf-array.md.
```

The icon puts the original's avatar between `[` and `]`. Copy any fork's `.github/rdf-array-logo.svg`
as the template and replace the base64 PNG inside `xlink:href="data:image/png;base64,…"` with the
upstream owner's avatar, then rasterize:

```bash
curl -sL "$(gh api users/<owner> --jq .avatar_url)" -o /tmp/avatar.png
python3 - <<'EOF'
import base64, re
tpl = open('../types-array/.github/rdf-array-logo.svg').read()
png = base64.b64encode(open('/tmp/avatar.png', 'rb').read()).decode()
open('.github/rdf-array-logo.svg', 'w').write(re.sub(r'(base64,)[^"]+', lambda m: m.group(1) + png, tpl, count=1))
EOF
qlmanage -t -s 512 -o /tmp .github/rdf-array-logo.svg && mv /tmp/rdf-array-logo.svg.png .github/rdf-array-logo.png
```

## 4. Implement, layer by layer

Work through the closure of §1 in dependency order (data model, then string spelling, then
parsers, then the rest), building and testing each dependency fork before the dependent one picks
it up. For each layer follow the existing fork of the same ecosystem (its `doc/rdf-array.md` lists
the files it touched) and the semantics in rdf-array.md; where the project forces a decision the
documents do not make, take it, note it under "Decisions" in the notes, and, if other
implementations face the same choice, raise it as an issue (§8).

Tests are transformed by the `array-tests` skill as the implementation goes, never afterwards.

## 5. Pin dependency forks

- **npm with yarn 1** (comunica, traqula): yarn runs no `prepare` for a git dependency, so a fork
  commits its compiled output (`dist/`, `main`/`types`/`typings` pointing into it) on
  `rdf-sequences`; root `resolutions` reach nested dependencies, but a direct dependency must name
  the git URL itself (`"n3": "github:rdf-array/N3.js-array#rdf-sequences"`); the lock pins a
  commit, so after a fork gains commits run `yarn upgrade <pkg>` in the dependent, and because yarn
  keeps an installed folder whose version did not change, also `rm -rf node_modules/<pkg>`, then
  `yarn install --check-files`; a stale cache entry needs `yarn cache clean <pkg>`. Never run two
  yarn installs at once. `@rdfjs/types` depends on `@types/node: *`, so pin `@types/node` in
  `resolutions` when an upgrade drags in a new major.
- **npm** (shex.js, jsonld.js): `overrides` for nested forks, git URLs for direct ones;
  `npm update <pkg>` to move a pinned commit.
- **Components.js** (comunica's dependency injection) reads its configuration lists as ladders:
  keep the vanilla JSON-LD parser for it (a direct dependency of the parse actor only, not a root
  resolution).
- **Python with uv**: `[tool.uv.sources]` pointing at the forks' `rdf-sequences` branches,
  `prerelease = "allow"`; one shared editable venv for the stack (`uv pip install -e …`).
- **Java (Jena)**: in-tree; Maven may be unavailable, so the notes carry the `javac`/`java`
  incantations.
- **Rust**: `[patch.crates-io]` or path/git dependencies on the forked crates. Oxigraph's crates are one
  workspace, so oxigraph-array needed none; a dependent such as rudof patches `oxrdf`, `oxttl`, … to
  oxigraph-array's `rdf-sequences` branch.

## 6. Notes, commits, publication

`doc/rdf-array.md` in the fork has: what rdf-array is in one paragraph and the stack table
(dependencies, their forks, base versions); setting up; what a sequence does here; what changed
(files, modules); tests (added, flagged with reasons, suites run and their numbers, suites not
run); decisions taken; not done. Link each decision or gap that has an issue (§8) to it. Commit messages start `rdf-array:` (older ones `RDF-:`) and end
with the attribution trailer the session uses; the first commit's body says what the fork changes
and what it pins. Pre-commit hooks may run lint, build and full test suites (comunica ~12 min,
traqula's `spec:all` needs the network); run them, and commit with `-n` only when the hook was
interrupted after the checks passed.

A fork with a site gets a `pages.yml` modelled on shex.js-array's or jsonld.js-array's (build, stage
`_site`, `actions/configure-pages` with `enablement: true`, `upload-pages-artifact`, `deploy-pages`);
enable Pages with `gh api --method POST repos/rdf-array/<fork>/pages -f build_type=workflow` after
the default branch is set, so the `github-pages` environment allows it, and point the repository's
homepage at the site.

## 7. Register the fork

Add it to this repository's [repos.json](../../../repos.json) (the `repos-manifest` skill: its kind,
language, upstream, description, anchor and `deps`, `"stack": true` if a stack is named for it, the
target marked done if it was one), run `python3 tools/manifest-check.py`, add it to the
implementations table of rdf-array.md and to the memory note the session keeps, and set the GitHub
description. Name a new stack in the README's short stack list.

## 8. Issues

All rdf-array issues live in [rdf-array/rdf-array](https://github.com/rdf-array/rdf-array/issues).
GitHub turns issues off on forks, and every `-array` fork keeps them off; only this repository
and the three `*-contrib` repositories have them on. Never file rdf-array issues on an upstream
project's tracker.

1. **Search first**, across the organisation, and comment on an existing issue rather than open a
   duplicate; the comment says what this fork does about it (accepts, rejects, not done, where in
   the code):

   ```bash
   gh issue list -R rdf-array/rdf-array --state all --limit 100
   gh search issues --owner rdf-array --state open "<words>"
   ```

2. **Cross-repo**: a question several implementations or suites face, a disagreement between
   implementations, a gap in a suite that every port meets, or a process problem across forks.
   Label it `cross-repo`. If it is a decision the model or a syntax has not made, also label it
   `open-question` and add a bullet with the link to the open questions of rdf-array.md
   (then regenerate `docs/rdf-array.html`). State what each implementation does today, and what deciding
   would change (tests to add to a `*-contrib`, implementations to fix).
3. **Repo-specific**: a gap or bug in one repository. Title it `<repo>: …` (as `shex.js-array: …`)
   and label it `repo`; repos.html files it under that repository by the prefix.
   **Spec**: a question about rdf-array itself, the data model or an -array specification
   (Turtle-array, ShEx-array, SHACL-array…), rather than an implementation: label it `spec`.
   A cross-repo issue may open its body with `Repos: a, b`, which repos.html also files it under.
4. Name the issue in the fork's `doc/rdf-array.md` (Decisions, Not done) and, when a commit settles
   it, in the commit message (`rdf-array/rdf-array#9`).

## Pitfalls met before

- zsh: quote `--include='*.ts'`, use `bash <<'EOF'` for `set -- $pair`, `status` is read-only, `=cmd`
  expands at the start of a word.
- The safety classifier refuses `rm -rf` with shell variables (write literal absolute paths) and
  git operations that delete remote branches (leave those to the user).
- A fork's tests may need `TZ=UTC`; coverage thresholds of 100% mean every new branch needs a test.
- `rdf-isomorphic` does not canonicalize blank nodes inside sequences, and vanilla `rdf-string`
  spells a sequence as `undefined`, so an isomorphism assertion passes vacuously unless the test
  dependencies pin rdf-string-array.
- Pushing to the wrong remote once created a stray branch on an upstream repository; check
  `git remote -v`.
