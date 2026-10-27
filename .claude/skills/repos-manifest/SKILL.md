---
name: repos-manifest
description: Keep repos.json, the rdf-array organisation's manifest of repositories, stacks, dependency edges and targets, in step with GitHub and with the forks' build files — add a new repository with its kind, language, upstream, description, anchor and deps, mark a stack root or a finished target, run tools/manifest-check.py, and keep the README's short stack list, rdf-array.md's implementations table and repos.html aligned. Also the issue conventions (title prefix, repo/cross-repo/spec labels) that repos.html files issues by. Use after creating, renaming, forking or deleting an rdf-array repository, when a fork pins a new fork, or when filing an issue.
---

# Maintaining repos.json

[repos.json](../../../management/repos.json) is the organisation's manifest. [repos.html](../../../management/repos.html),
published at <https://rdf-array.github.io/rdf-array/management/repos.html>, renders it with the open issues.
The README keeps only a short hand-written list of the stacks, deep-linked into that page. GitHub
cannot run the page's script in a README, which is why the full list is not there.

## Terms

- **repo**: any repository of the organisation, fork or not (the contrib repositories and this one
  are not forks).
- **stack**: a repository marked `"stack": true`, the project a group of forks was made for, together
  with every repository its runtime `deps` reach. A dependency shared by several stacks belongs to
  each; repos.html lists it under each and gives it its anchor at the first.
- **target**: a project in `targets`, not forked yet (`"done": true` once it is). The assessment
  stays in [targets.md](../../../management/targets.md).

## An entry

```json
{
  "name": "traqula-array",
  "short": "traqula",
  "anchor": "traqula",
  "kind": "implementation",
  "language": "JavaScript",
  "upstream": "comunica/traqula",
  "description": "the SPARQL parser, generator and algebra, with a collection as one sequence term.",
  "deps": [
    { "repo": "rdf-data-factory-array" },
    { "repo": "types-array" },
    { "repo": "rdf-tests-contrib", "scope": "test", "note": "cloned by a script whose URL is built from a variable" }
  ]
}
```

- **kind**: `implementation`, `test-suite` (a W3C or community suite fork), `contrib` (with
  `contribOf`, the suite fork it accompanies), `tool` (rdf-test-suite-array) or `meta` (this
  repository, `.github`).
- **short** and **anchor**: the name without `-array`; the anchor as GitHub would make a heading's
  (lower case, punctuation other than `-` and `_` dropped: `n3js`, `shexjs`, `jsonldjs`). Never
  reuse or change an anchor. Issues and documents link to `repos.html#<anchor>`, and the old
  `README.md#<anchor>` links map onto it.
- **upstream**: `owner/repo`, as GitHub names the fork's parent (manifest-check notes a mismatch);
  **upstreamFrom** when the upstream is itself a fork of another.
- **description**: what the repository does for rdf-array, in the present tense, inline Markdown
  (code spans, links; a relative `x.md` link points at this repository on GitHub). A site or
  playground goes here as a link.
- **deps**: the rdf-array repositories this one pins, `"scope": "test"` for test-only ones (a
  devDependency, a test-suite submodule, a vendored suite copy with its `*.commit` file, a suite a
  fetch script clones). Runtime deps make the stacks; test deps show as "Runs:" on a stack. An edge
  no build file shows needs a `note` saying where it comes from.
- **stack**: `true` on the repository a stack is named for. A dependency that becomes a target in its
  own right just gets `"stack": true`; nothing else moves.
- **targets**: `{ "anchor", "done", "text" }`, in the recommended order, `text` in inline Markdown.

## When a repository changes

1. **Created or forked:**
   - Add its entry in its language's place in the list. Order is display order: a stack's members
     are shown in the order the file lists them.
   - Add the `deps` its build files show, and mark the target done if it was one.
   - Set its GitHub description (`gh repo edit rdf-array/<name> --description "rdf-array: …"`) and
     its default branch.
   - A new stack also gets a line in the README's stack list, deep-linked to `repos.html#<anchor>`,
     and a row in rdf-array.md's implementations table (regenerate `docs/rdf-array.html`).
   - Leave issues off on a fork (`fork-array` §8).
2. **Pins a new fork:** add the edge. `manifest-check.py` reports any edge the build files show that
   repos.json lacks.
3. **Renamed:** GitHub redirects the old name, but update `name` (keep the anchor), every link in this
   repository and in the forks (`grep -rn "rdf-array/<old>" ~/checkouts/rdf-array/*/README.md
   ~/checkouts/rdf-array/*/doc/rdf-array.md`), the issue titles that use the old prefix, the local
   checkout directory and its `origin`.
4. **Deleted:** remove the entry and the edges to it; mention the deletion in the commit message.
5. Run the check, then commit as `rdf-array: manifest: <what changed>` and push.

## The check

```bash
python3 tools/manifest-check.py              # repos.json, GitHub and the build files of ~/checkouts/rdf-array/*
python3 tools/manifest-check.py --offline    # repos.json alone and the repos.html#… links (the Pages workflow runs this)
python3 tools/manifest-check.py --edges      # also print each checkout's derived edges
python3 tools/manifest-check.py --upstreams  # print the upstream of each repository missing from repos.json
```

It needs `gh` logged in with the `read:org` scope for the GitHub part, and the checkouts beside this
one (`--root DIR` otherwise; a missing checkout is noted, not an error). Errors:
- duplicate names or anchors, unknown kinds or repositories, a runtime dependency cycle;
- a `repos.html#…` link in README.md, management/targets.md or docs/html-index.html that resolves to nothing;
- a repository missing from repos.json or extra in it;
- an edge a build file shows that repos.json lacks.

Notes:
- missing or old-style GitHub descriptions;
- an upstream that differs from GitHub's fork parent;
- a declared edge no build file shows, unless the edge has a `note`.

## Issues

All issues live in rdf-array/rdf-array; repos.html files them as follows:

- **`<repo>: …` title + label `repo`**: about one repository, listed under it. The prefix is the full
  repository name, case as on GitHub. The page flags a prefixed issue without the label, and a
  `repo` label without a valid prefix.
- **label `cross-repo`**: spans repositories. A body that opens with `Repos: a, b` also lists the
  issue under those repositories. These issues are in their own section.
- **label `spec`**: about rdf-array itself: the data model, Turtle-array, SPARQL-array, ShEx-array,
  SHACL-array. These issues are in their own section.
- **`rdf-array: …`**: about this repository (its documents, tools, conventions), listed under it in
  the Meta section.
- Anything else shows as **Unfiled**, except the issue numbers in repos.json's `issues.ignore`
  (#1, the meta-information about the issues themselves), which the page leaves out.
- `open-question`, `bug` and `enhancement` are added as they apply.

## Other lists to keep in step

- The README's stack list (one line per stack) and its documents table.
- rdf-array.md's implementations table (one row per stack), and `targets.md` when a target becomes a
  fork.
- `docs/html-index.html` and the `pages.yml` check loop when a rendered document is added.
- The fork's own README banner and `doc/rdf-array.md` stack table when it gains a dependency fork.
