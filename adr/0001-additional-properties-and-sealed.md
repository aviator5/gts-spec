# ADR-0001: Separate instance closedness (`additionalProperties`) from derivation closedness (`x-gts-sealed`)

- **Status:** Proposed
- **Date:** 2026-05-20
- **Deciders:** GTS spec maintainers
- **Consulted:** —
- **Informed:** Reference implementations (gts-go, gts-rust), gts-spec conformance test suite
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

The GTS specification today uses JSON Schema's `additionalProperties: false` for two implicitly conflated purposes:

1. **Instance closedness** — at validation time, reject instances that contain fields not declared in the schema (the keyword's actual JSON Schema semantics).
2. **Derivation closedness** — at registry time, prevent derived types (`gts.A~B~`) from adding new top-level fields beyond what the base type (`gts.A~`) declares.

This conflation has caused three concrete pain points:

### Problem 1 — `additionalProperties: false` interacts badly with `allOf`

`additionalProperties` is an **in-place applicator**: it only considers `properties` and `patternProperties` defined in the same schema object. It does NOT see properties contributed by `$ref` or sibling `allOf` branches. Consequences:

```json
// Broken: top-level additionalProperties in derived schema
{
  "$id": "gts://gts.A~B~",
  "allOf": [{ "$ref": "gts://gts.A~" }],
  "properties": { "newField": {...} },
  "additionalProperties": false   // ⛔ rejects ALL inherited properties from A~
}
```

```json
// Equally broken: additionalProperties inside an allOf branch
{
  "$id": "gts://gts.A~B~",
  "allOf": [
    { "$ref": "gts://gts.A~" },
    {
      "properties": { "newField": {...} },
      "additionalProperties": false   // ⛔ same problem
    }
  ]
}
```

Authors expect "inherit base + add new field + close the object", but JSON Schema actually evaluates this as "reject everything except `newField`". This is a well-known JSON Schema footgun, and the current spec only partially warns about it (§5, lines 326–328).

### Problem 2 — `additionalProperties: false` is incompatible with forward compatibility

By definition (§4.2, §4.3), the closed content model breaks forward compatibility on any additive change. A consumer pinned to `v1.0` of a closed schema will reject `v1.1` data that adds a new optional property, because the unknown property is forbidden by `additionalProperties: false`. The spec already documents this in the §4.3 compatibility table and §4.4.2 example, but does not warn authors strongly enough at the place where they make the choice.

**Example.** A user-profile schema released as `v1.0` with the closed content model:

```jsonc
// gts.x.core.app.user_profile.v1.0~
{
  "$id": "gts://gts.x.core.app.user_profile.v1.0~",
  "type": "object",
  "required": ["id", "name", "email"],
  "properties": {
    "id":    { "type": "string" },
    "name":  { "type": "string" },
    "email": { "type": "string" }
  },
  "additionalProperties": false
}
```

A minor version `v1.1` adds an optional `phoneNumber` field — a normally safe additive change:

```jsonc
// gts.x.core.app.user_profile.v1.1~
{
  "$id": "gts://gts.x.core.app.user_profile.v1.1~",
  "type": "object",
  "required": ["id", "name", "email"],
  "properties": {
    "id":          { "type": "string" },
    "name":        { "type": "string" },
    "email":       { "type": "string" },
    "phoneNumber": { "type": "string" }
  },
  "additionalProperties": false
}
```

Now a producer running `v1.1` emits an instance:

```json
{ "id": "u-42", "name": "Alice", "email": "a@x.io", "phoneNumber": "+1-555-0100" }
```

A consumer still pinned to the `v1.0` schema validates this instance and **rejects it**: `phoneNumber` is not in `v1.0.properties`, and `additionalProperties: false` forbids it. Forward compatibility is broken purely because the closed content model was chosen on `v1.0`. Had `additionalProperties` been omitted (or set to `true`), the `v1.0` consumer would have ignored the unknown field and the data would have flowed through.

**Relation to the tolerant reader principle.** Forward compatibility is the version-axis projection of a broader design principle — the **tolerant reader principle** (Postel's Law: *"be conservative in what you do, be liberal in what you accept"*). A tolerant reader processes the fields it knows and ignores the rest; `additionalProperties: false` does the opposite, rejecting any instance that carries fields the reader does not know. Beyond the same-type version evolution shown above, closed content also breaks other patterns that depend on tolerant readers:

- **Pipeline enrichment** — an intermediary adds `correlationId` or `traceId` to a message in transit; a downstream consumer with a closed schema rejects the enriched message even though the original payload is intact.
- **Cross-vendor extension fields** — a vendor attaches operational metadata (`vendor_x.region`, `vendor_x.debug`) to a shared event type; consumers that do not know those fields reject the entire instance.
- **Producer-side optionality** — producers cannot opportunistically include diagnostic or context fields that consumers are free to ignore; every such field becomes a coordinated schema change.

In short, `additionalProperties: false` couples producers and consumers far more tightly than the underlying data flow requires. Forward compat is the most visible symptom, but the principle being violated is the more fundamental one.

### Problem 3 — `additionalProperties` is the wrong layer to control derivation

`additionalProperties` is a runtime instance-validation keyword. Authors who want to express *"derived types MUST NOT add new top-level properties to my schema"* (a schema-to-schema, registration-time constraint) currently have only two options, both wrong:

- **Put `additionalProperties: false` on the base schema.** This achieves the derivation-control side effect, but at the cost of forward compatibility (Problem 2) and at the cost of all the `allOf` gotchas above (Problem 1). It also overshoots: it forbids instances from carrying extra fields *at runtime*, which may not be the author's intent.
- **Use `x-gts-final: true` (§9.11).** This is too strict: it forbids derivation entirely, including legitimate refinements such as narrowing enums, tightening constraints, or specifying previously-open nested objects.

There is no middle ground today between "fully open for derivation" and "no derivation at all". And the language to express the partial closedness ("you may derive, but you may not add top-level fields") does not exist in JSON Schema at all — because it is a property of the **GTS type system**, not of any one schema instance.

Consider a platform team that owns the base event type and wants the contract *"the top-level shape of an event is fixed (`id` / `typeId` / `timestamp` / `payload`); vendors derive by refining `payload`, never by inventing new top-level keys"*.

**Attempt A — put `additionalProperties: false` on the base.** The intent (no new top-level keys in derived) is achieved as a side effect, but with two unwanted consequences:

```jsonc
// Base event, trying to lock the top-level set via additionalProperties
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "required": ["id", "typeId", "timestamp", "payload"],
  "properties": {
    "id":        { "type": "string" },
    "typeId":    { "type": "string" },
    "timestamp": { "type": "integer" },
    "payload":   { "type": "object", "additionalProperties": true }
  },
  "additionalProperties": false   // intent: lock the top-level set against derivation
}
```

Unintended consequences:
1. **Forward compatibility of the base itself is broken** (Problem 2). If the platform ever ships `v1.1` of this base with one extra top-level field, every `v1.0` consumer rejects `v1.1` instances. The author wanted to constrain *derived types*, not their own type's evolution.
2. **`allOf` footguns** (Problem 1) start firing on every legitimate derivation that mirrors the pattern. Authors who copy `additionalProperties: false` into their derived event schema produce schemas that reject their own inherited properties.
3. **Runtime overreach**: instances are now forbidden from carrying any extra fields, even fields that a downstream system might be using for non-validated context. The author wanted a registry-time constraint and got a runtime constraint by accident.

**Attempt B — use `x-gts-final: true`.** Too strict; it forbids all derivation, defeating the whole point of GTS extension:

```jsonc
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "properties": { "id": {...}, "typeId": {...}, "timestamp": {...}, "payload": {...} },
  "required": ["id", "typeId", "timestamp", "payload"],
  "x-gts-final": true
}
```

A perfectly legitimate derivation that only refines existing fields — never adds top-level keys — is rejected by the registry:

```jsonc
// Vendor derivation: narrows `typeId` to a const, refines `payload` structure.
// Adds zero top-level keys. Yet `x-gts-final` on the base rejects this at registration.
{
  "$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    {
      "properties": {
        "typeId": { "const": "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1~" },
        "payload": {
          "type": "object",
          "required": ["orderId", "customerId", "totalAmount"],
          "properties": {
            "orderId":     { "type": "string" },
            "customerId":  { "type": "string" },
            "totalAmount": { "type": "number" }
          }
        }
      }
    }
  ]
}
// ⛔ Rejected by OP#12: base is `x-gts-final`.
```

**Attempt C — express the actual intent.** There is no GTS or JSON Schema vocabulary today for "derive freely, refine constraints and nested objects, BUT do not add top-level keys". JSON Schema has no schema-to-schema keyword for this (all its keywords validate instances). GTS has only the binary `x-gts-final`. The middle ground that the author actually wants is literally inexpressible.

## Decision Drivers

- **Correctness over folklore.** Authors should not have to rediscover the `additionalProperties` + `allOf` pitfall.
- **Separation of concerns.** Instance validation and derivation control are different layers and should have different keywords.
- **Backward compatibility of the spec itself.** Existing conformance tests and reference implementations rely on the current §5 wording about `additionalProperties`. Any new rule should be additive where possible.
- **Symmetry with existing GTS modifiers.** `x-gts-final` and `x-gts-abstract` are already schema-to-schema controls enforced by OP#12 / OP#6; a partial-closedness modifier should follow the same pattern.
- **Minimal authoring burden.** The common case (top-level sealing) should be expressible with a single keyword on the root of the schema. Less common cases (sealing nested objects) should not require new ceremony.

## Considered Options

### Option 1 — Status quo (do nothing)

Keep using `additionalProperties: false` for both instance and derivation closedness; rely on §5 lines 326–328 to warn authors about the `allOf` interaction.

### Option 2 — Restrict `additionalProperties: false` placement; keep using it for both concerns

Add a normative rule: `additionalProperties: false` MUST NOT appear in a schema object that also contains `allOf`/`$ref`. Allowed only on standalone/root schemas and on inline-defined nested objects. No new keyword introduced.

### Option 3 — Introduce `x-gts-sealed` as a schema-root annotation only (model A)

A single boolean on the schema root that means "derived types MAY NOT add new top-level properties". Enforced by OP#12 at registration time. `additionalProperties` is left to its native JSON Schema meaning (instance validation only); spec discourages `additionalProperties: false` for GTS types that are expected to evolve or be derived.

### Option 4 — Introduce `x-gts-sealed` as a per-schema-object annotation (model B) — **selected**

Same as Option 3, but `x-gts-sealed` can be placed on any `type: object` sub-schema, sealing exactly that object's keys against extension by derived types. Most commonly placed on the root; occasionally on nested objects that hold a fixed set of system-defined keys (e.g., `metadata`). Other nested objects (e.g., `payload`) remain unsealed and free for derivation to refine.

## Decision Outcome

**Chosen option:** Option 4 — introduce `x-gts-sealed` as a **per-schema-object** annotation, and explicitly demote `additionalProperties: false` to its native JSON Schema role (instance validation), with clear authoring guidance against using it as a derivation-control mechanism.

The choice reflects the core insight from the consulted analysis: instance closedness and derivation closedness are orthogonal concerns and deserve orthogonal keywords. Per-object placement (model B) is symmetric with how JSON Schema authors already think about `additionalProperties` (per-object) and avoids the awkwardness of an all-or-nothing root flag when only one nested system-object needs to be sealed.

### Normative changes to the spec (README.md)

1. **§4.2 (JSON Schema Content Models)** — add a note that `additionalProperties: false` defines instance closedness only, breaks forward compatibility on additive changes (§4.3), and MUST NOT be used as a tool for controlling derivation.

2. **§5 (Validation semantics)** — replace the "additionalProperties and adding new properties" bullet (currently lines 326–328) with a stronger rule:

   > `additionalProperties: false` MUST NOT appear in a schema object that also contains `allOf`, `$ref`, `oneOf`, or `anyOf` referencing another schema (whether at the top level of the schema, or inside an `allOf` branch with sibling property declarations). Such combinations are rejected by JSON Schema 2020-12 in-place-applicator semantics and would reject the very inherited properties the author intended to keep. `additionalProperties: false` IS allowed in:
   > - schemas that do not compose via `allOf`/`$ref` (standalone or root base schemas with no GTS parent), and
   > - inline-defined nested object schemas inside a derived schema (e.g., the `payload` sub-schema of an event derivation).

3. **§9.11 (Schema modifiers)** — add a third modifier alongside `x-gts-final` and `x-gts-abstract`:

   | Keyword | Type | Purpose | Use case |
   |---|---|---|---|
   | `x-gts-sealed` | `boolean` | Marks the **object schema in which it is declared** as not extensible by derived types — derived schemas MUST NOT add new keys to that object's `properties`. | Base/parent schemas whose top-level (or specific nested) shape is fixed by contract but which still allow other forms of refinement. |

   Semantics:
   - **Placement:** MAY appear on any `type: object` schema object within a GTS Type Schema (root or nested). Per-object scope; does not propagate.
   - **OP#12 enforcement:** When registering a derived schema, for every object position where any schema in the inheritance chain declares `"x-gts-sealed": true`, the merged set of property keys contributed by the derived schema at that position MUST be a subset of the property keys present in the chain up to that point. New keys cause registration to fail.
   - **Refinement still allowed:** Derived schemas MAY narrow constraints on existing properties (e.g., reduce `maxLength`, narrow `enum`, increase `minimum`), MAY add `required`, MAY refine previously-open nested objects (recursively, subject to their own `x-gts-sealed` annotations).
   - **Instance validation unaffected:** `x-gts-sealed` does NOT affect instance validation. Instances MAY carry additional fields if and only if `additionalProperties` allows them. To also enforce closedness on instances, authors combine `x-gts-sealed` with a separate forward-compat decision about `additionalProperties` (see authoring guidance below).
   - **Mutual exclusion:** A schema MAY combine `x-gts-sealed` with `x-gts-abstract` (an abstract sealed base is meaningful). `x-gts-sealed` with `x-gts-final` is meaningless (final already forbids any derivation); registries MAY warn but SHOULD NOT reject.
   - **Annotation-only:** `x-gts-sealed`, like the other `x-gts-*` modifiers, MUST only appear in schema documents and MUST NOT appear in instance documents.

4. **§4.4 (Compatibility examples)** — augment with authoring guidance: for GTS types that participate in derivation, prefer the open content model (omit `additionalProperties` or set it to `true`) and use `x-gts-sealed` to constrain *which keys derived types may introduce*. Reserve `additionalProperties: false` for terminal contracts (config schemas, hardened input validation) that are not expected to evolve or be derived.

### Example — desired final shape of a sealed event base

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "x-gts-sealed": true,                 // derived types MUST NOT add top-level keys
  "properties": {
    "id":        { "type": "string" },
    "typeId":    { "type": "string" },
    "timestamp": { "type": "integer" },
    "metadata": {
      "type": "object",
      "x-gts-sealed": true,             // metadata is a fixed system-defined object
      "properties": {
        "source":  { "type": "string" },
        "traceId": { "type": "string" }
      }
    },
    "payload": {
      "type": "object",
      "additionalProperties": true       // payload is open: derived types refine it freely
    }
  },
  "required": ["id", "typeId", "timestamp", "payload"]
  // NOTE: no top-level "additionalProperties": false — instance closedness is a separate, opt-in concern
}
```

A derived event type may refine `payload` (with its own `properties` / `additionalProperties: false` inline, which is safe — Problem 1 does not apply because the nested `payload` schema is defined directly, not composed via `allOf`). It may not add top-level keys such as `tenantId`; if such fields are needed, they belong on a different base type or in a separate field of `payload`.

### Operations and conformance impact

- **OP#12 (Type Derivation Validation)** is extended to enforce `x-gts-sealed` in addition to its current responsibilities. The existing wording about "additionalProperties, narrowing/widening, etc." can be retained but should make clear that `additionalProperties` is enforced at the JSON-Schema level (instance compatibility), whereas `x-gts-sealed` is a GTS-level structural constraint enforced during schema registration.
- **OP#6 (Schema Validation of instances)** is unchanged. `x-gts-sealed` has no instance-validation effect.
- **Conformance tests** (gts-spec test suite) gain new cases under OP#12 covering:
  - Registering a derived schema that adds a top-level key to a sealed base → expect rejection.
  - Registering a derived schema that narrows or refines existing keys of a sealed base → expect success.
  - Sealed-on-nested object: derived adds a key inside the sealed nested object → expect rejection; derived narrows existing nested key → expect success.
- **Reference implementations** (gts-go, gts-rust) gain a new validator branch in their OP#12 pipeline. The change is additive; existing schemas without `x-gts-sealed` are unaffected.
- **Backward compatibility of the spec:** All three normative changes are additive or strictly clarifying. No previously-valid schema becomes invalid solely due to this ADR (the new MUST-NOT in §5 codifies behavior that was already broken under JSON Schema 2020-12; the spec change just makes the failure explicit at registration time).

## Pros and Cons of the Options

### Option 1 — Status quo

- **+** No spec change required.
- **−** Problems 1, 2, and 3 remain. Authors keep stepping on the `allOf` footgun.
- **−** No way to express partial-derivation closedness other than `x-gts-final` (too strict).

### Option 2 — Restrict `additionalProperties: false` placement; no new keyword

**Problems addressed:** P1 ✅ · P2 ❌ · P3 ❌

- **+** Addresses Problem 1 (the `allOf` footgun) with a single normative rule.
- **+** No new keyword to teach or implement.
- **−** Does not address Problem 3: there is still no way to control which top-level keys derived types may introduce, short of `x-gts-final`.
- **−** Conflates instance and derivation concerns: authors still use `additionalProperties: false` on the base as a backdoor mechanism for derivation control, paying the forward-compatibility cost (Problem 2) every time.

**Demonstration.** Under Option 2, the `user_profile.v1.0` schema from Problem 2 is still entirely legal — it is a standalone schema with no `allOf`/`$ref`, so the new placement rule does not touch it. The forward-compat break on the `v1.1` instance reproduces unchanged:

```jsonc
// Still valid under Option 2 (no allOf/$ref → placement rule doesn't fire).
{
  "$id": "gts://gts.x.core.app.user_profile.v1.0~",
  "type": "object",
  "properties": { "id": {...}, "name": {...}, "email": {...} },
  "additionalProperties": false   // ⚠ Problem 2 still fires when v1.1 ships
}
```

And the author from Problem 3 who wants "lock the top-level set of the event base against vendor derivation" is still stuck between:

```jsonc
// Backdoor A: additionalProperties: false on base — Option 2 allows this
// (still no allOf/$ref), but it carries the forward-compat cost AND the
// downstream allOf footgun in every derived schema that copies the pattern.
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "properties": { "id": {...}, "typeId": {...}, "payload": {...} },
  "additionalProperties": false
}
```

```jsonc
// Backdoor B: x-gts-final — still too strict, blocks legitimate refinements.
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "properties": { "id": {...}, "typeId": {...}, "payload": {...} },
  "x-gts-final": true
}
```

Neither expresses the actual intent. Problem 3 is untouched by Option 2.

### Option 3 — `x-gts-sealed` as schema-root only (model A)

**Problems addressed:** P1 ✅ · P2 ✅ · P3 ✅ (root only; nested sealing not expressible)

- **+** Separates concerns cleanly. Solves Problems 1, 2, and 3 for the common case.
- **+** Simpler semantics: one boolean, one position, one OP#12 rule.
- **−** Cannot express "the `metadata` object is sealed but the rest of the schema isn't". Authors must either seal everything or seal nothing.
- **−** Asymmetric with how JSON Schema authors think about `additionalProperties` (per-object), introducing cognitive friction.

**Demonstration of the common case (works).** The author from Problem 3 can now express exact intent without touching `additionalProperties`:

```jsonc
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "x-gts-sealed": true,                       // derivation-time constraint
  "properties": {
    "id":        { "type": "string" },
    "typeId":    { "type": "string" },
    "timestamp": { "type": "integer" },
    "payload":   { "type": "object", "additionalProperties": true }
  },
  "required": ["id", "typeId", "timestamp", "payload"]
  // No `additionalProperties: false` → forward compat preserved (P2 solved).
  // No `allOf` next to `additionalProperties: false` → P1 footgun avoided.
  // Top-level keys locked against vendor derivation → P3 solved.
}
```

**Demonstration of the limitation (mixed sealing — does NOT work).** A platform team wants the *opposite* of the case above: keep top-level open so vendors can attach extension fields, but lock down a system-controlled `metadata` sub-object whose shape is fixed by the platform. Under Option 3 this is inexpressible — `x-gts-sealed` lives only at the root:

```jsonc
// Desired intent (CANNOT be expressed under Option 3):
//   - top-level: OPEN for vendor derivation (vendors may add their fields)
//   - metadata:  SEALED (only platform-controlled keys allowed)
//   - payload:   OPEN (free refinement by vendors)
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  // x-gts-sealed must go at the root or nowhere. There's no way to say
  // "root open, metadata sealed". The author is forced to either:
  //   (a) seal everything (losing vendor top-level extensibility), or
  //   (b) seal nothing (losing metadata integrity).
  "properties": {
    "id":       { "type": "string" },
    "typeId":   { "type": "string" },
    "metadata": {
      "type": "object",
      "properties": { "source": {...}, "traceId": {...} }
      // ← here is where "x-gts-sealed: true" needs to go, but
      //   Option 3 forbids per-object placement.
    },
    "payload":  { "type": "object", "additionalProperties": true }
  }
}
```

### Option 4 — `x-gts-sealed` as per-schema-object (model B, selected)

**Problems addressed:** P1 ✅ · P2 ✅ · P3 ✅ (all positions, including nested)

- **+** Separates concerns cleanly (Problem 3 solved at the right layer).
- **+** Symmetric with `additionalProperties` placement, matching author intuition.
- **+** Expressive enough for the realistic mixed cases (`metadata` sealed, `payload` open).
- **+** Backward-compatible: schemas without the keyword behave exactly as today.
- **−** OP#12 enforcement must walk the schema recursively to find sealed positions; slightly more implementation complexity than Option 3.
- **−** Documentation must be careful to distinguish per-object placement from a global flag; authors might mis-read it as schema-root-only on first encounter.

**Demonstration of the mixed case (works where Option 3 fails).** The "top-level open, `metadata` sealed, `payload` open" intent that Option 3 cannot express is straightforward under Option 4 — `x-gts-sealed` simply moves to the nested object that needs it:

```jsonc
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  // No x-gts-sealed at root → top-level OPEN, vendors may add extension fields.
  "properties": {
    "id":       { "type": "string" },
    "typeId":   { "type": "string" },
    "metadata": {
      "type": "object",
      "x-gts-sealed": true,         // ← per-object placement, sealed HERE
      "properties": {
        "source":  { "type": "string" },
        "traceId": { "type": "string" }
      }
    },
    "payload":  { "type": "object", "additionalProperties": true }
  }
}
```

And the fully-locked case from Option 3 still works identically — `x-gts-sealed` at the root behaves the same way as in Option 3, just as one application of the per-object rule. Authors learn one keyword, place it wherever the constraint applies, and the same OP#12 walk enforces all positions uniformly.

## More Information

- Related sections of README.md:
  - §3.2 (GTS Types Inheritance)
  - §4.2 (JSON Schema Content Models)
  - §4.3 (Compatibility Rules for GTS Type Schemas)
  - §4.4.2 (Backward Compatibility Example — Closed Model)
  - §5 (Validation semantics for GTS chained IDs)
  - §9.11 (GTS Type Schema Modifiers `x-gts-final` / `x-gts-abstract`)
  - OP#6 (Schema Validation), OP#12 (Type Derivation Validation)
- Related JSON Schema concepts:
  - JSON Schema 2020-12, §10.3.2.3 `additionalProperties` (in-place applicator semantics)
  - JSON Schema 2020-12, §10.2.1.1 `allOf` (subschema composition)
- Open questions for follow-up:
  - Should `x-gts-sealed` interact with `patternProperties`? (Likely yes — sealed forbids derivation from introducing new pattern groups as well as new literal keys. To be specified in the implementing change.)
  - Should the registry surface a structured error code for "sealed violation" distinct from generic OP#12 failure? (Recommend yes, for tool ergonomics.)
  - Future: a `x-gts-sealed-traits` analogue for traits schemas (§9.x) — out of scope here, captured as a candidate follow-up.
