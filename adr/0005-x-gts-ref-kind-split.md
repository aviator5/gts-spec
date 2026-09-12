# ADR-0005: Split `x-gts-ref` into `x-gts-type-ref` and `x-gts-instance-ref`

- **Status:** Accepted
- **Date:** 2026-09-02
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

### What `x-gts-ref` does today

`x-gts-ref` (README §9.6) annotates a JSON Schema string field to declare that its value is a GTS identifier rather than an arbitrary string. The keyword value — the **operand** — is either a literal GTS prefix (`gts.x.core.events.topic.v1~`, optionally with a wildcard) or a JSON Pointer into the schema document (`/$id`, `/properties/id`). A candidate value is accepted when it is a syntactically valid GTS identifier (OP#1) that is *rooted at* the resolved operand.

### The defect: the keyword is kind-blind

GTS has two kinds of identifier: a **GTS Type Identifier** ends with `~`, a **GTS Instance Identifier** does not (Terminology, §2.2). Rooted matching alone does not distinguish them, so one `x-gts-ref` constraint accepts all of:

- the operand type itself — `gts.x.infra.compute.vm_state.v1~`
- types derived from it — `gts.x.infra.compute.vm_state.v1~vendor.pkg._.state.v1~`
- instances rooted at it — `gts.x.infra.compute.vm_state.v1~x.infra._.running.v1`

A schema author cannot say which of these a field is supposed to hold. The VM `powerState` field is the canonical case:

```json
{
  "type": "string",
  "x-gts-ref": "gts.x.infra.compute.vm_state.v1~"
}
```

The intended value is an instance such as `gts.x.infra.compute.vm_state.v1~x.infra._.running.v1`, yet the bare Type Identifier `gts.x.infra.compute.vm_state.v1~` validates just as well. The same ambiguity affects the `topicRef` trait in `examples/events` and the capability references in `examples/modules`, and it is systemic rather than incidental: every reference field in the specification's own examples is affected.

The pointer operand `/$id` is worse, because it is used for both roles in the same corpus. In `examples/modules/types/gts.x.core.modules.module.v1~.schema.json` the `type` field carries `x-gts-ref: "/$id"` and holds a **Type** Identifier, while the sibling `id` field of `gts.x.core.modules.capability.v1~.schema.json` carries the identical annotation and holds an **Instance** Identifier. The two are indistinguishable to a validator.

### Why wildcards cannot close the gap

The obvious workaround — express the kind in the operand — does not work. A chain-suffix wildcard such as `gts.x.infra.compute.vm_state.v1~*` matches the type root, derived types, and instances alike, because `*` is a matching token over identifier text and not a kind selector. The trailing `~` that carries the kind sits at the *end* of the candidate, which is exactly the part a suffix wildcard leaves unconstrained. Kind must therefore be part of the keyword contract, not of the operand string.

### The operand language is also under-specified

Reviewing the keyword surfaced defects that are independent of kind but cannot be left in place once the keyword is rewritten:

- **`/$id` is documented as equality** — "field value must equal the current schema's `$id`" — while deployed implementations and the conformance suite treat it as a root (`tests/test_refimpl_x_gts_ref.py` accepts an instance identifier rooted at the schema's own type).
- **Three spellings compete.** The normative list gives `gts.*` and `/$id`; the implementation notes add `./$id` and `./description`; the TypeSpec examples use `"/gts.x.infra.compute.vm_state.v1~"`, which under any pointer reading does not resolve.
- **Pointer targets are inconsistent.** `tests/test_refimpl_x_gts_ref.py:378` points at a scalar (`/properties/some/const`), while `tests/test_refimpl_x_gts_ref.py:187` points at another annotated subschema (`/properties/id`) — i.e. operand indirection, with no defined termination, cycle, or multi-branch behaviour.
- **MINOR-version matching has no owner.** §4.2 explicitly declines to define the relationship between `v1~` and `v1.0~`/`v1.1~`; §10 defines it for wildcard collection but contradicts its own examples for `v1~*`. A conformance-test author cannot determine from the current text whether a literal operand `…v1~` matches a candidate rooted at `…v1.1~`.
- **Placement contradicts §11.0.** §11.0 states that GTS's `x-gts-*` keywords "are type-level annotations that MUST appear at the document top level". `x-gts-ref` has always been field-level, so §11.0 was already wrong; a conforming implementation could reject every intended use.

### What this ADR must decide

1. How a schema author states the required kind of a reference field.
2. What "rooted at the operand" means once kind is enforced — including MINOR versions, wildcards, and the chained-grammar boundary.
3. How an operand resolves, and in particular against what a JSON Pointer operand resolves when the constraint is reached through `$ref`/`allOf` from a base type.
4. Whether the keywords are annotations or assertions.
5. Whether the legacy keyword survives as a deprecated alias.

## Decision Drivers

- **Author intent must be expressible.** A reference field is either a type slot or an instance slot; the schema must say which.
- **Validators must not guess.** Kind determination must follow from the parsed canonical identifier, not from heuristics or registry lookups.
- **Every rule must be implementable against a concrete artifact.** A rule that requires materializing an abstract "merged schema" is not implementable: JSON Schema evaluation produces no canonical merged document, and colliding `allOf` branches, conditionals, recursive references, nested `$id`s and `$dynamicRef` make any flattening non-canonical.
- **Reuse the existing operand language where it is sound.** Literal operands, `/$id`, wildcards, rooted matching and optional registry resolution all work; the kind dimension is what is missing, and the under-specified corners are what must be closed.
- **Chain-boundary and version correctness.** Matching must run over parsed GTS chains, and the MINOR rule must be stated where the keyword is defined rather than delegated to sections that disagree.
- **Fail fast at registration.** A malformed or unresolvable constraint is a defect in the schema and should surface when the Type Schema is registered — not on the first instance that happens to exercise the field.
- **Compose with the host dialect.** The keywords must behave as assertions at their schema location so that `anyOf`, `oneOf`, `not` and conditionals mean what they appear to mean.
- **No silent behavior change.** The specification is pre-1.0, but a keyword that quietly changes meaning is worse than one that is removed loudly.
- **Keep emitters simple.** TypeSpec (`@extension`) and YAML forms carry the keyword as a plain string-valued annotation; that shape should survive.

## Considered Options

- Option 1 — Keep `x-gts-ref`, express kind in the operand (wildcards, `const`)
- Option 2 — Keep `x-gts-ref`, add a sibling kind modifier keyword
- Option 3 — Keep `x-gts-ref`, make its value an object (`{"ref": …, "kind": …}`)
- Option 4 — Split into `x-gts-type-ref` and `x-gts-instance-ref` *(chosen)*
  - Option 4a — Keep `x-gts-ref` as a deprecated kind-blind alias
  - Option 4b — Clean break: reject `x-gts-ref` from 0.14 *(chosen)*

Operand resolution is decided separately, because the kind split does not by itself determine it:

- Option R1 — Fully lexical: every operand, `/$id` included, resolves in the resource that authored the keyword
- Option R2 — Fully dynamic: all operands resolve against a merged "effective validation schema"
- Option R3 — Hybrid: `/$id` is a reserved dynamic token; all other pointers are lexical *(chosen)*

Four consequential sub-decisions fall out of the chosen options and are recorded below: **B** (`/$id` is rooted resolution, not equality), **C** (pointer targets are terminal strings), **D** (operand spellings removed), **E** (assertion semantics and the deferred `Valid(S)` repair).

### Option 1 — Express kind in the operand

Leave the keyword alone and ask authors to encode the kind in the operand string, e.g. a wildcard shaped to exclude the trailing `~`, or a standard JSON Schema `const` next to `x-gts-ref` to pin one exact value.

This fails for the reason given above: a chain-suffix wildcard cannot exclude the type root, because the discriminating character is the last one in the candidate. `const` does work, but only for the degenerate case of a single permitted value — it cannot express "any instance of this type or of any of its descendants", which is what every real reference field needs.

### Option 2 — Sibling kind modifier keyword

Keep `x-gts-ref` and add `x-gts-ref-kind: "type" | "instance"` alongside it.

Two keywords must then be kept in sync at every reference site, and the specification must define what an absent `x-gts-ref-kind` means. Any default reintroduces exactly the ambiguity being removed, and "no default — always required" is the same amount of author churn as the split with an extra keyword to validate, place, and document.

### Option 3 — Object-valued `x-gts-ref`

Change the keyword's value from a string to an object: `{"ref": "gts.x…v1~", "kind": "instance"}`. Like Option 4b, this can be a single clean break rather than a dual-shape transition — the comparison below assumes it is.

It is still breaking, so it buys no migration relief, and it costs the plain-string annotation form that TypeSpec `@extension` and YAML rely on. The keyword's own value then needs a meta-schema, and dual acceptance still has to be expressed somehow — either by a third `kind` value, which is the ambiguity again under a nicer name, or by `anyOf`, which is what Option 4 already uses.

### Option 4 — Two keywords

Replace `x-gts-ref` with `x-gts-type-ref` and `x-gts-instance-ref`. Both retain the operand language and rooted matching; each adds a kind assertion on the candidate. A field that genuinely accepts either kind uses standard JSON Schema `anyOf` with one branch per keyword — which also documents that dual acceptance was deliberate.

### Option R1 — Fully lexical operands

Every operand resolves in the schema resource that authored the keyword. `/$id` in base `A~` always yields `A~`, whichever leaf is being validated.

Well-defined and cheap, but the inherited constraint is then the loosest one at every leaf. To reject an instance of a sibling branch, each leaf must restate the constraint with its own literal operand — the per-leaf boilerplate that declaring the constraint once on the base exists to avoid — and a leaf that forgets **fails open**: it silently accepts sibling instances with no error anywhere.

### Option R2 — Fully dynamic operands

Every operand, including `/properties/…`, resolves against the "effective validation schema": the leaf after resolving authored `$ref`/`allOf` composition.

This is not implementable as stated. JSON Schema evaluation yields no canonical merged document; given `{"$id": "B~", "allOf": [{"$ref": "A~"}, {"properties": {…}}]}` there is no defined JSON object for `/properties/type` to address — it could mean the raw leaf, the referenced resource, one overlay, or an invented flattening. Colliding branches, conditionals, recursive references, nested `$id`s and `$dynamicRef` make any such flattening non-canonical. Specifying it would require inventing a whole virtual-schema construction with conflict rules, for the sake of one keyword.

### Option R3 — Hybrid *(chosen)*

`/$id` is a **reserved dynamic token**: it resolves to the `$id` of the leaf Type Schema selected for the validation operation. That is a single string lookup on one identified schema — no traversal, nothing to flatten. Every other pointer is an ordinary lexical RFC 6901 pointer into the resource that authored it.

This delivers the polymorphic self-reference that motivated dynamic resolution, at the cost of one documented irregularity, and leaves no undefined document to specify.

## Decision Outcome

Chosen: **Option 4 with the clean break of Option 4b, and Option R3 for operand resolution.**

The kind becomes a property of the keyword — where a validator cannot ignore it and an author cannot forget it — while the operand language is kept, tightened, and made fully resolvable against concrete artifacts.

This is a **BREAKING** change introduced in specification version 0.14. Normative text: README §9.6.

### Keyword semantics

Both keywords take a string operand. Three operand forms are distinguished by explicit parsing precedence:

1. exactly `/$id` — the reserved dynamic token (see below);
2. any other string beginning `/` — a lexical JSON Pointer;
3. a string beginning `gts.` — a literal, optionally containing a wildcard.

Matching proceeds in two stages. **Stage 1**: the candidate must be a valid GTS identifier under the *chained* grammar (§2.1 and the EBNF of §2.3 govern) whose parsed type chain begins with the resolved operand, at a chain boundary, honoring the MINOR rule below. **Stage 2**: the candidate's kind must equal the kind the keyword selects — a Type Identifier ends with `~`, an Instance Identifier does not. Neither stage consults a registry.

For a resolved operand `gts.a.b._.c.v1~`:

| Keyword | Accepted | Rejected |
|---|---|---|
| `x-gts-type-ref` | that Type Identifier and Type Identifiers derived from it | every Instance Identifier |
| `x-gts-instance-ref` | Instance Identifiers rooted at that type — well-known or combined-anonymous (`~<UUID>`), directly or through derived types | the type itself and every derived type |

A wildcard operand denotes the **subset of Type Identifiers** the pattern matches; strings it also matches that are not Type Identifiers are simply not type roots. A candidate matches when its type chain begins with at least one member of that subset, and implementations need not enumerate it. A trailing chain wildcard on a type root is therefore redundant with the bare root. Validity is stated as a non-emptiness condition rather than a syntactic ban: a wildcard-free operand must itself be a Type Identifier, and a wildcard operand is valid when its Type-Identifier subset can be non-empty. This avoids a dedicated type-root-pattern grammar and gives a defensible answer for patterns such as `gts.x.core.events.topic.v1~x.core._.default.v*`, which match both a derived Type and an Instance: the operand denotes the Type matches, and the rest are ignored.

The MINOR rule is stated in §9.6.3 rather than delegated: an operand carrying no MINOR is rooted at any MINOR of that MAJOR; an operand carrying a MINOR is rooted at that MINOR only. This is a matching relation only — it does not make `v1~` and `v1.1~` the same registered type identity, and §4.2 is unaffected.

The resolved operand MUST be able to denote a Type Identifier: a wildcard-free operand must itself be one, and a wildcard operand is valid when its Type-Identifier subset can be non-empty. One that resolves to an Instance Identifier, to a pattern whose Type-Identifier subset is necessarily empty, or to a non-identifier makes the schema invalid.

Dual acceptance is written with `anyOf`, one branch per keyword. Neither keyword narrows to a single exact identifier; a field that must hold one specific value adds `const`.

### Sub-decision A — `/$id` is a reserved dynamic token; other pointers are lexical (Option R3)

`/$id` resolves to the `$id` of the leaf GTS Type Schema selected for the validation operation, with `gts://` removed. Every other pointer resolves per RFC 6901 against the root of the schema **resource** in which the keyword was authored — resource boundaries following the declared dialect, including embedded resources established by a nested `$id`, so "the authoring resource" is not simply "the physical file".

The consequence is **dynamic rebinding** for `/$id` only:

```text
base   gts.a.b._.c.v1~            declares:  x-gts-instance-ref: "/$id"
leaf   gts.a.b._.c.v1~d.e._.f.v1~     body:  allOf [ $ref gts://gts.a.b._.c.v1~, … ]

accepted:   gts.a.b._.c.v1~d.e._.f.v1~x.y._.z.v1
rejected:   gts.a.b._.c.v1~d.e._.q.v1~x.y._.z.v1     (sibling branch)
```

This is the behavior the `id` / `type` self-reference pattern has always wanted: the base declares once that the field holds an instance of *itself*, and each leaf tightens that to *this leaf*. An author who wants the static behavior writes the literal operand.

Note that `/$id` is deliberately a reserved token rather than a pointer that happens to be treated specially: `/$id/foo` is an ordinary lexical pointer. The alternative — a distinct non-pointer token such as `$self` — is syntactically more honest but churns every existing `/$id` site for no semantic gain, so the wart is accepted and documented.

**Reachability is orthogonal.** A reference keyword is evaluated only where the dialect evaluates its schema location. The chained `$id` establishes derivation and OP#12 compatibility but does not import ancestor schema bodies (ADR-0001), so a derived Type Schema that neither `$ref`s nor restates its base inherits no reference constraint from it and there is nothing to rebind. Synthesizing an implicit `allOf` over the chain just for this keyword would contradict ADR-0001.

### Sub-decision B — `/$id` is rooted resolution, not an equality mode

§9.6 currently describes `/$id` as a self-reference whose "field value must equal the current schema's `$id`". That conflicts with the rest of the keyword and with deployed behavior, where an instance identifier rooted at the schema's own type is accepted, not just the type string itself. `/$id` is therefore an operand like any other, feeding the same rooted matching. Equality, where genuinely wanted, is expressed with `const`.

This is an additional breaking correction, not a clarification: `x-gts-type-ref: "/$id"` accepts strictly more than 0.13's written equality reading, and `x-gts-instance-ref: "/$id"` accepts a disjoint set.

### Sub-decision C — Pointer targets are terminal strings; operand indirection is removed

A lexical pointer MUST resolve to a JSON **string**. That string, with any `gts://` prefix removed, *is* the operand, and it is **terminal**: it must itself be a literal type root or wildcard pattern, and is never reinterpreted as a pointer or as the reserved token. Without the terminal rule a pointer resolving to the string `/properties/b` would silently reintroduce recursion.

This keeps the scalar-target form already exercised by `tests/test_refimpl_x_gts_ref.py:378` (`/properties/some/const`) and removes the operand-indirection form at `tests/test_refimpl_x_gts_ref.py:187` (`/properties/id` pointing at another annotated subschema). Indirection is dropped because it has no defined termination, cycle detection, or behaviour when the target sits under `$ref`, `anyOf`, or several applicable branches — disproportionate machinery whose only benefit is avoiding a duplicated operand. That test must be migrated by restating the operand at the second site.

### Sub-decision D — Operand spellings removed

The `./$id` / `./description` spellings are removed. They appeared in §9.6's implementation notes and in `examples/modules/README.md`, but never in the normative "allowed values" list, and no schema in `examples/` uses them.

`"/gts.x…"` is likewise not a literal operand: under the precedence above it parses as a lexical pointer with a single token `gts.x…`, which does not resolve. The occurrences in the TypeSpec examples are schema defects, corrected to the literal form during migration.

### Sub-decision E — Assertion semantics, and the deferred `Valid(S)` repair

Both keywords are **assertions**, evaluated at their schema location and composing through the applicators of the declared dialect. This is load-bearing for the design: an implementation that scanned for keyword occurrences instead of evaluating branches would enforce both branches of the `anyOf` idiom and reject every value. §9.6 states this explicitly, along with the consequences — a non-string value fails the assertion (no sibling `"type": "string"` is required), and both keywords at one schema location are unsatisfiable by construction and rejected as an invalid schema rather than silently accepted.

This exposes a gap this ADR deliberately does **not** close. §4.3 defines `Valid(S)` as the instances accepted "under the JSON Schema dialect declared by that schema", and §11.0 states that GTS is not a dialect — so on a literal reading these keywords do not affect `Valid(S)` at all, and no OP#8 verdict can depend on them. The repair is to define accepted instances as JSON Schema validation *plus* all applicable GTS instance-assertion keywords, covering OP#8 and OP#12 together.

That belongs in its own ADR: it edits §4.3, the core of the compatibility model, and this ADR is not reviewing the compatibility model. Scoping it here would make ADR-0005 the de-facto owner of §4. The keyword contract stands without it, because §9.6 defines runtime assertion semantics independently; only the OP#8/OP#12 *implications* below are stated conditionally as a result. Note the repair is narrower than it first appears: `x-gts-final`, `x-gts-abstract`, `x-gts-traits-schema` and `x-gts-traits` are Type-Schema and registration constraints rather than assertions over instance payloads, so `Valid(S)` for them is largely unaffected.

### Migration

Every existing `x-gts-ref` occurrence must be migrated **by field intent**. There is no mechanical rewrite: `/$id` is currently used for both type fields and instance fields, so each site must be read. The migration table lives here rather than in the specification, which carries only the resulting normative rules:

| 0.13 | Field holds | 0.14 |
|---|---|---|
| `"x-gts-ref": "gts.a.b._.c.v1~"` | a type or a derived type | `"x-gts-type-ref": "gts.a.b._.c.v1~"` |
| `"x-gts-ref": "gts.a.b._.c.v1~"` | an instance of that type | `"x-gts-instance-ref": "gts.a.b._.c.v1~"` |
| `"x-gts-ref": "gts.*"` | any type | `"x-gts-type-ref": "gts.*"` |
| `"x-gts-ref": "gts.*"` | any instance | `"x-gts-instance-ref": "gts.*"` |
| `"x-gts-ref": "/$id"` | this type or a derived type (`type` discriminator) | `"x-gts-type-ref": "/$id"` |
| `"x-gts-ref": "/$id"` | an instance of this type (`id` of a well-known instance) | `"x-gts-instance-ref": "/$id"` |
| `"x-gts-ref": "/$id"` | an instance of some *other* member of the same family | the literal root, **not** `/$id` — see Sub-decision A |
| `"x-gts-ref": "gts.a.b._.c.v1~*"` | — (redundant trailing chain wildcard) | drop the `*`: rooted matching already admits descendants |
| `"x-gts-ref": "/gts.a.b._.c.v1~"` | — (parses as an unresolvable pointer) | the literal `"gts.a.b._.c.v1~"` under the intended keyword |
| `"x-gts-ref": "./$id"`, `"./description"` | — (`./` spelling removed) | `"/$id"`, or a form-2 pointer such as `"/properties/some/const"` |
| `"x-gts-ref": "/properties/id"` where the target is itself an annotated subschema | — (operand indirection removed) | restate the target's own operand at this site |
| a field that must accept both kinds | either | `anyOf` of the two keywords (§9.6.5) |

Migrating an existing type is **not** uniformly a narrowing — see the OP#8 implication below.

GTS-aware registration and validation operations targeting 0.14 MUST **reject** the legacy `x-gts-ref` keyword rather than ignore it — a schema that still carries it is a schema whose reference constraints are not being enforced, and silence there is the worst outcome. Generic JSON Schema validators remain free to treat unknown `x-*` keywords as annotations; the rejection is a GTS-layer rule.

Option 4a (keep `x-gts-ref` as a deprecated kind-blind alias) was rejected: the whole defect is that the alias validates too little, so leaving it live prolongs exactly the ambiguity the ADR exists to remove, and a pre-1.0 specification with three reference-implementation repositories is the cheapest place this break will ever be.

### Implications

- **Specification** — §9.6 rewritten as a self-contained normative section (§9.6.1–§9.6.6): assertion semantics, operand grammar with precedence, two-stage matching with the MINOR matrix and the kind table, the reserved `/$id` token and dynamic rebinding, `anyOf`/`const` idioms, and enforcement including the §9.3 boundary. §11.0 corrected to distinguish the four document-level keywords from the field-level reference keywords. §9.7's `topicRef` example and the §9.3 / §9.8 / §9.11.5 mentions updated. BREAKING 0.14 row added. The specification carries no account of the superseded keyword beyond that row: rationale and the migration table live in this ADR.
- **Examples** — migrate every occurrence in `examples/` (JSON Schema, TypeSpec `@extension`, YAML) by field intent; normalize `"/gts.…"` to a literal; drop redundant trailing chain wildcards; update `examples/modules/README.md`, which documents `./$id`.

  The migration is not a rename, and `examples/modules/types/gts.x.core.modules.module.v1~.schema.json` shows why all three judgements are needed in one file. Its `type` field holds a Type Identifier (`x-gts-type-ref`). Its `capabilities` and `requirements` items hold **Instance** Identifiers — the shipped instance lists `gts.x.core.modules.capability.v1~x.core.api.has_ws.v1` and `gts.x.core.modules.module.v1~x.webstore._.catalog.v1` — so both become `x-gts-instance-ref`. And `requirements` must additionally move from `/$id` to the **literal** `gts.x.core.modules.module.v1~`: under Sub-decision A a dynamic `/$id` would confine a derived module type's requirements to instances of that derived type alone, forbidding a plugin module from requiring a base-type module, which is plainly not the intent. Every `/$id` site must be re-read for this, not just re-spelled.
- **Conformance tests** — wrong-kind rejection in both directions; the three operand forms and their precedence; terminal-string pointer targets, including rejection of a pointer resolving to a pointer-shaped string; direct, derived, well-known and combined-anonymous (`~<UUID>`) candidates; the MINOR matrix; rejection of an unchained non-`~` identifier (which the §8.2 regex alone would accept); wildcard root-subsets, including a pattern that matches both a derived Type and an Instance; `anyOf`/`oneOf`/`not` composition proving assertion semantics; both keywords at one location rejected; non-string values rejected; unresolvable and Instance-Identifier operands rejected at `/validate-type-schema`; a schema stored with validation disabled reported as a schema-level error at instance-validation time; dynamic `/$id` rebinding through authored `$ref`/`allOf` including sibling rejection; a chained `$id` **without** an authored schema reference importing no ancestor constraint; and legacy `x-gts-ref` asserted as rejected. `tests/test_refimpl_x_gts_ref.py:187` must be migrated off operand indirection.
- **OP#8 (Type Schema Evolution Compatibility)** — the migration is **not** uniformly a narrowing. A literal operand usually narrows the annotated field, but `x-gts-type-ref: "/$id"` widens it relative to 0.13's equality reading and `x-gts-instance-ref: "/$id"` exchanges it for a disjoint set; other constraints on the same field may mask either effect. The relation MUST therefore be established by whole-schema accepted-set comparison (§4.3, §4.5), never inferred from the keyword swap — and, per Sub-decision E, only once the accepted-set definition accounts for GTS instance-assertion keywords. Checkers that do not model these keywords report `unknown`, which per §4.3 is not itself evidence of incompatibility.
- **OP#9 (Version Casting)** — no new prohibition. A cast MUST produce a value satisfying the target field's constraint, including its kind; the identity-field rewriting rules of §4 apply unchanged, and casting across a changed reference constraint remains possible where an explicit mapping exists.
- **OP#12 (Type Derivation Validation)** — governed by accepted-set inclusion, not by a syntactic kind comparison. Widening a reference field, or swapping its kind, ordinarily violates derivation compatibility, but the verdict is on the full effective schema: `const`, `not`, or an unreachable branch can make a syntactic kind swap harmless. With dynamic `/$id`, a leaf's inherited constraint is automatically the narrower one.
- **Known follow-up** — the `Valid(S)` repair of Sub-decision E, as its own issue and ADR.
- **Known pre-existing defects, out of scope** — two, both worked around by making §9.6 self-contained rather than fixed here, and both to be filed separately. (a) §10's wildcard rules contradict their own examples for `v1~*`: the prose says the bare chain-suffix wildcard matches the root, the worked example omits it. (b) The §8.2 chained-identifier regex makes its entire `~`-suffix group optional and therefore accepts an unchained non-`~` identifier such as `gts.a.b._.c.v1`, which §2.1 and the §2.3 EBNF reject and which §8.2's own prose validation rules also forbid. §9.6.3 cites §2.1/§2.3 as governing for this reason.
- **Reference implementations** — follow-up implementation issues for `gts-go` and `gts-rust` are opened after this ADR and the conformance contract land. `gts-python` follows the same contract.

## Pros and Cons of the Options

### Option 1 — Express kind in the operand

- **+** No new keywords; no migration.
- **−** Does not work: a chain-suffix wildcard cannot exclude the type root, since the discriminating `~` is the candidate's last character.
- **−** `const` covers only a single fixed value, not "any instance of this type or its descendants".
- **−** Leaves author intent unstated even where a workaround exists.

### Option 2 — Sibling kind modifier keyword

- **+** Keeps one reference keyword; the operand language is untouched.
- **−** Two keywords to keep in sync at every reference site.
- **−** Any default for the modifier reintroduces the ambiguity; requiring it costs the same author churn as the split.
- **−** More surface to specify: placement, allowed values, behavior when orphaned.

### Option 3 — Object-valued `x-gts-ref`

- **+** One keyword; kind is structurally adjacent to the operand.
- **+** Can be a single clean break, exactly like Option 4b.
- **−** Breaking anyway, so it buys no migration relief over the split.
- **−** Loses the plain-string annotation form used by TypeSpec `@extension` and YAML.
- **−** The keyword value needs a meta-schema of its own.
- **−** Dual acceptance still needs either a third `kind` value — the ambiguity renamed — or `anyOf`, which Option 4 already provides.

### Option 4 — Two keywords *(chosen)*

- **+** Kind is part of the keyword contract; a validator cannot ignore it and an author cannot omit it.
- **+** Reuses the operand language, wildcard and version rules, and registry layering.
- **+** Reads at the call site — `x-gts-instance-ref` states the field's intent without cross-referencing a sibling keyword.
- **+** Dual acceptance is expressible with standard `anyOf`, and is then visibly deliberate.
- **+** Keeps the plain-string value shape, so TypeSpec and YAML emitters need no new machinery.
- **−** Breaking: every occurrence in the specification, examples, tests, and three reference implementations must be migrated.
- **−** Migration cannot be mechanical, because `/$id` is used for both roles today.
- **−** Two keywords instead of one to document and validate.

### Option 4a — Deprecated kind-blind alias

- **+** Existing schemas keep registering.
- **−** They keep registering *without* the constraint the migration exists to add — the ambiguity survives in the field.
- **−** Three keywords to specify and test, plus precedence rules when the alias appears next to a new keyword.
- **−** Delays the break without reducing its total cost.

### Option 4b — Clean break *(chosen)*

- **+** One migration, one version, no precedence rules.
- **+** Rejection is loud: a stale schema fails registration instead of silently under-validating.
- **+** Pre-1.0 with three reference implementations is the cheapest point to do this.
- **−** Every 0.13 schema must be edited before it can register against 0.14.

### Option R1 — Fully lexical operands

- **+** Simplest possible rule; every operand resolves against one concrete document.
- **+** Matches plain JSON Schema `$ref` scoping intuition.
- **−** Sibling rejection requires every leaf to restate the constraint — the boilerplate that base-level declaration exists to avoid.
- **−** Fails open: a leaf that omits the restatement silently accepts sibling instances, with no error anywhere.

### Option R2 — Fully dynamic operands

- **+** One uniform rule; every pointer rebinds to the leaf.
- **−** Not implementable as stated: JSON Schema evaluation produces no canonical merged document for a pointer to address.
- **−** Would require inventing a virtual-schema construction with conflict rules for colliding branches, conditionals, recursion, nested `$id`s and `$dynamicRef`.
- **−** Enormous specification surface for one keyword's convenience.

### Option R3 — Hybrid *(chosen)*

- **+** Delivers polymorphic self-reference, which is the only case that actually needs dynamism.
- **+** Every rule resolves against a concrete artifact: one `$id` string, or one authoring resource.
- **+** Leaves the "chained `$id` imports nothing" rule of ADR-0001 intact and orthogonal.
- **−** One irregular form: `/$id` looks like a pointer but is a reserved token (`/$id/foo` is not).
- **−** Two resolution rules to document instead of one.

## More Information

Cross-references inside this specification: §9.6 (reference keywords), §9.7 (`topicRef` trait example), §9.3 (registration-time reference validation), §9.11.5 (enforcement pattern), §11.0 (keyword placement, dialect framing), §4.2 (MINOR addressability), §4.3 and §4.5 (compatibility as accepted-instance-set inclusion), §2.1–§2.3 (canonical form, chaining, EBNF), §3.7 (well-known and combined-anonymous instances), §8.1–§8.2 (parsing regexes), §10 (wildcards), OP#1, OP#8, OP#9, OP#12.

Related ADRs: [`adr/0001-derivation-form.md`](0001-derivation-form.md) — the chained `$id` alone establishes derivation, which is why an unreferenced ancestor body contributes no reference constraints (Sub-decision A).

Issue: [GlobalTypeSystem/gts-spec#96](https://github.com/GlobalTypeSystem/gts-spec/issues/96).

External references:

- [RFC 6901 — JavaScript Object Notation (JSON) Pointer](https://datatracker.ietf.org/doc/html/rfc6901)
- [`anyOf` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/combining#anyOf)
- [`const` in JSON Schema](https://json-schema.org/understanding-json-schema/reference/generic#constant-values)

Open questions for a later revision:

- This ADR keeps rooted matching for both keywords. If "exactly this type, no descendants" proves to be a common need, a future ADR may add an explicit non-rooted mode rather than relying on `const`.
- Whether the reserved `/$id` token should eventually be respelled as a non-pointer form (`$self`) once a breaking window is open for unrelated reasons.
