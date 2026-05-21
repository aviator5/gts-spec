# ADR-0002: Single canonical form for derivation — strict 1-item `allOf` + top-level overlay

- **Status:** Proposed
- **Date:** 2026-05-21
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Informed:** Reference implementations (gts-go, gts-rust), gts-spec conformance test suite
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

Up to this point the GTS specification has been silent on the **structural shape** of a derived GTS Type Schema. The semantic side (OP#12) validates derivation by checking *constraint compatibility* — that every valid instance of the derived schema is also a valid instance of every ancestor in the chain — but the spec does not say anything about how the derivation link itself is expressed in JSON Schema syntax.

In practice every reference implementation, every example in `examples/**/types/`, and every test in `tests/test_op12_*` and `tests/test_op13_*` uses the same de-facto shape:

```jsonc
{
  "$id": "gts://A~B~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "allOf": [
    { "$ref": "gts://A~" },
    { "type": "object", "properties": { /* ... */ }, "required": [ /* ... */ ] }
  ]
}
```

This is convention, not contract. JSON Schema Draft-07 permits a long list of semantically-equivalent shapes for the same intent — properties at the top level instead of inside `allOf`; `allOf` with three or more items; multiple `$ref`s; an `$ref` to some type that is not the immediate parent in the chained `$id`; even substituting `allOf` for `anyOf` or `oneOf` and relying on a degenerate single-branch case. Some of these shapes are obviously bugs; others are legitimate ways an author might write the same derivation; all of them today must either be accepted or rejected on a case-by-case basis by every implementation, with no normative guidance.

This costs us in three concrete ways.

### Problem 1 — Validators and linters must handle every JSON-Schema-permissible variation

Without a canonical shape, a registry that wants to enforce GTS-level rules ("the parent in `allOf` must be the immediate predecessor in the chained `$id`") has to first discover *which* of the many shapes it is looking at. Is the overlay at the top level or inside `allOf`? Are there one or two members in `allOf`? Is the `$ref` at index 0 or index 1? Linters and codegen face the same problem. Every cross-implementation interop bug we have seen in this area traces back to one tool accepting a shape that another tool rejects.

### Problem 2 — Authors do not know where to put `properties`, `required`, `additionalProperties`, `x-gts-traits-schema`, `x-gts-final`, ...

The top level of the schema and the second item of `allOf` are both syntactically valid homes for the overlay. Most ordinary keywords (`required`, `properties`, narrowed constraints) compose via `allOf` to produce the same effective schema regardless of placement; authors who write the same derivation two different ways generally get the same behaviour at instance-validation time.

The notable exception is `additionalProperties`. In Draft-07 it is an in-place applicator and only "sees" properties declared in the **same schema object** as itself — never properties contributed via `$ref` or sibling `allOf` branches. So none of the placements works the way authors intuitively expect:
- `additionalProperties: false` next to `properties: { tier: ... }` at the top level — rejects the base type's inherited `id`/`name` (they are not in top-level `properties`).
- `additionalProperties: false` inside an `allOf[1]` overlay next to its own `properties` — that branch also rejects `id`/`name`.
- `additionalProperties: false` at the top level when `properties` live only inside `allOf[1]` — rejects *every* field, including the derived `tier`.

Authors repeatedly try all three and get three different broken behaviours. The right answer is "don't use `additionalProperties: false` for derivation closedness at all" (the subject of a separate discussion outside this ADR) — but until that's settled, a single canonical shape at least removes the placement choice as a degree of freedom.

There is also a hybrid case to worry about: properties at the top level AND another overlay nested inside `allOf`. This is well-defined in JSON Schema (all three subschemas combine via implicit AND) but is opaque to read and to validate. A single canonical shape eliminates the placement question entirely and prevents the hybrid case.

### Problem 3 — Codegen and registry tooling cannot rely on a single inspection path

Tools that generate code from GTS Type Schemas, render documentation, or compute structural diffs between versions have to branch on the schema shape. A canonical shape collapses these branches and lets tools assume a single inspection path: read the top-level keys, follow the single `$ref` in `allOf` to the parent. Anything else is a malformed schema.

## Decision Drivers

- **Single-shape simplicity for validators, linters, and codegen.** One canonical form means one inspection path.
- **Author clarity.** Properties, required, modifiers, and trait keywords should live in one obvious place.
- **No new authoring burden.** The canonical form must be at least as natural as the current de-facto form, and ideally simpler.
- **Acceptable migration cost.** We are inside a breaking release window already; a one-time rewrite of examples and tests is acceptable. We are not adding migration burden that would block the release.

## Considered Options

### Running example used in this section

To keep the four options comparable, the worked examples below all express the same intent: a derived type `premium_user` that extends a base `user` type by adding a required `tier` field with an enum constraint. The base type is registered once and is the same across all options:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~",
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "id":   { "type": "string" },
    "name": { "type": "string" }
  }
}
```

Two instance payloads are referenced throughout:

```json
// Payload P-OK — valid against the derived premium_user
{ "id": "u-1", "name": "Alice", "tier": "gold" }
```

```json
// Payload P-BAD — missing the required `tier` field
{ "id": "u-2", "name": "Bob" }
```

Under each option below, we show the derived schema in the shape(s) admitted by that option, plus which payloads validate and which do not.

### Option 1 — Status quo (no normative form)

The spec stays silent on top-level shape. Any JSON-Schema-permissible structure is admissible: `allOf` with 1 / 2 / 3+ items, `allOf` without a `$ref`, multiple `$ref`s, hybrid forms (overlay at the top level AND nested inside `allOf`), top-level `anyOf`/`oneOf`/`not`, and so on. The registry checks only the existing OP#12 semantic compatibility rules; it does not reject structural anomalies. This is the de-facto state of the spec before this ADR.

Under Option 1 **all of the following shapes coexist** in the wild because no rule forbids any of them:

```jsonc
// Shape 1a — overlay at top level (Form A)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": { "tier": { "type": "string", "enum": ["gold", "platinum"] } }
}
```

```jsonc
// Shape 1b — overlay inside allOf (Form B)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "allOf": [
    { "$ref": "gts://gts.x.example.user.v1~" },
    {
      "type": "object",
      "required": ["tier"],
      "properties": { "tier": { "type": "string", "enum": ["gold", "platinum"] } }
    }
  ]
}
```

```jsonc
// Shape 1c — hybrid: overlay at top level AND nested inside allOf
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.example.user.v1~" },
    { "properties": { "tier": { "type": "string", "enum": ["gold", "platinum"] } } }
  ],
  "required": ["tier"]
}
```

```jsonc
// Shape 1d — split overlay across two allOf items
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "allOf": [
    { "$ref": "gts://gts.x.example.user.v1~" },
    { "required": ["tier"] },
    { "properties": { "tier": { "type": "string", "enum": ["gold", "platinum"] } } }
  ]
}
```

**Payload behavior under Option 1:** all four shapes happen to produce the same effective JSON Schema (`P-OK` validates, `P-BAD` fails because `tier` is required). But the equivalence is *incidental*. Any variant that adds `additionalProperties: false` — at the top level, inside an `allOf` branch, or both — silently rejects inherited properties from the base because the keyword does not "see" properties contributed through `$ref` (see Problem 2). So `P-OK` fails on every such variant, regardless of where the closing keyword is placed. Implementations have no normative rule that forbids any of these variations and they handle them inconsistently.

### Option 2 — Strict Form A (`allOf` with exactly one `$ref` to parent; overlay at the top level) — **selected**

Only one schema shape is accepted for the derived type:

```jsonc
// The only valid form under Option 2
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": {
    "tier": { "type": "string", "enum": ["gold", "platinum"] }
  }
}
```

The derived schema looks like a normal JSON Schema *plus* one extra `allOf` pointer back to its parent. Everything the derived schema contributes — properties, required, narrowed constraints, content-model keywords, GTS modifiers, trait keywords — lives at the top level of the schema object.

**Payload behavior:**
- `P-OK` (`{"id": "u-1", "name": "Alice", "tier": "gold"}`) validates — satisfies the parent (id, name present) and the derived top level (tier present and in enum).
- `P-BAD` (`{"id": "u-2", "name": "Bob"}`) fails — derived schema requires `tier`.
- All shapes 1b–1d from Option 1 (and any other variant) are rejected at registration regardless of payload.

### Option 3 — Strict Form B (`allOf` with exactly two items: `$ref` + inline overlay)

```jsonc
// The only valid form under Option 3
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "allOf": [
    { "$ref": "gts://gts.x.example.user.v1~" },
    {
      "type": "object",
      "required": ["tier"],
      "properties": {
        "tier": { "type": "string", "enum": ["gold", "platinum"] }
      }
    }
  ]
}
```

This is the current de-facto convention in examples and tests. Migration cost is zero. The overlay is a self-contained sub-schema, which has minor advantages for tools that want to diff or extract the "delta" between a base and a derivation.

**Payload behavior:**
- `P-OK` validates — satisfies both `allOf` branches.
- `P-BAD` fails — derived overlay requires `tier`.
- Form-A-shaped schemas (overlay at top level) are rejected at registration regardless of payload.

### Option 4 — Relaxed (Form A or Form B both valid; everything else rejected)

A new normative rule with **two** canonical shapes instead of one. Form A and Form B are both accepted; every other shape — `allOf` with 3+ items, `allOf` without a `$ref`, multiple `$ref`s, hybrid forms (top-level overlay AND inside `allOf`), top-level `anyOf`/`oneOf`/`not` — is rejected at registration. Authors choose between Form A and Form B based on readability.

This differs from Option 1 (Status quo) in that the registry *does* perform structural validation; it just permits two canonical shapes rather than one.

Under Option 4, the SAME derived type can legitimately be written in two ways:

```jsonc
// 4a — Form A (overlay at top level)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "type": "object",
  "allOf": [{ "$ref": "gts://gts.x.example.user.v1~" }],
  "required": ["tier"],
  "properties": { "tier": { "type": "string", "enum": ["gold", "platinum"] } }
}
```

```jsonc
// 4b — Form B (overlay inside allOf)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.example.user.v1~vendor.premium_user.v1~",
  "allOf": [
    { "$ref": "gts://gts.x.example.user.v1~" },
    {
      "type": "object",
      "required": ["tier"],
      "properties": { "tier": { "type": "string", "enum": ["gold", "platinum"] } }
    }
  ]
}
```

**Payload behavior:** both shapes accept `P-OK` and reject `P-BAD` identically. Variants like Shape 1c (hybrid) or 1d (split across 3 allOf items) are rejected at registration. The downside is that one platform may publish Form A and another Form B for semantically identical types, forcing every consumer to handle both shapes.

## Decision Outcome

**Chosen option:** Option 2 — strict Form A. The derived GTS Type Schema MUST contain `allOf` with exactly one subschema, that subschema MUST be `{"$ref": "gts://<immediate-parent>"}`, and everything else lives at the top level of the derived schema alongside `allOf`. Form B, Form C, multi-item `allOf`, skip-level `$ref`s, references to unrelated types, and top-level `anyOf`/`oneOf`/`not` are all invalid and MUST be rejected at registration time.

The same canonical form applies uniformly to host types and to trait types — a trait type is a regular registered GTS Type Schema, and the rules do not distinguish between them.

### Normative changes to the spec (README.md)

1. **New subsection 3.2.1 "Top-level composition rules for GTS Type Schemas"** (introduced in this release) — states the canonical form for derived schemas, the immediate-parent `$ref` rule, the prohibition on top-level `anyOf`/`oneOf`/`not`, and the rule that base schemas (single-segment chain) do not use `allOf` for derivation and also do not use top-level `anyOf`/`oneOf`/`not`. References this ADR for the rationale.

2. **OP#12 description** — extended: structural validation now enforces the rules from 3.2.1 in addition to the existing constraint-compatibility checks.

3. **Section 11.0 (JSON Schema Dialect)** — short addition noting that `anyOf`/`oneOf`/`not`, while valid Draft-07 keywords, are restricted at the top level of GTS Type Schemas per 3.2.1.

### Example — desired final shape of a derived event type

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" }
  ],
  "required": ["payload"],
  "properties": {
    "typeId": { "const": "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~" },
    "payload": {
      "type": "object",
      "properties": {
        "orderId": { "type": "string" },
        "totalAmount": { "type": "number" }
      },
      "required": ["orderId", "totalAmount"]
    }
  },
  "x-gts-traits": {
    "topicRef": "gts.x.core.events.topic.v1~x.commerce._.orders.v1",
    "retention": "P90D"
  }
}
```

A few things to note about this shape:

- `allOf` has exactly one item. That item is the `$ref` to the immediate parent (`gts.x.core.events.type.v1~`). Skip-level `$ref`s (referencing an ancestor higher up the chain) are not permitted.
- `type: "object"` appears at the top level of the derived schema, not inside `allOf`. The same is true of `properties`, `required`, and the trait keywords.
- Nested sub-schemas (e.g., `payload`) are unrestricted: `anyOf`, `oneOf`, and the rest of JSON Schema remain available at depth. The restriction is purely top-level.

### Operations and conformance impact

- **OP#12 (Type Derivation Validation)** is extended to enforce the top-level composition rules at registration time.
- **OP#6 (Schema Validation of instances)** is unchanged — the canonical form does not affect instance validation, because `allOf` semantics in JSON Schema produce the same merged constraints regardless of where the overlay lives.
- **`register_derived` test helper** (`tests/helpers/http_run_helpers.py`) changes shape — `allOf` becomes a single-item list and the overlay is spread at the top level. Existing call sites do not change.
- **Existing example schemas** — every `examples/**/types/*.schema.json{,c}` that uses Form B is rewritten to Form A in the same release.
- **Reference implementations** (gts-go, gts-rust) add a structural validator branch in their OP#12 pipeline. This is a new requirement, not an additive one — existing Form-B schemas in third-party registries become invalid and must be migrated.
- **Backward compatibility of the spec:** this is a **breaking change**. It is bundled with the trait-system redesign (URN-string `x-gts-traits-schema`, parallel derivation) under one BREAKING version entry — see the README version log.

## Pros and Cons of the Options

### Option 1 — Status quo

**Problems addressed:** P1 ❌ · P2 ❌ · P3 ❌

- **+** No spec change required.
- **−** Every implementation continues to invent its own shape recognition. Cross-implementation bugs persist.
- **−** Authors continue to guess at placement; the `additionalProperties` + `allOf` footgun keeps catching them.
- **−** Codegen and tooling stay branchy.

### Option 2 — Strict Form A (selected)

**Problems addressed:** P1 ✅ · P2 ✅ · P3 ✅

- **+** Validators have one shape to recognise. Linters and codegen have one inspection path.
- **+** Properties / required / modifiers / trait keywords always live at the top level — one place to look, one place to write them.
- **+** The derived schema reads as a normal JSON Schema with one extra `allOf` pointer to its parent; consistent with how base schemas already look.
- **+** Eliminates an entire class of placement-ambiguity bugs around `additionalProperties` by removing the "did the author put it on the right level?" question. (The underlying Draft-07 `additionalProperties` + `$ref` interaction is a separate concern, outside the scope of this ADR.)
- **−** Migrates ~10 example files and the `register_derived` test helper; existing third-party Form-B schemas become invalid (one-time migration).
- **−** Loses the minor "overlay is a self-contained sub-schema" property of Form B, which a small set of tools exploit for diffing.

### Option 3 — Strict Form B

**Problems addressed:** P1 ✅ · P2 ◐ · P3 ✅ (partially)

- **+** Zero migration cost; matches existing examples and tests verbatim.
- **+** Overlay is a self-contained sub-schema — convenient for tools that extract or diff "deltas".
- **+** Single canonical shape, like Option 2, addresses P1 and P3.
- **−** `type: "object"` either gets duplicated (top level *and* inside the overlay) or omitted at the wrong level. Either choice creates pedagogical friction.
- **−** `additionalProperties: false` placement is still ambiguous in practice (top level vs inside `allOf`); authors place it wrongly more often than in Form A in our observed examples.
- **−** Deeper nesting for the most common authoring path.

### Option 4 — Relaxed (either form valid)

**Problems addressed:** P1 ❌ · P2 ❌ · P3 ❌

- **+** Author flexibility.
- **−** Doubles the validation surface — every test must cover both forms; every validator must accept both.
- **−** Splits the community: some teams adopt Form A, others Form B. Cross-vendor schemas mix and match. No single inspection path for tooling.
- **−** Contradicts the "simpler validation" goal that motivated this ADR in the first place.

## More Information

This ADR is part of one consolidated BREAKING spec release (version 0.12) that also redesigns the trait system to reference trait-types by URN and removes inline-schema / composition forms of `x-gts-traits-schema`. See the README version log entry for the full set of changes that ship together.
