---
name: readme-manifest
description: Keep this repository's README manifest of the rdf-array organisation's repositories in step with GitHub — add a new fork under its language heading (a primary project as a heading, a dependency quoted under it) with its upstream and anchor, tick it off the not-yet-forked list, elide the -array suffix, keep descriptions and the implementations table in rdf-array.md aligned, and run tools/manifest-check.py to find repositories missing from the README or listed without existing. Use after creating, renaming, forking or deleting an rdf-array repository.
---

# Maintaining the README manifest

The README's "Repositories" section is the organisation's manifest: every repository, grouped by
language, with the project each stack was forked for first and the dependencies forked with it
nested under it. `tools/manifest-check.py` compares it with GitHub.

## The rules of the list

- **Layout.** `## Repositories` opens with a jump line to its sections, then `### Test suites` first,
  one `###` heading per language (Java, JavaScript, Python, Rust, then any new one such as C++),
  and `### Not yet forked` last. Under a language, one `####` heading per *primary* project, the one
  the stack was forked for (jena, shex.js, comunica, jsonld.js, PyShEx, oxigraph, rudof); the
  heading text is the elided name, linked to the fork.
- **Dependencies** that had to learn the term for a primary project are a list inside a blockquote
  (`> - …`) under its paragraph: GitHub renders blockquotes in a muted grey, which is as close to
  grey styling as its Markdown allows (no CSS, no `style`). A dependency shared by several stacks
  is listed once, under the first stack that used it, with the others named in parentheses: "(also
  comunica and jsonld.js)". A primary project whose dependencies are forks listed elsewhere links
  them (`> - [oxigraph](#oxigraph), above.`); one without forked dependencies says so: "No forked
  dependencies."
- **Anchors.** Every repository can be linked as `README.md#<anchor>`, the anchor being its elided
  name as GitHub makes heading anchors: lower case, spaces to hyphens, punctuation other than `-`
  and `_` dropped (`#jena`, `#n3js`, `#shexjsg`, `#rdf-tests-contrib`). Headings get theirs from
  GitHub; a dependency or a contrib repository gets an explicit `<a id="…"></a>` at the start of its
  item, which GitHub keeps (as `user-content-…`, resolved by its scripts). Never reuse an anchor.
- **Names.** The fork's name is shown without its `-array` suffix, linked to the fork; the upstream
  follows as `owner/repo`, linked: "Fork of [owner/repo](…): …" under a heading, in parentheses in a
  dependency item. When the fork's upstream is itself a fork, name the original too: "([ericprud/x](…),
  from [linkml/x](…))".
- **Description.** What the fork does for rdf-array, in the present tense, naming the term or the
  construct (`Sequence`, `( … )`, `@list`, the Collection shape expression) rather than the
  project's general purpose; a site or playground URL when there is one.
- **Ordering.** Within a stack: the data model and term libraries, then parsers and serializers,
  then query, then results; or simply the order of the stack table in the fork's
  `doc/rdf-array.md`.
- **Test suites**: each W3C fork has a `####` heading, elided like the others, with its `*-contrib`
  sibling quoted under it by its full name (contrib repositories are new, use `main`, and are not
  forks).
- **Not yet forked**: the targets of [targets.md](../../../targets.md) as a task list in the
  recommended order, each `- [ ] <a id="…"></a>**Name**` with its upstream link, language, one line
  of what it is, impact and utility, and a link to its assessment section in targets.md. When a
  target becomes a fork, its item turns into `- [x] … [name](#anchor), <date>.` and the fork gets
  its heading under its language.
- **This repository** is the host and is not listed; the documents table at the top covers it.
- **Check the rendering** with GitHub's own renderer when the layout changes:
  `jq -n --rawfile t README.md '{text:$t, mode:"gfm", context:"rdf-array/rdf-array"}' | gh api markdown --input -`
  shows which anchors, checkboxes and blockquotes survive.

## An entry

```markdown
#### [comunica](https://github.com/rdf-array/comunica-array)

Fork of [comunica/comunica](https://github.com/comunica/comunica): the SPARQL-array engine:
sequence patterns with variables, ordering, CONSTRUCT, the result formats, Turtle, JSON-LD and
RDF/XML sources, remote endpoints.

> - <a id="traqula"></a>[traqula](https://github.com/rdf-array/traqula-array) ([comunica/traqula](https://github.com/comunica/traqula)) —
>   the SPARQL parser, generator and algebra, with a collection as one sequence term.
```

## When a repository changes

1. **Created or forked:** set its GitHub description (`gh repo edit rdf-array/<name> --description
   "rdf-array: …"`) and default branch; add the README entry, with its anchor, and tick its
   target in "Not yet forked" if it was one; add the fork to the implementations
   table in `rdf-array.md` (and regenerate `rdf-array.html`, which the Pages workflow checks); if it
   has a site, the homepage URL. Add it to the session's memory note of the forks. Leave issues off
   on a fork (GitHub's default): its issues go to rdf-array/rdf-array (`fork-array` §8).
2. **Renamed:** GitHub redirects the old name, but update every link in this repository and in the
   forks that point at it (`grep -rn "rdf-array/<old>" ~/checkouts/rdf-array/*/README.md
   ~/checkouts/rdf-array/*/doc/rdf-array.md`), the local checkout directory and its `origin`.
3. **Deleted:** remove the entry; mention the deletion in the commit message.
4. Run the check, then commit as `rdf-array: manifest: <what changed>` and push.

## The check

```bash
python3 tools/manifest-check.py              # repositories missing from or extra in the README
python3 tools/manifest-check.py --upstreams  # also prints each missing one's upstream, for the entry
```

It lists the organisation's repositories with `gh repo list rdf-array`, reads every
`https://github.com/rdf-array/<name>` link in the README, and reports repositories not linked,
links to repositories that do not exist, repositories without a GitHub description, and
descriptions still carrying the old `RDF-:` prefix. It exits non-zero on the first two kinds, so it
can guard a commit. It needs `gh` logged in with the `read:org` scope.

## Other lists to keep in step

- `rdf-array.md`'s implementations table (one row per stack) and `targets.md` when a target
  becomes a fork (move it from the table to "done").
- `html-index.html` and the `pages.yml` check loop when a rendered document is added.
- The fork's own README banner and `doc/rdf-array.md` stack table when it gains a dependency fork.
