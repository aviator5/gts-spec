<!-- gts-spec-version: 0.11 -->
> **VERSION**: GTS specification draft, version 0.11

# Global Type System (GTS) Specification

This document defines GTS — a simple, human-readable, globally unique identifier and referencing system for data type definitions (e.g., JSON Schemas) and data instances (e.g., JSON objects). It is specification-first, language-agnostic, and intentionally minimal, with primary focus on JSON and JSON Schema.

**Format Support**: GTS Types and GTS Instances can be represented in multiple formats including JSON, YAML, and TypeSpec. See the [examples directory](./examples/) for demonstrations in different formats.

The GTS identifiers are strings in a format like:

```
gts.<vendor>.<package>.<namespace>.<type>.v<MAJOR>[.<MINOR>]
```

They can be used instead of UUID, ULID, URN, JSON Schema URL, XML Namespace URI, or other notations for identification of various objects and schema definitions like:

- API data types and typed payloads (e.g. custom resource attributes)
- RPC contracts schemas
- API errors, headers and various semantics definitions
- Event catalogs, messages and stream topics
- Workflow categories and instances
- FaaS functions or actions contract definitions
- Policy objects (RBAC/ABAC/IAM)
- UI elements, schemas and forms
- Observability payloads (e.g. log formats)
- IoT/Edge telemetry data (e.g. device message formats)
- Warehouse/lake schemas
- Enumerations and references (e.g. enum id + description)
- ML/AI artifacts (e.g. model metadata or MCP tools declarations)
- Configuration-as-data templates and config instances
- Testing artifacts (e.g. golden records and fixtures)
- Database schemas
- Compliance and audit objects

Besides being a universal identifier, GTS provides concrete, production-ready capabilities that solve common architectural challenges for platform vendors and service providers integrating multiple third-party services under single control plane. In particular:

- **Extensible plugin architectures**: Third-party vendors can safely extend platform base types such as custom API fields, events, settings, configs, UI elements, user roles, licensing, etc.
- **Cross-vendor type safety**: Validate contracts (APIs, events, configs, etc.) across multiple vendors with automated compatibility checking in a middleware layer
- **Hybrid database storage**: Store base type fields in indexed columns for fast queries, vendor-specific extensions in JSON/JSONB—no schema migrations needed
- **Granular access control**: Use wildcard patterns and attribute-based policies for fine-grained type-based authorization (ABAC) without maintaining explicit lists
- **Human-readable debugging**: Identifiers encode vendor, package, namespace, and version—instantly comprehensible in logs and traces
- **Schema evolution without downtime**: Add optional fields, register new derived types, and deploy producers/consumers independently

See the [Practical Benefits for Service and Platform Vendors](#51-practical-benefits-for-service-and-platform-vendors) section for more details.

## Table of Contents

- [Global Type System (GTS) Specification](#global-type-system-gts-specification)
- [Terminology](#terminology)
- [1. Motivation](#1-motivation)
- [2. Identifier Format](#2-identifier-format)
  - [2.1 Canonical form](#21-canonical-form)
  - [2.2 Chained identifiers](#22-chained-identifiers)
  - [2.3 Formal Grammar (EBNF)](#23-formal-grammar-ebnf)
- [3. Semantics and Capabilities](#3-semantics-and-capabilities)
  - [3.1 Core Operations](#31-core-operations)
  - [3.2 GTS Types Inheritance](#32-gts-types-inheritance)
  - [3.2.1 Top-level composition rules for GTS Type Schemas](#321-top-level-composition-rules-for-gts-type-schemas)
  - [3.3 Query Language](#33-query-language)
  - [3.4 Attribute selector](#34-attribute-selector)
  - [3.5 Access control with wildcards](#35-access-control-with-wildcards)
  - [3.6 Access Control Implementation Notes](#36-access-control-implementation-notes)
  - [3.7 Well-known and Anonymous Instances](#37-well-known-and-anonymous-instances)
- [4. GTS Identifier Versions Compatibility](#4-gts-identifier-versions-compatibility)
  - [4.1 Compatibility Modes](#41-compatibility-modes)
  - [4.2 JSON Schema Content Models](#42-json-schema-content-models)
  - [4.3 Compatibility Rules for GTS Type Schemas](#43-compatibility-rules-for-gts-type-schemas)
  - [4.4 GTS Versions Compatibility Examples](#44-gts-versions-compatibility-examples)
  - [4.5 Best Practices for GTS Type Schema Evolution](#45-best-practices-for-gts-type-schema-evolution)
- [5. Typical Use-cases](#5-typical-use-cases)
  - [5.1 Practical Benefits for Service and Platform Vendors](#51-practical-benefits-for-service-and-platform-vendors)
  - [5.2 Example: Multi-vendor Event Management Platform](#52-example-multi-vendor-event-management-platform)
  - [5.3 GTS Registry Requirement](#53-gts-registry-requirement)
- [6. Implementation-defined and Non-goals](#6-implementation-defined-and-non-goals)
- [7. Comparison with other identifiers](#7-comparison-with-other-identifiers)
- [8. Parsing and Validation](#8-parsing-and-validation)
  - [8.1 Single-segment regex (type or instance)](#81-single-segment-regex-type-or-instance)
  - [8.2 Chained identifier regex](#82-chained-identifier-regex)
- [9. Reference Implementation Recommendations](#9-reference-implementation-recommendations)
  - [9.1 Identifier reference in JSON and JSON Schema](#91---identifier-reference-in-json-and-json-schema)
  - [9.2 GTS operations (OP#1 - OP#13)](#92---gts-operations-op1---op13)
  - [9.3 GTS entities registration](#93---gts-entities-registration)
  - [9.4 CLI support](#94---cli-support)
  - [9.5 Web server with OpenAPI](#95---web-server-with-openapi)
  - [9.6 `x-gts-ref` support](#96---x-gts-ref-support)
  - [9.7 GTS Type Schema Traits (`x-gts-traits-schema` / `x-gts-traits`)](#97---gts-type-schema-traits-x-gts-traits-schema--x-gts-traits)
  - [9.8 YAML support](#98---yaml-support)
  - [9.9 TypeSpec support](#99---typespec-support)
  - [9.10 UUID as object IDs](#910---uuid-as-object-ids)
  - [9.11 GTS Type Schema Modifiers (`x-gts-final` / `x-gts-abstract`)](#911---gts-type-schema-modifiers-x-gts-final--x-gts-abstract)
- [10. Collecting Identifiers with Wildcards](#10-collecting-identifiers-with-wildcards)
- [11. JSON and JSON Schema Conventions](#11-json-and-json-schema-conventions)
- [12. Notes and Best Practices](#12-notes-and-best-practices)
- [13. Testing](#13-testing)
- [14. Registered Vendors](#14-registered-vendors)


## Document Version

| Ver | Status                                                                                             |
|-----|----------------------------------------------------------------------------------------------------|
| 0.1 | Initial Draft, Request for Comments                                                                |
| 0.2 | Semantics and Capabilities refined - access control notes, query language, attribute selector      |
| 0.3 | Version compatibility rules refined; more practical examples of usage; remove Python examples      |
| 0.4 | Clarify some corner cases - tokens must not start with digit, uuid5, minor version semantic        |
| 0.5 | Added Referece Implmenetation recommendations (section 9)                                          |
| 0.6 | Introduced well-known/anonymous instance term; defined field naming implementation recommendations |
| 0.7 | BREAKING: require $ref value to start with 'gts://'; strict rules for schema/instance distinction; prohibiting well-known instances without left-hand type segments  |
| 0.8beta1 | Add OP#12 (schema vs schema validation), unified validation endpoint (/validate-entity), and clarify instance -> schema and schema -> schema validation semantics for chained GTS IDs |
| 0.8beta2 | Introduce schema traits (`x-gts-traits-schema`, `x-gts-traits`) and OP#13 (schema traits validation) |
| 0.8 | Add alternate combined anonymous instance identifier format |
| 0.9 | Add `x-gts-final` and `x-gts-abstract` schema modifiers; enforce final/abstract semantics in OP#6 and OP#12 |
| 0.10 | BREAKING: terminology unified around GTS Type / GTS Instance; rename API fields `schema_id` → `type_id` (also `old_schema_id`/`new_schema_id`/`to_schema_id`/`selected_schema_id_field`); rename API field `is_schema` → `is_type` (type-definition vs instance discriminator); `type_id` MUST be a GTS Type Identifier or `null` — no longer falls back to JSON Schema dialect URL; rename endpoints `/validate-schema` → `/validate-type`, `/schemas` → `/types`; rename OP#12 'Schema vs Schema Validation' → 'Type Derivation Validation'; rename OpenAPI components `ValidateSchemaRequest` → `ValidateTypeRequest`, `SchemaRegister` → `TypeRegister`; rename example directories `examples/**/schemas/` → `examples/**/types/` (file extensions `.schema.json` retained); add Terminology section |
| 0.11 | Introduce term **GTS Type Schema** as the canonical definition of a GTS Type; remove the standalone `Schema` term from Terminology; rewrite `GTS Type` entry to name the abstract registered entity; rename `GTS Type Registry` → `GTS Registry` (registry now scopes both Type Schemas and well-known Instances). **Conformance tests for reference implementations** also updated: rename API endpoints `/validate-type` → `/validate-type-schema` and `/types` → `/type-schemas`; rename OpenAPI components `TypeRegister` → `TypeSchemaRegister`, `ValidateTypeRequest` → `ValidateTypeSchemaRequest`; rename request field `TypeSchemaRegister.schema` → `TypeSchemaRegister.type_schema`; rename helper `validate_type` → `validate_type_schema`. |
| 0.12 | BREAKING: introduce normative **top-level composition rules** (new §3.2.1, see [ADR-0002](./adr/0002-strict-allof-derivation-form.md)) — derived GTS Type Schemas MUST use the strict canonical form (single-item `allOf` with `$ref` to the immediate parent in the chained `$id`; overlay constraints at the top level); top-level `anyOf`/`oneOf`/`not` are forbidden on all GTS Type Schemas (nested usage unchanged). **Trait system redesign** (§9.7 full rewrite): `x-gts-traits-schema` value type changes from inline JSON Schema to a **single GTS Type URN string** referencing a registered trait-type; inline-schema, `$ref`, and composition forms removed (no deprecation); trait-types are first-class GTS Type Schemas subject to the same derivation rules; host-type and trait-type derivation chains run in parallel (a derived host's trait-type MUST be derived from the ancestor's trait-type); trait completeness made explicit — a non-abstract host with unresolved required trait fields is invalid; shallow + immutable-once-set merge semantics preserved. **OP#12** extended with structural validation per §3.2.1. **Existing examples and tests** (`examples/events/types/`, `test_op12_*`, `test_op13_*`) are rewritten to the new model. |

## Terminology

This specification uses the following terms with precise meanings:

- **GTS Type**: a type entity identified by a GTS Type Identifier and defined by a GTS Type Schema. A GTS Type may exist as a standalone document (e.g., a `*.schema.json` file), be exchanged between systems, or be stored in a GTS Registry.
- **GTS Type Identifier**: a canonical GTS identifier ending with `~` that identifies a GTS Type.
- **GTS Type Schema**: the canonical definition of a GTS Type — a JSON Schema document annotated with the GTS vocabulary (`x-gts-*`), describing the type's instance shape, traits, metadata, and relations.

  Implementations MAY accept alternative source forms (e.g., TypeSpec, YAML) provided they deterministically map to a canonical GTS Type Schema. The canonical form, used for interchange, validation, and registration, is the JSON Schema document.
- **GTS Registry**: a registry that stores and resolves GTS entities — Type Schemas and well-known Instances — by GTS Identifier.
- **GTS Instance**: a concrete object, value, or document that conforms to a GTS Type.
- **GTS Instance Identifier**: a GTS identifier without the trailing `~`, used to identify a well-known instance.

## 1. Motivation

The proliferation of distributed systems, microservices, and event-driven architectures has created a significant challenge in maintaining **data integrity**, **system interoperability**, and **type governance** across organizational boundaries and technology stacks.

Existing identification methods—such as opaque UUIDs, simple URLs (e.g. JSON Schema URLs), or proprietary naming conventions—fail to address the full spectrum of modern data management requirements. The **Global Type System (GTS)** is designed to solve these systemic issues by providing a simple, structured, and self-describing mechanism for identifying and referencing GTS Types and GTS Instances.

The primary value of GTS is to provide a single, universal identifier that is immediately useful for:

### 1.1 Unifying Data Governance and Interoperability

**Human- and Machine-Readable**: GTS identifiers are semantically meaningful, incorporating vendor, package, namespace, and version information directly into the ID. This makes them instantly comprehensible to developers, architects, and automated systems for logging, tracing, and debugging.

**Vendor and Domain Agnostic**: By supporting explicit vendor registration, GTS facilitates safe, cross-vendor data exchange (e.g., in event buses or plugin systems) while preventing naming collisions and ensuring the origin of a definition is clear.

### 1.2 Enforcing Type Safety and Extensibility

**Explicit Type/Instance Distinction**: The GTS naming format clearly separates a GTS Type from a concrete GTS Instance, enabling unambiguous type resolution and validation.

**Inheritance and Conformance Lineage**: The chained identifier system provides a robust, first-class mechanism for expressing type derivation and instance conformance. This is critical for ecosystems where third-parties must safely extend core types while guaranteeing compatibility with the base schema.

**Built-in Version Compatibility**: By adopting a constrained Semantic Versioning model, GTS inherently supports automated compatibility checking across minor versions. This simplifies data casting (upcast/downcast), allowing consumers to safely process data from newer schema versions without breaking.

### 1.3 Simplifying Policy and Tooling

**Granular Access Control**: The structured nature of the identifier enables the creation of coarse-grained access control policies using wildcard matching (e.g., granting a service permission to process all events from a specific vendor/package: gts.myvendor.accounting.*).

**Deterministic Opaque IDs**: GTS supports the deterministic derivation of UUIDs (v5), providing a stable, fixed-length key for database indexing and external system APIs where human-readability is not required, while maintaining a clear, auditable link back to the source type.

**Specification-First**: As a language- and format-agnostic specification (though prioritizing JSON/JSON Schema), GTS provides a stable foundation upon which robust, interchangeable validation and parsing tools can be built across any ecosystem.


## 2. Identifier Format

GTS identifiers name either a GTS Type or a GTS Instance. A single GTS identifier may also chain multiple identifiers to express inheritance/compatibility and an instance’s conformance lineage.

The GTS identifier is a string with total length of 1024 characters maximum.

### 2.1 Canonical form

- A single GTS Type Identifier:
  - `gts.<vendor>.<package>.<namespace>.<type>.v<MAJOR>[.<MINOR>]~`
  - Note the trailing `~` to denote a GTS Type Identifier.
- A single GTS Instance Identifier (object of given type):
  - Well-known instance: `gts.<vendor>.<package>.<namespace>.<type>.v<MAJOR>[.<MINOR>]~<vendor>.<package>.<namespace>.<type>.v<MAJOR>[.<MINOR>]`
  - Combined anonymous instance: `gts.<vendor>.<package>.<namespace>.<type>.v<MAJOR>[.<MINOR>]~<UUID>`
  - Well-known and combined anonymous instance identifiers MUST include a left-hand type segment in a chain (see 2.2 and 3.7).
  - Combined anonymous instance identifiers MUST include a UUID tail.
  - Note: no trailing `~` for instances. 

The `<vendor>` refers to a string code that indicates the origin of a given schema or instance definition. This can be valuable in systems that support cross-vendor data exchange, such as events or configuration files, especially in environments with deployable applications or plugins.

The `<package>` notation defines a module, plugin, or application provided by the vendor that contains the specified GTS definition.

The `<namespace>` specifies a category of GTS definitions within the package, and finally, the `<type>` defines the specific object type.

Segments must be lowercase ASCII letters, digits, and underscores; they must start with a letter or underscore: `[a-z_][a-z0-9_]*`. The single underscore `_` is reserved as a placeholder and may only be used for the `<namespace>` segment.

The `<vendor>`, `<package>`, `<namespace>`, and `<type>` segment tokens must not start with a digit.

Versioning uses semantic versioning constrained to major and optional minor: `v<MAJOR>[.<MINOR>]` where `<MAJOR>` and `<MINOR>` are non-negative integers, for example:
- `gts.x.core.events.type.v1~` - defines a base event type in the system
- `gts.x.core.events.type.v1.2~` - defines a specific edition v1.2 of the base event type

The `<UUID>` is a 128-bit identifier (e.g., a UUID v5) that is used to identify a specific anonymous instance of a type. It is generated using a deterministic algorithm based on the type identifier and the instance data.

**Examples** - The GTS identifier can be used for instance or type identifiers:
```bash
gts.x.idp.users.user.v1.0~ # defines ID of a schema of the user objects provided by vendor 'x' in scope of the package 'idp'
gts.x.mq.events.topic.v1~ # defines ID of a schema of the MQ topic stream provided by vendor 'x' in scope of the 'mq' (message queue) package

```

### 2.2 Chained identifiers

Multiple GTS identifiers can be chained with `~` to express derivation and conformance. The chain follows **left-to-right inheritance** semantics:

- Pattern: `gts.<segment1>~<segment2>~<segment3>`
- Where **<segment>** is a single GTS identifier segment: `<vendor>.<package>.<namespace>.<type>.v<MAJOR>[.<MINOR>]`
  - `<segment1>` is a **base type** (GTS Type Identifier ending with `~`)
  - `<segment2>` is a **derived/refined type** (GTS Type Identifier ending with `~`) that extends `<segment1>` with additional constraints or implementation-specific details. It MUST be compatible with `<segment1>`.
  - `<segment3>` is a **GTS Instance Identifier** (no trailing `~`) that conforms to `<segment2>`. By transitivity, it also conforms to `<segment1>`.

**Important:** Each type in the chain inherits from its immediate predecessor (left neighbor) and MUST maintain compatibility.

**Chaining rules:**
1. All elements except the rightmost MUST be type identifiers (conceptually ending with `~`).
2. The rightmost element determines the identifier's nature:
   - Ends with `~` → the whole identifier represents a **GTS Type**.
   - No trailing `~` → the whole identifier represents a **GTS Instance**.
3. The `gts.` prefix appears **only once** at the very beginning of the identifier string.
4. Segments after the first are considered relative identifiers and do not repeat the `gts.` prefix. (e.g., `gts.x.some.base.type.v1~vendor.app.some.derived.v1~`).
5. Use `_` as a placeholder when the namespace is not applicable

**Examples with explanations:**

``` bash
# Base type only (standalone schema)
gts.x.core.events.type.v1~

# Type `ven.app._.custom_event.v1` derives from base type `gts.x.core.events.type.v1`. Both are schemas (trailing `~`).
gts.x.core.events.type.v1~ven.app._.custom_event.v1~

# Instance `ven.app._.custom_event_topic.v1.2` (no trailing `~`) conforms to type `gts.x.core.events.topic.v1`. The identifier shows the full inheritance chain.
gts.x.core.events.topic.v1~ven.app._.custom_event_topic.v1.2
```

### 2.3 Formal Grammar (EBNF)

The complete GTS identifier syntax in Extended Backus-Naur Form (EBNF):

```ebnf
(* Top-level identifier *)
gts-identifier = "gts." , gts-segment , ( chain-suffix-type | chain-suffix-instance | chain-suffix-anon-instance ) ;

(* Chained type ID ends with ~ *)
chain-suffix-type      = { "~" , gts-segment } , "~" ;

(* Chained instance ID MUST have at least one tilde separator and NO trailing tilde *)
chain-suffix-instance  = "~" , gts-segment , { "~" , gts-segment } ;

(* Combined anonymous instance ID ends with a UUID tail and NO trailing tilde *)
chain-suffix-anon-instance = { "~" , gts-segment } , "~" , uuid ;

(* Single GTS ID segment *)
gts-segment    = vendor , "." , package , "." , namespace , "." , type , "." , version ;

vendor         = segment ;
package        = segment ;
namespace      = segment ;
type           = segment ;

(* Segment: lowercase letters, digits, underscores; starts with letter or underscore *)
segment        = ( letter | "_" ) , { letter | digit | "_" } ;

(* Version: major.minor or major only *)
version        = "v" , major , [ "." , minor ] ;
major          = "0" | positive-integer ;
minor          = "0" | positive-integer ;

(* Primitives *)
positive-integer = non-zero-digit , { digit } ;
letter           = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j"
                 | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t"
                 | "u" | "v" | "w" | "x" | "y" | "z" ;
digit            = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
non-zero-digit   = "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;

(* UUID tail for combined anonymous instance identifiers *)
hex-digit        = digit | "a" | "b" | "c" | "d" | "e" | "f" ;
uuid             = 8hex , "-" , 4hex , "-" , 4hex , "-" , 4hex , "-" , 12hex ;
8hex             = hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit ;
4hex             = hex-digit , hex-digit , hex-digit , hex-digit ;
12hex            = hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit , hex-digit ;
```

**Grammar notes:**

1. **Type vs Instance distinction**: A GTS identifier ending with `~` (final-tilde present) denotes a GTS Type. Without the trailing `~`, it denotes a GTS Instance.

2. **Chain interpretation**: In a chained identifier `gts.<gts-segment1>~<gts-segment2>~<gts-segment3>`, each `~` acts as a separator. All segments before the final segment MUST be types (conceptually ending with `~`). The final segment determines whether the entire identifier is a type or instance.

3. **Combined anonymous instance**: In a chained identifier of the form `gts.<gts-segment1>~...~<uuid>`, the UUID is the instance identifier tail. All segments before the UUID MUST be types (conceptually ending with `~`).

4. **Placeholder rule**: Use `_` (underscore) as a segment value when the namespace is not applicable. It is recommended to use the placeholder only for the `<namespace>` segment.

5. **Normalization**: GTS identifiers must be lowercase. Leading/trailing whitespace is not permitted. Canonical form has no optional spacing.

6. **Reserved prefix**: The `gts.` prefix is mandatory and reserved. Future versions may introduce alternative prefixes but will maintain backward compatibility.


## 3. Semantics and Capabilities

GTS identifiers enable the following operations and use cases:

### 3.1 Core Operations

1. **Global Identification**: Uniquely identify data types (JSON Schemas) and data instances (JSON objects) in a human-readable format across systems and vendors.

2. **Schema Resolution and Validation**:
   - For a type identifier (ending with `~`): resolve to the JSON Schema definition
   - For an instance identifier: extract the rightmost type from the chain and validate the object against that schema
   - Chain validation: optionally verify that each type in the chain is compatible with its predecessor

#### Validation semantics for GTS chained IDs (instance -> schema and schema -> schema)

GTS identifiers may be chained (e.g. `gts.A~B~C`). Validation MUST respect the left-to-right inheritance model and MUST preserve the compatibility guarantee (section 3.2).

- **Instance → schema validation** (validate an object instance):
  - The system MUST resolve the **rightmost type** in the identifier chain and validate the instance payload against that JSON Schema.
  - If the instance identifier includes a type chain (`A~B~<instance>`), validating against the rightmost type `B` MUST also imply conformance to all base types in the chain (by transitivity).
  - Implementations MAY additionally validate that each adjacent type pair in the chain is compatible (schema→schema validation), but the primary runtime instance validation target is always the rightmost type.

- **Schema → schema validation** (validate a derived schema against its predecessor schema):
  - Given a derived type identifier chain (e.g. `A~B~` or `A~B~C~`), the system MUST validate that each derived schema is compatible with its immediate predecessor in the chain.
  - The compatibility rule is: every valid instance of the derived schema MUST also be a valid instance of the base schema.
  - When JSON Schema inheritance is expressed via `allOf` (recommended), the derived schema MUST be written such that it does not invalidate the compatibility guarantee.

- **`additionalProperties` and adding new properties**:
  - If a base schema (or any schema in the inheritance chain) defines an object with `additionalProperties: false`, then derived schemas MUST NOT introduce new properties at that object level that would be rejected by the base schema.
  - Derived schemas MAY still tighten constraints of existing properties (e.g. reduce `maxLength`, narrow `enum`, increase `minimum`) and MAY further specify previously-open nested objects (e.g. base `payload: {"type":"object"}` and derived defines `payload.properties`).

3. **Version Compatibility Checking**: Automatically determine if schemas with different MINOR versions are compatible (see section 4).

4. **Access Control Policies**: Build fine-grained or coarse-grained authorization rules using:
   - Exact identifier matching
   - Wildcard patterns (e.g., `gts.vendor.package.*`)
   - Chain-based isolation (e.g., restrict access to specific vendor's extensions)
   - See also ABAC use-cases in sections 3.3 and 3.4 below

5. **Extensible Type Systems**: Enable platforms where:
   - Base system types are defined by a core vendor
   - Third-party vendors extend base types with additional constraints
   - All validation guarantees are preserved through the inheritance chain
   - Type evolution is tracked explicitly through versioning

### 3.2 GTS Types Inheritance

GTS chained identifiers express type derivation through **left-to-right inheritance**. In a chain like `gts.A~B~C`:

- Type `B` extends type `A` by adding constraints or refining field definitions
- Type `C` further extends type `B` in the same manner
- Each derived type MUST be **fully compatible** with its predecessor (see section 4.3)

**Compatibility guarantee**: Every valid instance of a derived type is also a valid instance of all its base types in the chain. This means:
- An instance conforming to `C` also conforms to `B` and `A`
- Validation against the rightmost type automatically ensures conformance to all base types
- Derived types can only add optional fields (in open models), tighten constraints, or provide more specific definitions—never break base type contracts

This inheritance model enables safe extensibility: third-party vendors can extend platform base types while maintaining full compatibility with the core system.

**Schema modifiers**: Schemas may optionally declare `"x-gts-final": true` to prohibit further derivation, or `"x-gts-abstract": true` to require that instances use a concrete derived type rather than the base type directly. See section 9.11 for full semantics.

**Implementation pattern: Hybrid storage for extensible schemas**

GTS types inheritance enables a powerful database design pattern that combines **structured storage** for base type fields with **flexible JSON storage** for derived type extensions. This approach provides:

- **Query performance**: Index and query base type fields using native database types
- **Extensibility**: Store vendor-specific extensions as JSON/JSONB without schema migrations
- **Type safety**: Validate all data against registered GTS schemas before storage
- **Multi-tenancy**: Support multiple vendors extending the same base type in a single table

**Example: Event Management Platform**

A platform defines a base event schema with common fields:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "typeId": { "type": "string" },
    "occurredAt": { "type": "string", "format": "date-time" },
    "payload": { "type": "object", "additionalProperties": true }
  },
  "required": ["id", "typeId", "occurredAt", "payload"]
}
```

A third-party vendor (ABC) registers a derived event type for order placement:

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~abc.events.order_placed.v1~", // define a new event type derived from the base event type
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" }, // inherit base event schema
    {
      "properties": {
        "typeId": { "const": "gts.x.core.events.type.v1~abc.orders.order_placed.v1~" },
        "payload": {
          "type": "object",
          "properties": { // define the payload structure specific for this new event type
            "orderId": { "type": "string" },
            "customerId": { "type": "string" },
            "totalAmount": { "type": "number" },
            "items": { "type": "array", "items": { "type": "object" } }
          },
          "required": ["orderId", "customerId", "totalAmount", "items"],
          "additionalProperties": false
        }
      }
    }
  ]
}
```

The platform stores all events in a single table using hybrid storage:

```sql
CREATE TABLE events (
    id VARCHAR(255) PRIMARY KEY,     -- Indexed for fast event fetch by ID
    type_id VARCHAR(255) NOT NULL,   -- Indexed for filtering by event type
    occurred_at TIMESTAMP NOT NULL,  -- Indexed for time-range queries
    payload JSONB NOT NULL,          -- Vendor-specific extensions stored as JSON
    INDEX idx_type_occurred (type_id, occurred_at)
);
```

**Benefits of this approach:**

1. **No schema migrations**: New event types are registered via GTS schemas, not database DDL
2. **Efficient queries**: Filter by `type_id` or `occurred_at` using indexes, then parse `payload` only for matching rows
3. **Vendor isolation**: Use `type_id` patterns (e.g., `gts.x.core.events.type.v1~abc.*`) for access control (see 3.5)
4. **Full validation**: All events are validated against their registered GTS schema before insertion, ensuring data quality despite flexible storage


### 3.2.1 Top-level composition rules for GTS Type Schemas

GTS Type Schemas use JSON Schema composition (`allOf`) to express type derivation. To keep validators, linters, and codegen tooling simple, and to give authors one obvious place to declare each kind of constraint, the spec requires a **single canonical form** at the top level. The full rationale and rejected alternatives are recorded in [ADR-0002](./adr/0002-strict-allof-derivation-form.md).

**Terminology used in this subsection:**

- **Base GTS Type Schema** — a GTS Type Schema whose `$id` chain has exactly **one** segment, ending in `~` (e.g., `gts://gts.x.core.events.type.v1~`).
- **Derived GTS Type Schema** — a GTS Type Schema whose `$id` chain has **two or more** segments separated by `~`, still ending in `~` (e.g., `gts://A~B~` or `gts://A~B~C~`).

Both are *type* identifiers — both end in `~`. Instance identifiers (no trailing `~`) are not GTS Type Schemas and are not addressed by this subsection.

#### Rules for derived schemas

1. **`allOf` is required.** A derived GTS Type Schema MUST contain an `allOf` keyword at its top level.
2. **`allOf` contains exactly one subschema.** That subschema MUST be `{"$ref": "gts://<P>"}`, where `<P>` is the **immediate** parent in the chained `$id`. The `$ref` value MUST be an exact string-prefix match against `$id` (for `$id = gts://A~B~C~` the `$ref` MUST be `gts://A~B~`). Skip-level `$ref`s (e.g., `gts://A~` from `$id = gts://A~B~C~`) and `$ref`s to types outside the `$id` chain are invalid.
3. **Overlay at top level.** Every constraint the derived schema contributes — `type`, `properties`, `required`, narrowed constraints, `additionalProperties`, `x-gts-traits-schema`, `x-gts-traits`, `x-gts-final`, `x-gts-abstract`, and any other keyword — MUST appear at the top level of the schema, alongside `allOf`. The overlay MUST NOT be nested inside `allOf` as a second item.
4. **No top-level union or negation.** `anyOf`, `oneOf`, and `not` MUST NOT appear at the top level of a derived GTS Type Schema.

Forms that violate any of (1)–(4) are invalid GTS Type Schemas; registries and `/validate-type-schema` MUST reject them.

#### Rules for base schemas

5. **No `allOf`-based derivation.** A base GTS Type Schema does not inherit from anything and MUST NOT use `allOf` to express derivation. (Local `allOf` inside a property subschema, used for purely structural composition unrelated to GTS derivation, remains permitted — see rule 7.)
6. **No top-level union or negation.** `anyOf`, `oneOf`, and `not` MUST NOT appear at the top level of a base GTS Type Schema either. The restriction is uniform with rule (4).

#### Nested sub-schemas are unrestricted

7. Inside `properties`, `definitions`, `items`, and any other nested context, `allOf`, `anyOf`, `oneOf`, and `not` remain valid Draft-07 constructs. Union types, discriminator patterns, and conditional sub-shapes are all still expressible — the restriction is purely top-level.

#### Canonical example

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
        "orderId":     { "type": "string" },
        "totalAmount": { "type": "number" }
      },
      "required": ["orderId", "totalAmount"]
    }
  }
}
```

#### Invalid forms (rejected at registration)

- `allOf` with two items (overlay inside `allOf` — the legacy "Form B"):
  ```jsonc
  { "$id": "gts://A~B~",
    "allOf": [ { "$ref": "gts://A~" }, { "properties": { /* ... */ } } ] }
  ```
- `allOf` with three or more items.
- `allOf` whose only item is an inline overlay (no `$ref` to the parent).
- `allOf` with multiple `$ref` items (attempting multi-parent inheritance).
- A **hybrid** schema that declares overlay constraints BOTH at the top level AND inside `allOf` as a second item. Under JSON Schema this is well-defined (all three subschemas combine via implicit AND), but the structure is opaque and the spec rejects it via rule (2) — `allOf` must contain exactly one subschema:
  ```jsonc
  { "$id": "gts://A~B~",
    "allOf": [ { "$ref": "gts://A~" }, { "properties": { "x": { /* ... */ } } } ],
    "properties": { "y": { /* ... */ } } }
  ```
- `$ref` that does not match the immediate parent — e.g., `$id = gts://A~B~C~` with `$ref = gts://A~` (skip-level), or `$ref` pointing to a type outside the chain.
- Top-level `anyOf`, `oneOf`, or `not`.
- A base schema (single-segment `$id`) declaring `allOf` for derivation, or declaring top-level `anyOf`/`oneOf`/`not`.

OP#12 (Type Derivation Validation, §9.2) enforces these structural rules in addition to its existing constraint-compatibility checks.

### 3.3 Query Language

GTS Query Language is a compact predicate syntax, inspired by XPath/JSONPath, that lets you constrain results by attributes. Attach a square-bracketed clause to a GTS identifier containing name="value" pairs separated by commas. Example form: <gts>[ attr="value", other="value2" ].

> **Scope note:** The query language and attribute selector (section 3.4) are runtime conveniences for filtering and accessing data in GTS-aware applications. They are **not part of the core GTS identifier specification** and should not be embedded in stored identifiers or schema definitions. Use them only in runtime queries, policy evaluation, and data access operations.

Predicates can reference plain literals or GTS-formatted values, e.g.:

```bash
# filter all events that are published to the topic "some_topic" by the vendor "z"
gts.x.core.events.type.v1~[type_id="gts.x.core.events.topic.v1~z.app._.some_topic.v1~"]
# filter all user settings that were defined for users if type is z-vendor app_admin
gts.x.core.acm.user_setting.v1~[user_type="gts.x.core.acm.user.v1~z.app._.app_admin.v1~"]
```

Multiple parameters are combined with logical AND to further restrict the result set:

```bash
gts.x.y.z.type.v1~[foo="bar", id="ef275d2b-9f21-4856-8c3b-5b5445dba17d"]
```

### 3.4 Attribute selector

GTS includes a lightweight attribute accessor, akin to JSONPath dot notation, to read a single value from a bound instance. Append `@` to the identifier and provide a property path, e.g., <gts>@<root>.<nested>.

The selector always resolves from the instance root and returns one attribute per query. For example:

```bash
# refer to the value of the message identifier
gts.x.y.z.message.v1@id
```

Nested attributes also can be accessed within the instance's structure. For example:
```bash
# refer to the value of the 'bar' item property from the 'foo' field
gts.x.y.z.message.v1.0@foo.bar
```

### 3.5 Access control with wildcards

Wildcards (`*`) enable policy scopes that cover families of identifiers (e.g., entire vendor/package trees) rather than single, exact instance or schema IDs. This is useful in RBAC/ABAC style engines and relationship-based systems (e.g., Zanzibar-like models) where permissions are expressed over sets of resources.

```bash
# grants access to all the audit events category defined by the vendor 'xyz'
gts.x.core.events.type.v1~x.core._.audit_event.v1~xyz.*
# grants access to all the menu items referring screens of the vendor 'abc'
gts.x.ui.left_menu.menu_item.v1[screen_type="gts.x.ui.core_ui.screens.v1~abc.*"]
```

### 3.6 Access Control Implementation Notes

> **Scope disclaimer:** GTS-based access control implementation is outside the scope of this specification and will vary across systems. GTS provides the syntax to express authorization rules; however, different policy engines may apply different evaluation strategies or may not support attribute-based or wildcard-based access control at all.

The following guidance is provided for implementers building GTS-aware policy engines:

**Policy management domain model:**
- **Principal**: Users, services, or groups (outside the scope of GTS) mapped to roles.
- **Resource**: GTS identifiers or patterns (with wildcards and, optionally, attribute predicates) that denote types or instances.
- **Action**: Verbs such as `read`, `write`, `emit`, `subscribe`, `admin` defined by the platform.

**Example policy shapes:**
- **RBAC-style allow**: Role `xyz_auditor` → allow `read` on `gts.x.core.events.type.v1~x.core._.audit_event.v1~xyz.*`
- **ABAC refinement**: Attach predicate filters like `[screen_type="..."]` to restrict by referenced type.
- **Derived-type envelopes**: Grant access at the base type (e.g., `gts.x.core.events.type.v1~`) so that derived schemas remain covered if they conform by chain rules.

**Matching semantics options:**
- **Implicit derived-type coverage (recommended)**: Granting access to a base GTS Type Identifier without an explicit wildcard (e.g., `gts.a.b.c.d.v1~`) SHOULD be treated as an implicit grant to all derived types and instances under that base type (equivalent in intent to `gts.a.b.c.d.v1~*`).

  Example candidate: `gts.a.b.c.d.v1~w.x.y.z.v1`

  This candidate SHOULD match all of:
  - `gts.a.b.c.d.v1~`
  - `gts.a.b.c.d.v1~*`
  - `gts.a.b.c.d.v1~w.*`

  But it SHOULD NOT match:
  - `gts.a.b.c.d.v1~x.*`
- **Segment-wise prefixing**: The `*` wildcard can match any valid content of the target segment and its suffix hierarchy, enabling vendor/package/namespace/type grouping.
- **Chain awareness**: Patterns may target the base segment, derived segments, or instance tail; evaluation should consider the entire chain when present.
- **Attribute filters**: Optional `[name="value", ...]` predicates further constrain matches (e.g., only instances referencing a specific `name`).
- **Minor version semantics**: Patterns without minor versions (e.g., `gts.vendor.pkg.ns.type.v1~*`) match candidates with any minor version of that major version (e.g., `v1.0~`, `v1.1~`), since the minor version is optional and omitting it means "any minor version". See section 10 for detailed examples.

**Evaluation guidelines:**
- **Deny-over-allow (recommended)**: If your engine supports explicit denies, process them before allows to prevent privilege escalation.
- **Most-specific wins**: Prefer the most specific matching rule (longest concrete prefix, fewest wildcards, most predicates).
- **Version safety**: Consider pinning MAJOR and, optionally, MINOR versions in sensitive paths; otherwise rely on minor-version compatibility guarantees (see section 4).
- **Tenant isolation**: Use vendor/package scoping to isolate tenants and applications; avoid cross-vendor wildcards unless explicitly required.

**Performance guidelines:**
- **Indexing**: Normalize and index rules by canonical GTS prefix to avoid expensive pattern-matching scans.
- **Caching**: Cache resolution results for common patterns and predicate evaluations; invalidate caches on schema or policy changes.
- **Auditing**: Log the concrete identifier and the matched rule (pattern + predicates) for traceability and compliance.

### 3.7 Well-known and Anonymous Instances

In GTS, a **GTS Type is always named**: it has a stable **GTS Type Identifier** (ends with `~`) and can be referenced from a JSON Schema `$id`.

However, a **GTS Instance** may be represented in two common ways:

- **Well-known instance (named)**: used for unique, globally-defined objects that benefit from a stable human-readable name (catalog entries, topics/streams, modules, capabilities, etc.).
  - **Mandatory**: well-known GTS Instance Identifiers MUST be expressed as a **chain** where the left segment is the type and the rightmost segment is the instance name. Single-segment instance identifiers (without a left-hand type segment) are prohibited.
  - Example (well-known topic/stream instance):
    - `gts.x.core.events.topic.v1~x.commerce._.orders.v1.0`
  - Field naming: typically `id` (alternatives: `gtsId`, `gts_id`).

Example:

```json
{
  "id": "gts.x.core.events.topic.v1~x.commerce._.orders.v1.0",
  "name": "orders",
  "description": "Order lifecycle events topic"
}
```

- **Anonymous instance**: used for runtime-created objects where a globally meaningful name is not required (events/messages, DB rows, audit records, etc.).
  - Recommended: use an opaque identifier as `id` (typically a UUID) and store the associated **GTS Type Identifier** separately (e.g., in a `type` field).
  - Example (anonymous event instance):
    - `id: "7a1d2f34-5678-49ab-9012-abcdef123456"`, `type: "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~"`
  - Field naming: `type` (alternatives: `gtsType`, `gts_type`).

  Some services may also support a **combined** anonymous instance representation:
  - `id: "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~7a1d2f34-5678-49ab-9012-abcdef123456"`
  - In this case, the explicit `type` field MAY be omitted, since the GTS Type Identifier can be derived from the `id` prefix up to the final `~`.

**Note:** A type marked with `"x-gts-abstract": true` cannot have direct instances (well-known or anonymous). Instances must reference a concrete (non-abstract) derived type as the rightmost type in the chain. See section 9.11.

This split is common in event systems: **topics/streams** are often well-known instances, while individual **events** are anonymous. See `./examples/events` and the field-level recommendations in section **9.1**.

Example:

```json
{
  "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
  "type": "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~",
  "occurredAt": "2025-09-20T18:35:00Z"
}
```

## 4. GTS Identifier Versions Compatibility

GTS uses semantic versioning with MAJOR and optional MINOR components. This section covers two distinct compatibility concepts:

**1. Type Derivation Compatibility** (via chaining): A derived type like `gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~` must be **always fully compatible** with its base type `gts.x.core.events.type.v1~`. Derived types refine base types by adding constraints or specifying fields left open (e.g., `payload` as `object` with `additionalProperties: true`).

**2. Minor Version Compatibility** (same type, different versions): When evolving a single type across minor versions (e.g., `v1.0` → `v1.1` → `v1.2`), compatibility depends on the chosen strategy:

- **MAJOR version increments** (v1 → v2): Always indicate breaking changes
- **MINOR version increments** (v1.0 → v1.1): Must maintain compatibility according to one of three strategies: backward, forward, or full compatibility

The compatibility mode for minor version evolution is **implementation-defined** and can vary depending on system component implementing the API or DB storage, namespace or use case. For example:
- Event schemas might use **forward compatibility** (old consumers can read new events)
- API request payloads might use **backward compatibility** (new servers can process old requests)
- Configuration schemas might require **full compatibility** (any version can read any other)

### 4.1 Compatibility Modes

Before we dig deeper into the GTS versions compatibility, let's first define the different compatibility modes:

**Backward Compatibility**: A consumer with the **new schema** can process data produced with an **old schema**.
- **Use case**: Consumers are updated after producers (e.g., API clients updated before servers).
- **Guarantee**: New code can read old data.

**Forward Compatibility**: A consumer with the **old schema** can process data produced with a **new schema**.
- **Use case**: Producers are updated before consumers, or to support rollback scenarios.
- **Guarantee**: Old code can read new data.

**Full Compatibility**: Changes are both backward and forward compatible.
- **Use case**: Producers and consumers can be deployed in any order.
- **Guarantee**: Maximum safety but most restrictive evolution path.

> **Implementation note**: The exact compatibility mode is implementation-defined and outside the scope of this specification. Systems may enforce different modes for different identifier namespaces

### 4.2 JSON Schema Content Models

Understanding `additionalProperties` is critical for compatibility:

- **Open content model**: `additionalProperties` is `true` or not specified. The schema accepts fields not explicitly defined.
- **Closed content model**: `additionalProperties` is `false`. The schema rejects any fields not explicitly defined.

These models affect which changes are safe:
- Adding a field to a **closed** model is backward compatible (old data has no extra fields; new consumers handle absence).
- Adding/removing optional fields in an **open** model is fully compatible (open consumers accept any fields; optional fields can be absent).

### 4.3 Compatibility Rules for GTS Type Schemas

The table below shows which schema changes between minor versions of the same type are safe for each compatibility mode.

> NOTE: The table below illustrates the compatibility rules for GTS Type Schemas of the same type, but different versions. The derived types are always fully compatible with the base type.

| Change | Backward | Forward | Full | Notes |
|--------|----------|---------|------|-------|
| **Adding optional property (open model)** | ✅ Yes | ✅ Yes | ✅ Yes | Old consumers ignore new fields (open model accepts any fields). New consumers handle absence of optional field. |
| **Removing optional property (open model)** | ✅ Yes | ✅ Yes | ✅ Yes | New consumers ignore the removed field in old data (open model accepts any fields). Old consumers handle absence of optional field. |
| **Updating description/examples** | ✅ Yes | ✅ Yes | ✅ Yes | Documentation changes don't affect validation. |
| **Updating minor version of referenced GTS types** | ✅ Yes | ✅ Yes | ✅ Yes | Assumes referenced types follow same compatibility rules. |
| **Adding optional property (closed model)** | ✅ Yes | ❌ No | ❌ No | Old data lacks the field; new consumers handle absence. Old consumers reject new data with extra fields. |
| **Changing required property to optional** | ✅ Yes | ❌ No | ❌ No | New consumers handle absence. Old data always provides it. |
| **Removing enum value** | ✅ Yes | ❌ No | ❌ No | New consumers handle remaining values. Old data may use removed value. |
| **Widening numeric type (int → number)** | ✅ Yes | ❌ No | ❌ No | Old data (integers) is subset of new type. Old consumers may not handle floats. |
| **Relaxing constraints (e.g., increasing max)** | ✅ Yes | ❌ No | ❌ No | Old data satisfies looser constraints. Old consumers reject values outside old limits. |
| **Removing optional property (closed model)** | ❌ No | ✅ Yes | ❌ No | Old consumers expect the field may be absent. New data won't have it. |
| **Changing optional property to required** | ❌ No | ✅ Yes | ❌ No | Old consumers don't expect it to be required. New data always provides it. |
| **Adding new enum value** | ❌ No | ✅ Yes | ❌ No | Old data uses existing values. New consumers handle new values. Old consumers reject unknown values. |
| **Narrowing numeric type (number → int)** | ❌ No | ✅ Yes | ❌ No | New consumers accept integers only. Old data may contain floats. |
| **Tightening constraints (e.g., decreasing max)** | ❌ No | ✅ Yes | ❌ No | New consumers enforce stricter rules. Old data may violate new constraints. |
| **Adding new required property** | ❌ No | ❌ No | ❌ No | Breaking change: old data lacks the field, new consumers require it. |
| **Removing required property** | ❌ No | ❌ No | ❌ No | Breaking change: old data has the field, new consumers don't expect it. |
| **Renaming property** | ❌ No | ❌ No | ❌ No | Breaking change: equivalent to remove + add. |
| **Changing property type (incompatible)** | ❌ No | ❌ No | ❌ No | Breaking change unless using union types. |


### 4.4 GTS Versions Compatibility Examples

This section demonstrates how different types of schema changes affect compatibility between minor versions of the same GTS type. We take as example Event Management system and typical events structure, however it can be used for any other data schemas in the system

#### 4.4.1 Forward Compatibility Example

**Use case**: Configuration schemas where old systems must tolerate new config options.

**Schema v1.0** (`gts.x.core.db.connection_config.v1.0~`):
```json
{
  "$id": "gts://gts.x.core.db.connection_config.v1.0~",
  "type": "object",
  "required": ["host", "port", "database"],
  "properties": {
    "host": { "type": "string" },
    "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
    "database": { "type": "string" },
    "timeout": { "type": "integer", "minimum": 1, "default": 30 }
  },
  "additionalProperties": false
}
```

**Schema v1.1** (adds required field):
```json
{
  "$id": "gts://gts.x.core.db.connection_config.v1.1~",
  "type": "object",
  "required": ["host", "port", "database", "timeout"],
  "properties": {
    "host": { "type": "string" },
    "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
    "database": { "type": "string" },
    "timeout": { "type": "integer", "minimum": 1 }
  },
  "additionalProperties": false
}
```

**Compatibility analysis**:
- ✅ **Forward**: v1.0 consumer can read v1.1 data (`timeout` is optional in v1.0 with default value)
- ❌ **Backward**: v1.1 consumer **rejects** v1.0 data (missing required `timeout`)
- ❌ **Full**: Not fully compatible

**Deployment strategy**: Update config producers to always include `timeout`, then update consumers to v1.1.

**Config examples**:
```json
// v1.0 config (rejected by v1.1 because timeout is now required)
{"host": "db.example.com", "port": 5432, "database": "mydb"}

// v1.1 config (valid for both schemas)
{"host": "db.example.com", "port": 5432, "database": "mydb", "timeout": 60}
```

#### 4.4.2 Backward Compatibility Example (Closed Model)

**Use case**: Event schemas where producers and consumers can be deployed independently.

**Base event schema v1** (`gts.x.core.events.type.v1~`)
```json
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "required": ["id", "type", "timestamp"],
  "properties": {
    "id": { "type": "string" },
    "type": { "type": "string" },
    "timestamp": { "type": "integer" },
    "payload": { "type": "object", "additionalProperties": true }
  },
  "additionalProperties": false
}
```

**Schema v1.0** (`gts.x.core.events.type.v1~x.api.users.create_request.v1.0~`):
```json
{
  "$id": "gts://gts.x.core.events.type.v1~x.api.users.create_request.v1.0~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    {
      "properties": {
        "payload": {
          "type": "object",
          "required": ["email", "name"],
          "properties": {
            "email": { "type": "string", "format": "email" },
            "name": { "type": "string" }
          },
          "additionalProperties": false
        }
      }
    }
  ]
}
```

**Schema v1.1** (adds optional field):
```json
{
  "$id": "gts://gts.x.core.events.type.v1~x.api.users.create_request.v1.1~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    {
      "properties": {
        "payload": {
          "type": "object",
          "required": ["email", "name"],
          "properties": {
            "email": { "type": "string", "format": "email" },
            "name": { "type": "string" },
            "phoneNumber": { "type": "string" }
          },
          "additionalProperties": false
        }
      }
    }
  ]
}
```

**Compatibility analysis**:
- ❌ **Forward**: v1.0 server **rejects** v1.1 requests (closed model with `additionalProperties: false` rejects unknown `phoneNumber`)
- ✅ **Backward**: v1.1 server can process v1.0 requests (missing `phoneNumber` is optional)
- ❌ **Full**: Not fully compatible

**Deployment strategy**: Update servers to v1.1 first, then gradually update clients.

**Request payload examples**:
```json
// v1.0 request payload (valid for both schemas)
{"email": "user@example.com", "name": "John Doe"}

// v1.1 request payload (rejected by v1.0 server due to additionalProperties: false)
{"email": "user@example.com", "name": "John Doe", "phoneNumber": "+1234567890"}
```

#### 4.4.3 Full Compatibility Example (Open Model)

**Schema v1.0** (`gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~`):
```json
{
  "$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    {
      "properties": {
        "payload": {
          "type": "object",
          "required": ["orderId", "customerId", "totalAmount"],
          "properties": {
            "orderId": { "type": "string" },
            "customerId": { "type": "string" },
            "totalAmount": { "type": "number" }
          },
          "additionalProperties": true
        }
      }
    }
  ]
}
```

**Schema v1.1** (adds optional field):
```json
{
  "$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.1~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    {
      "properties": {
        "payload": {
          "type": "object",
          "required": ["orderId", "customerId", "totalAmount"],
          "properties": {
            "orderId": { "type": "string" },
            "customerId": { "type": "string" },
            "totalAmount": { "type": "number" },
            "currency": { "type": "string", "default": "USD" }
          },
          "additionalProperties": true
        }
      }
    }
  ]
}
```

**Compatibility analysis**:
- ✅ **Backward**: v1.1 consumers can read v1.0 data (missing `currency` field is handled via default)
- ✅ **Forward**: v1.0 consumers can read v1.1 data (open model ignores unknown `currency` field)
- ✅ **Full**: Fully compatible—deploy in any order

**Event payload examples**:
```json
// v1.0 data (valid for both schemas)
{"orderId": "123", "customerId": "456", "totalAmount": 99.99}

// v1.1 data (valid for v1.1, readable by v1.0 due to open model)
{"orderId": "123", "customerId": "456", "totalAmount": 99.99, "currency": "EUR"}
```

> **Note**: Changes to referenced GTS identifier values do not affect full compatibility. For example, the following two schemas are treated as fully compatible even though they reference different const values:

```jsonc
{
  "$id": (
      "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.1~"
  ),
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "allOf": [
      {"$ref": "gts://gts.x.core.events.type.v1~"},
      {
          "type": "object",
          "required": ["type", "payload"],
          "properties": {
              "type": {
                  "const": (
                      "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.1~"
                  )
              },
          }
      }
  ]
}
```

```jsonc
{
  "$id": (
      "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.2~"
  ),
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "allOf": [
      {"$ref": "gts://gts.x.core.events.type.v1~"},
      {
          "type": "object",
          "required": ["type", "payload"],
          "properties": {
              "type": {
                  "const": (
                      "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.2~" // GTS ID changed to v1.2
                  )
              },
          }
      }
  ]
}
```


#### 4.4.4 Type Derivation vs Version Evolution

**Important distinction**: Type derivation (chaining) is different from version evolution:

```json
// Base type (always compatible with derived types)
"$id": "gts://gts.x.core.events.type.v1~"

// Derived type v1.0 (refines base type)
"$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~"

// Derived type v1.1 (minor version of the derived type)
"$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.1~"
```

**Compatibility rules**:
1. `order_placed.v1.0~` is **always fully compatible** with base `type.v1~` (derivation)
2. `order_placed.v1.1~` is **always fully compatible** with base `type.v1~` (derivation)
3. `order_placed.v1.1~` compatibility with `order_placed.v1.0~` depends on the changes made (version evolution—see examples above)

See the [examples folder](./examples/events/types/) for complete schema definitions demonstrating these patterns.


### 4.5 Best Practices for GTS Type Schema Evolution

To maximize compatibility and minimize breaking changes between the minor versions of the same GTS type, follow these recommendations:

1. **Make new properties optional with defaults**: This is the safest way to add fields. Use `default` keyword in JSON Schema.

2. **Never remove or rename required properties**: Always a breaking change. Increment MAJOR version instead.

3. **Deprecate instead of removing**: Mark fields as deprecated in documentation. Keep them in the schema for at least one MAJOR version.

4. **Avoid changing field types**: Type changes are almost always breaking. To evolve a type, use union types: `"type": ["string", "number"]`.

5. **Use a GTS Registry**: Centralize GTS Type management and enforce compatibility checks before allowing new versions to be published.


## 5. Typical Use-cases

### 5.1 Practical Benefits for Service and Platform Vendors

Besides being a universal identifier, GTS provides concrete, production-ready capabilities that solve common architectural challenges for platform vendors and service providers integrating multiple third-party services under single control plane:

#### Type Safety and Evolution
- **Automated compatibility checking**: Validate schema changes against backward/forward/full compatibility rules before deployment (see section 4.3)
- **Safe schema evolution**: Add optional fields to open models without breaking existing consumers or requiring coordinated deployments
- **Version casting**: Automatically upcast/downcast data between minor versions (e.g., process v1.2 data with v1.0 consumer)
- **Breaking change detection**: Prevent accidental breaking changes through automated validation in CI/CD pipelines

#### Multi-Vendor Extensibility
- **Plugin architectures**: Allow third-party vendors to extend platform base types while maintaining compatibility guarantees (see section 3.2)
- **Hybrid storage**: Store common fields in indexed columns, vendor-specific extensions in JSONB—no schema migrations needed (see section 3.2 implementation pattern)
- **Vendor isolation**: Use GTS chains to track data provenance and enforce vendors' data boundaries in shared databases
- **Zero-downtime extensions**: Register new derived types without altering existing tables or restarting services

#### Access Control and Security
- **Wildcard-based policies**: Grant object access permissions using patterns like `gts.vendor.package.*` instead of maintaining explicit lists (see section 3.5)
- **Attribute-based filtering**: Combine GTS identifiers with predicates for fine-grained access control (see section 3.3)
- **Chain-aware authorization**: Restrict access to specific vendor extensions while allowing base type access
- **Audit trails**: Log GTS identifiers for complete traceability of data access and schema usage

#### Developer Experience
- **Human-readable identifiers**: Debug issues by reading event types, config schemas, or API payloads directly from logs
- **Self-documenting APIs**: GTS identifiers encode vendor, package, namespace, and version—no external documentation lookup needed
- **GTS Type Registries**: Build centralized catalogs where GTS Types are indexed by GTS Type Identifiers for discovery and validation
- **Deterministic UUIDs**: Generate stable UUID v5 from GTS identifiers for external systems requiring opaque IDs. The UUID5 namespace is ns:URL + 'gts':

```python
import uuid
GTS_NS = uuid.uuid5(uuid.NAMESPACE_URL, "gts")
print(uuid.uuid5(GTS_NS, "gts.x.core.events.type.v1~"))
print(uuid.uuid5(GTS_NS, "gts.x.core.events.type.v1~abc.app._.custom_event.v1.2"))
```


### 5.2 Example: Multi-Vendor Event Management Platform

**Practical Scenario:**

Consider a vendor, `X`, who operates a multi-tenant event management platform. This platform acts as a broker, receiving events from various producers (e.g., third-party applications) and routing them to the correct handlers. According to the platform's specification, every event must contain a `gtsId` field that references a registered event schema. This allows the platform to validate, authorize, and route events of different kinds, such as general-purpose events, audit logs, and custom messages.

Now, imagine a second vendor, `ABC`, develops an application named `APP` that runs on vendor `X`'s platform. When a customer makes an online purchase within `APP`, the application needs to emit a `store.purchase_audit_event` to the event manager.

In this scenario, vendor `X`'s platform must be able to:
1.  **Authorize** the incoming event, ensuring that vendor `ABC` is permitted to emit it.
2.  **Validate** the event's structure against the correct schema.
3.  **Ensure data isolation**, making the event visible only to authorized parties (e.g., vendor `ABC`'s `APP` administrators) and not to other tenants.

Let's define the schemas required to implement this.

First, let's define the base event schema for vendor `X` event manager:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~",
  "title": "Base Event",
  "type": "object",
  "properties": {
    "id": { "type": "string", "$comment": "This field serves as the unique identifier for the event instance" },
    "type": { "type": "string", "$comment": "This field serves as the unique identifier for the event schema" },
    "timestamp": { "type": "integer", "$comment": "timestamp in seconds since epoch" },
    "payload": { "type": "object", "additionalProperties": true, "$comment": "Event payload... can be anything" }
  },
  "required": ["id", "type", "timestamp", "payload"],
  "additionalProperties": false
}
```

Now, let's define the audit event schema for vendor `X` event manager:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~x.core.audit.event.v1~",
  "title": "Audit Event, derived from Base Event",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    {
      "type": "object",
      "properties": {
        "payload": {
          "type": "object",
          "properties": {
            "user_id": { "type": "string", "$comment": "User ID" },
            "user_agent": { "type": "string", "$comment": "User agent" },
            "ip_address": { "type": "string", "$comment": "IP address" },
            "data": { "type": "object", "additionalProperties": true, "$comment": "Audit event custom data... can be anything" }
          },
          "required": ["user_id", "user_agent", "ip_address", "data"],
          "additionalProperties": false
        }
      },
      "required": ["payload"]
    }
  ]
}
```

Then, let's define the schema of specific audit event registered by vendor `ABC` application `APP`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~x.core.audit.event.v1~abc.app.store.purchase_audit_event.v1.2~",
  "title": "Vendor ABC Custom Purchase Audit Event from app APP",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~x.core.audit.event.v1~" },
    {
      "type": "object",
      "properties": {
        "payload": {
          "type": "object",
          "properties": {
            "data": {
              "type": "object",
              "properties": {
                "purchase_id": { "type": "string" },
                "amount": { "type": "number" },
                "currency": { "type": "string" },
                "price": { "type": "number" }
              },
              "required": ["purchase_id", "amount", "currency", "price"],
              "additionalProperties": false
            }
          }
        }
      },
      "required": ["payload"]
    }
  ]
}
```

Finally, when the producer (the application `APP` of vendor `ABC`) emits the event, it uses the `type` to identify the event schema and provide required payload:

```json
{
  "id": "e81307e5-5ee8-4c0a-8d1f-bd98a65c517e",
  "type": "gts.x.core.events.type.v1~x.core.audit.event.v1~abc.app.store.purchase_audit_event.v1.2~",
  "timestamp": 1743466200000000000,
  "payload": {
    "user_id": "9c905ae1-f0f3-4cfb-aa07-5d9a86219abe",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "ip_address": "127.0.0.1",
    "data": {
      "purchase_id": "cats_drinking_bowl_42",
      "amount": 2,
      "currency": "USD",
      "price": 19.95
    }
  }
}
```

When the event manager receives the event it processes it as follows:

1. **Schema Resolution**: Parse the `type` to identify the full chain. The event manager can see that this instance conforms to `gts.x.core.events.type.v1~`, `...~x.core.audit.event.v1~`, and finally `...~abc.app.store.purchase_audit_event.v1.2~`.

2. **Validation**: Load the most specific JSON Schema (`...~abc.app.store.purchase_audit_event.v1.2~`) and validate the event object against it. It would automatically mean the event body is validated against any other schema in the chain (e.g., the base event and the base audit event).

3. **Authorization**: Check if the producer is authorized to emit events matching the pattern `gts.x.core.events.type.v1~x.core.audit.event.v1~abc.app.*` or a broader pattern like `gts.x.core.events.type.v1~x.core.audit.event.v1~abc.*`.

4. **Routing & Auditing**: Use the chain to route events to appropriate handlers or storage if needed.

> **Note**: use the [GTS Kit](https://github.com/globaltypesystem/gts-kit) for visualization of the entities relationship and validation

See additional GTS examples in the [examples folder](./examples/):
- [Event Examples](./examples/events/) - Event-driven architecture with topic and event type definitions
- [Module Examples](./examples/modules/) - Modular system capabilities and plugins
- [MCP Examples](./examples/mcp/) - AI/LLM tool definitions using Model Context Protocol
- [TypeSpec VM Examples](./examples/typespec/vms/) - Virtual machine types across different platforms (VMWare, Nutanix, Virtuozzo) defined in TypeSpec format
- [YAML UI Examples](./examples/yaml/ui/) - User interface component definitions (menus, grids) in YAML format


### 5.3 GTS Registry Requirement

> **Critical implementation requirement:** The architectural guarantees of GTS—particularly type safety across inheritance chains and safe minor version evolution—depend entirely on a stateful **GTS Registry** component. Production systems MUST implement or integrate a registry capable of:
>
> 1. **Storing and indexing** all registered GTS Type Schemas by their GTS Type Identifiers
> 2. **Validating compatibility** of new GTS Type versions against existing versions using the precise rules defined in section 4.3 before publication
> 3. **Enforcing inheritance constraints** to ensure derived types remain compatible with their base types
> 4. **Rejecting incompatible changes** that violate the declared compatibility mode (backward/forward/full)
> 5. **Providing GTS Type resolution** for validation, casting, and relationship resolution operations
>
> Without a registry performing rigorous type compatibility validation (including schema diffing where applicable), the type safety guarantees of GTS cannot be maintained. Implementations should treat the registry as a critical infrastructure component, similar to a database or message broker.


## 6. Implementation-defined and Non-goals

This specification intentionally does not enforce lifecycle, operational or governance choices. It is up to the implementation vendor to define policies and behavior for:

1. Whether a defined type is exported (published) and available for cross-vendor use via APIs or an event bus.
2. Whether a given JSON/JSON Schema definition is mutable or immutable (e.g., handling an incompatible change without changing the minor or major version).
3. How to implement access policies and access checks based on the GTS query and attribute access languages.
4. When to introduce a new minor version versus a new major version.
5. GTS identifiers renaming and aliasing
6. Exact GTS identifier minor version compatibility rules enforcement (backward, forward, full)

> **Non-goals reminder**: GTS is not an eventing framework, transport, or workflow. It standardizes identifiers and basic validation/casting semantics around JSON and JSON Schema.


## 7. Comparison with other identifiers

- JSONSchema $schema url: While JSONSchema provides a robust framework for defining the structure of JSON data, GTS extends this by offering clear vendor, package and namespace notation and chaining making it easier to track and validate data instances across different systems and versions.
- UUID: Opaque and globally unique. GTS is meaningful to humans and machines; UUIDs can be derived from GTS deterministically when opaque IDs are required.
- Apple UTI: Human-readable, reverse-DNS-like. GTS is similar in readability but adds explicit versioning, vendors/apps support, chaining, and schema/instance distinction suitable for JSON Schema-based validation.
- Amazon ARN: Global and structured, but cloud-service-specific. GTS is vendor-neutral and domain-agnostic, focused on data schemas and instances.


## 8. Parsing and Validation

### 8.1 Single-segment regex (type or instance)

Single-chain variant:

```regex
^gts\.([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\.v(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?~?$
```

Verbose, named groups (Python `re.VERBOSE`):

```regex
^\s*
gts\.
(?P<vendor>[a-z_][a-z0-9_]*)\.
(?P<package>[a-z_][a-z0-9_]*)\.
(?P<namespace>[a-z_][a-z0-9_]*)\.
(?P<type>[a-z_][a-z0-9_]*)
\.v(?P<major>0|[1-9]\d*)
(?:\.(?P<minor>0|[1-9]\d*))?
(?P<is_type>~)?
\s*$
```

`is_type` captures the optional trailing `~` (present for type IDs, absent for instance IDs).

### 8.2 Chained identifier regex
 
 For chained identifiers, the pattern enforces that all segments except the final instance designator are type IDs (with `~` separators):
 
 ```regex
 ^\s*gts\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.v(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?(?:~[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.v(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?)*(?:~(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?)?\s*$
 ```

 **Pattern explanation:**
 - Starts with a single absolute segment (`gts.` prefix)
 - Followed by zero or more relative segments, each prefixed by `~`
 - The identifier may end with:
   - `~` (type)
   - a segment end (instance)
   - `~<uuid>` (combined anonymous instance)

 **Validation rules:**
 1. Standalone type identifier: MUST end with `~`
 2. In a chain, all elements before the final instance designator MUST be types (end with `~` in the original string).
    - For well-known instances, the final designator is the last `<vendor>.<package>.<namespace>.<type>.v...` segment (no trailing `~`).
    - For combined anonymous instances, the final designator is the UUID tail after the last `~`.
 3. Only the first segment uses the `gts.` prefix; chained segments are relative (no `gts.`)

 **Parsing strategy:**
 - Split on `~` to get raw segments; the first is absolute, the rest are relative
 - If the final raw segment is a UUID, treat it as the combined-anonymous instance tail; otherwise treat the final raw segment as the well-known instance segment (or absent, if the identifier ends with `~`)
 - Parse the non-UUID segments as GTS segments (first absolute, the rest relative)
 - Validate that all segments except the final instance designator are types


## 9. Reference Implementation Recommendations

GTS specification provides recommendations for reference implementation of the core operations for working with GTS identifiers. These recommendations are not mandatory but are provided to help implementers understand the expected behavior of appropriate reference implementations in different programming languages.

For existing reference implementations, refer to the official libraries:

- [gts-python](https://www.github.com/GlobalTypeSystem/gts-python)
- [gts-go](https://www.github.com/GlobalTypeSystem/gts-go)
- [gts-rust](https://www.github.com/GlobalTypeSystem/gts-rust)

### 9.1 - Identifier reference in JSON and JSON Schema

This section provides **recommended** conventions for embedding GTS identifiers into JSON objects (instances) and JSON Schemas (types). Implementations may support additional conventions, but these provide an interoperable default.

**JSON Schema (`$id`)**

It is recommended to put the GTS **type identifier** into the JSON Schema `$id` field, using a URI-like form by prepending the `gts://` prefix:

> **Reserved prefix note**: Do **not** place the canonical `gts.` string directly in `$id`. Always wrap the identifier with the `gts://` scheme (for example: `"$id": "gts://gts.x.core.events.type.v1~"`). The raw `gts.` prefix is reserved for canonical identifiers inside the scheme, and mixing it directly into `$id` leads to ambiguity and upload failures.

```json
{
  "$id": "gts://gts.x.core.events.type.v1~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Event Envelope (Common Fields)"
}
```

Implementation note: GTS itself defines the canonical identifier string starting with `gts.`. When `$id` is expressed as `gts://...`, implementations should trim the `gts://` prefix and treat the remainder as the canonical GTS identifier for validation, comparison, and registry keys. The `gts://` prefix exists only to make `$id` URI-compatible.

When `$id` starts with `gts://`, the remainder **must** be a valid, wildcard-free GTS identifier (see OP#1 rules). Asterisks and other wildcard tokens are not permitted in GTS Type Identifiers.

**JSON Schema (`$ref`)**

It is recommended to make GTS Type references in JSON Schema `$ref` URI-compatible the same way as `$id`, by prepending the `gts://` prefix when `$ref` points at a GTS Type Identifier:

> **Note:** Just like `$id`, do not embed raw `gts.` prefixes in `$ref`. Use the URI form (`gts://...`) and ensure the referenced identifier is a valid GTS ID with no wildcard characters.

```json
{
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" }
  ]
}
```

Note: local JSON Pointer references (e.g. `"$ref": "#/definitions/Foo"`) are Draft-07 compliant and remain valid. The `gts://` recommendation applies only when `$ref` targets a GTS Type Identifier. Under Draft-07 the canonical container for reusable subschemas is `definitions`; the `$defs` keyword (introduced in 2019-09) MUST NOT be used in GTS Type Schemas.

Implementation note: When `$ref` is expressed as `gts://...`, implementations should trim the `gts://` prefix and treat the remainder as the canonical GTS identifier for resolution, validation, comparison, and registry keys. The `gts://` prefix exists only to make `$ref` URI-compatible.

The post-`gts://` content must therefore parse as a valid GTS identifier with no wildcards; otherwise the schema upload should be rejected.

**JSON instances (well-known vs anonymous)**

- **Well-known instances (named)**: recommended to use a GTS identifier in the `id` field (alternatives: `gtsId`, `gts_id`). Prefer a chained identifier so the **left segment(s)** define the GTS Type automatically, and the **rightmost** segment is the instance name.
  - Example (well-known topic/stream instance): `gts.x.core.events.topic.v1~x.commerce._.orders.v1.0`
- **Anonymous instances**: typically use the `id` field to store the object UUID, and store the GTS Type Identifier separately in a `type` field (alternatives: `gtsType`, `gts_type`).
  - Example (anonymous event instance): `id: "7a1d2f34-5678-49ab-9012-abcdef123456"`, `type: "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~"`

See working examples under `./examples/events`:
- Well-known topics: `./examples/events/instances/gts.x.core.events.topic.v1~x.commerce.orders.orders.v1.0.json`
- Anonymous events: `./examples/events/instances/gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1~.examples.json`

### 9.2 - GTS operations (OP#1 - OP#13):

Implement and expose all operations OP#1–OP#13 listed above and add appropriate unit tests.

- **OP#1 - ID Validation**: Verify identifier syntax
- **OP#2 - ID Extraction**: Extract identifiers from JSON objects or JSON Schema documents
- **OP#3 - ID Parsing**: Decompose identifiers into constituent parts (vendor, package, namespace, type, version, etc.)
- **OP#4 - ID Pattern Matching**: Match identifiers against patterns containing wildcards
- **OP#5 - ID to UUID Mapping**: Generate deterministic UUIDs from GTS identifiers
- **OP#6 - Schema Validation**: Validate object instances against their corresponding schemas. When validating instances, if the rightmost type in the chain is marked `x-gts-abstract: true`, validation MUST fail (see section 9.11)
- **OP#7 - Relationship Resolution**: Load schemas and instances, resolve inter-dependencies, and detect broken references
- **OP#8 - Compatibility Checking**: Verify that schemas with different MINOR versions are compatible
- **OP#9 - Version Casting**: Transform instances between compatible MINOR versions
- **OP#10 - Query Execution**: Filter identifier collections using the GTS query language
- **OP#11 - Attribute Access**: Retrieve property values and metadata using the attribute selector (`@`)
- **OP#12 - Type Derivation Validation**: Validate that a derived type correctly extends its base chain. This includes:
  - **Structural rules (§3.2.1)** — top-level form is the canonical single-item `allOf` with a `$ref` to the immediate parent in the chained `$id`; no top-level `anyOf`/`oneOf`/`not`; base schemas do not use `allOf` for derivation.
  - **Constraint compatibility** — derived schemas conform to all constraints defined in their parent schemas throughout the inheritance hierarchy (`additionalProperties`, narrowing/widening, etc.).
  - **Trait inheritance** — parallel trait-type derivation and trait completeness checks from OP#13.
  - **Modifier enforcement** — if any base in the chain is marked `x-gts-final: true`, validation MUST fail (see §9.11).
- **OP#13 - Schema Traits Validation**: Validate schema traits — `x-gts-traits-schema` (a URN-string reference to a registered trait-type) and `x-gts-traits` (a plain JSON object whose merged value across the host chain must be a valid instance of the host's effective trait-type). See §9.7 for full semantics and validation rules (parallel derivation, immutable-once-set merge, trait completeness for non-abstract host-types).

### 9.3 - GTS entities registration

Implement simple GTS instances in-memory registry with optional GTS entities validation on registration. If "validation" parameter enabled, the entity registration action must ensure that all the GTS references are valid - identitfiers must match GTS pattern, refererred entities must be registered, the x-gts-ref references must be valid (see below)

### 9.4 - CLI support

Provide a CLI wrapping OPs for local use and CI: e.g., `gts validate`, `gts parse`, `gts match`, `gts uuid`, `gts compat`, `gts cast`, `gts query`, `gts get`. Use non-zero exit codes on validation/compatibility failures for pipeline integration.

### 9.5 - Web server with OpenAPI

Implement an HTTP server that conforms to `tests/openapi.json` so it can be tested from this specification directory.

```
# 1. Start appropriate server, normally as 'gts server'
# 2. Test it's conformance to required openapi.json by running specification tests:
pytest ./tests
```

### 9.6 - `x-gts-ref` support

Use `x-gts-ref` in GTS schemas (JSON schemas) to declare that a string field is a GTS entity reference, not an arbitrary string; validators must enforce this.

Allowed values:
- `"x-gts-ref": "gts.*"` — field must be a valid GTS identifier (see OP#1); optionally resolve against a registry if available.
- `"x-gts-ref": "/$id"` — relative self-reference; field value must equal the current schema’s `$id` without the `gts://` prefix ("/" refers to the JSON Schema document root, `$id` is its identifier). The referred field must be a GTS string or another `x-gts-ref` field.

See examples in `./examples/modules` for typical patterns.

Implementation notes:

- Treating `x-gts-ref` like JSON Schema string constraints:
  - When the value is a literal starting with `gts.` (e.g., `gts.x.core.modules.capability.v1~`), it can be enforced similarly to a `startsWith(...)` check by validating the instance value against the provided GTS prefix (sections 8.1/8.2). Implementations must also validate the GTS ID.
  - When the value is a relative path like `./$id` or `./description`, resolve it as a JSON Pointer relative to the schema root. If the pointer doesn't resolve to a GTS string or another `x-gts-ref` field, an error must be reported.
  - For nested paths (e.g., `./properties/id`), resolve the pointer accordinly to the field path in the JSON Schema document.


### 9.7 - GTS Type Schema Traits (`x-gts-traits-schema` / `x-gts-traits`)

**OP#13 - Schema Traits Validation**: Validate that `x-gts-traits` values on a host GTS Type Schema conform to the **trait-type** referenced by `x-gts-traits-schema` (resolved through the parallel trait-type chain), that the trait-type chain itself is a valid derivation, that traits set by an ancestor are not overridden by a descendant (immutable-once-set), and that every required trait field is resolved (concrete value or `default`) for any non-abstract host-type. Both `x-gts-traits-schema` and `x-gts-traits` are schema-only keywords and MUST NOT appear in instances. Uses the same validation endpoints (`/validate-type-schema`, `/validate-entity`).

A **schema trait** is a semantic annotation attached to a GTS Type Schema that describes **system behaviour** for processing instances of that type. Traits are not part of the object data model — they do not define instance properties. Instead, they configure cross-cutting concerns such as:

- **Retention rules** — how long instances of this type are kept (e.g., object TTL)
- **Processing directives** — how attributes should be handled (e.g., PII masking, indexing hints)
- **Association links** — linking schemas to related entities (e.g., associating an event type with its topic/stream)

Traits are themselves **first-class GTS Type Schemas**, registered like any other type. A host type attaches one trait-type by URN; descendants of the host inherit that attachment and MAY refine it by attaching a *derived* trait-type (parallel derivation, §9.7.4).

#### 9.7.1 Keywords

Two JSON Schema annotation keywords are used together:

| Keyword | JSON type | Purpose | Typical location |
|---------|-----------|---------|------------------|
| **`x-gts-traits-schema`** | String — a GTS Type URN (e.g., `"gts://gts.x.core.traits.event_meta.v1~"`) | References the **trait-type** that defines the shape of trait values for instances of this host-type and its descendants | Base / ancestor host-types; derived host-types when they attach a derived trait-type |
| **`x-gts-traits`** | Plain JSON object | Provides concrete **values** for the trait properties — an instance of the effective trait-type | Any host-type in the chain; values from all levels are merged top-down with immutable-once-set semantics (§9.7.5) |

**Schema-only keywords:** Both `x-gts-traits-schema` and `x-gts-traits` are **schema annotation keywords** and MUST only appear in JSON Schema documents (documents with `$schema`). They MUST NOT appear in instance documents. Implementations MUST reject instances that contain these keywords.

**`x-gts-traits-schema` is a single string URN.** The inline-schema, `$ref`, and composition forms permitted by earlier versions of this spec are **removed**. Implementations MUST reject any `x-gts-traits-schema` whose value is not a string. The string value MUST be a valid GTS Type URN ending in `~`, and the referenced trait-type MUST already be registered (or registered in the same atomic operation) and MUST itself be a valid GTS Type Schema (subject to §3.2.1).

**`x-gts-traits` is a plain JSON object** containing concrete values. Each level of the host chain may provide a partial object; the registry merges values shallowly across the chain with immutable-once-set semantics (§9.7.5).

A single host schema MAY contain both keywords — common when a derived host-type attaches a derived trait-type (`x-gts-traits-schema`) and provides initial values for some of the newly-introduced fields (`x-gts-traits`).

#### 9.7.2 Trait-type definition

A trait-type is a regular GTS Type Schema. It MUST follow all the same rules as any other GTS Type Schema — including the top-level composition rules of §3.2.1 (canonical form for derivation, no top-level `anyOf`/`oneOf`/`not`, single immediate-parent `$ref` in `allOf` for derived trait-types).

There is no special marker that identifies a type as "intended to be used as a trait" — any registered GTS Type Schema may be referenced as a trait-type. A vendor MAY group its trait-types under a shared base trait-type (so that all derived trait-types form one parallel-derivation family), or MAY register each trait-type independently. The spec does not mandate either organization.

**Base trait-type example** (an `event_meta` trait-type that captures retention and topic-ref):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.traits.event_meta.v1~",
  "type": "object",
  "properties": {
    "topicRef": {
      "description": "GTS ID of the topic/stream where events of this type are published.",
      "type": "string",
      "x-gts-ref": "gts.x.core.events.topic.v1~",
      "default": "gts.x.core.events.topic.v1~x.core._.default.v1"
    },
    "retention": {
      "description": "ISO 8601 duration for event retention.",
      "type": "string",
      "default": "P30D"
    }
  }
}
```

**Derived trait-type example** (extending the base with an additional `auditRetention` field):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.traits.event_meta.v1~x.core.audit.event_meta.v1~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.traits.event_meta.v1~" }
  ],
  "properties": {
    "auditRetention": {
      "description": "Retention override for audit compliance.",
      "type": "string",
      "default": "P365D"
    }
  }
}
```

The derived trait-type follows the strict canonical form (§3.2.1): one-item `allOf` with `$ref` to the immediate parent, all new constraints (the additional `properties` entry) at the top level. OP#12 derivation rules apply to trait-types just as they do to host-types: a derived trait-type MUST be fully compatible with its parent, defaults declared in an ancestor MUST NOT change in a descendant, etc.

#### 9.7.3 Attaching a trait-type to a host

A host GTS Type Schema attaches a trait-type by setting `x-gts-traits-schema` to the trait-type's URN:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "x-gts-traits-schema": "gts://gts.x.core.traits.event_meta.v1~",
  "properties": {
    "id":         { "type": "string" },
    "typeId":     { "type": "string" },
    "occurredAt": { "type": "string", "format": "date-time" },
    "payload":    { "type": "object" }
  },
  "required": ["id", "typeId", "occurredAt", "payload"]
}
```

A host-type may attach **at most one** trait-type. Multiple trait shapes are expressed by combining them into a single trait-type (with the relevant `properties`), not by attaching multiple trait-types to one host.

Derived host-types provide trait values for the attached trait-type by adding `x-gts-traits` at the top level of the derived schema (alongside the canonical-form `allOf`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" }
  ],
  "x-gts-traits": {
    "topicRef":  "gts.x.core.events.topic.v1~x.commerce._.orders.v1",
    "retention": "P90D"
  },
  "properties": {
    "typeId": { "const": "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~" },
    "payload": {
      "type": "object",
      "properties": {
        "orderId":     { "type": "string" },
        "totalAmount": { "type": "number" }
      },
      "required": ["orderId", "totalAmount"]
    }
  }
}
```

The derived host-type inherits `x-gts-traits-schema` from its base; it does not redeclare it. The `x-gts-traits` object is validated against the effective trait-type (§9.7.5).

#### 9.7.4 Parallel derivation

Host-type inheritance and trait-type inheritance run on **two parallel chains**:

- The **host chain** is the chained `$id` of the host (e.g., `gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~`).
- The **trait-type chain** is the chained `$id` of whichever trait-type is in effect (e.g., `gts.x.core.traits.event_meta.v1~x.core.audit.event_meta.v1~`).

For a host chain `H₀ → H₁ → … → Hₙ`:

1. **Inheritance by default.** If `Hₖ` does not declare its own `x-gts-traits-schema`, it inherits the trait-type attached by the nearest ancestor that did declare one. If no ancestor declared one, the host-type has no traits at all (and `x-gts-traits` MUST NOT appear on it or any of its descendants).
2. **Refinement by parallel derivation.** If `Hₖ` declares its own `x-gts-traits-schema = T_k` and some ancestor `Hⱼ` (j < k) declared `Tⱼ`, then `T_k`'s `$id`-chain MUST be derived from `Tⱼ`. In other words, `T_k`'s chain MUST extend `Tⱼ`'s chain (left-prefix match in trait-type space). Any other declaration on `Hₖ` is invalid.
3. **First-time attachment.** If no ancestor of `Hₖ` declared a trait-type, `Hₖ` may attach any registered trait-type.

This rule ensures that descending the host chain can only **refine** the trait shape — never substitute it for an unrelated one.

**Example.** Suppose `gts.x.core.events.type.v1~` attaches `gts.x.core.traits.event_meta.v1~`. A derived audit-event host-type may attach a derived trait-type that adds an `auditRetention` field, **provided** that derived trait-type extends the base trait-type:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~x.core.audit.event.v1~",
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" }
  ],
  "x-gts-abstract": true,
  "x-gts-traits-schema": "gts://gts.x.core.traits.event_meta.v1~x.core.audit.event_meta.v1~",
  "x-gts-traits": {
    "topicRef": "gts.x.core.events.topic.v1~x.core._.audit.v1"
  }
}
```

The trait-type's chain (`event_meta.v1~ → audit.event_meta.v1~`) is parallel to the host's chain (`events.type.v1~ → audit.event.v1~`). Attaching, say, `gts.x.core.traits.retention.v1~` here — a trait-type unrelated to the base `event_meta` chain — would be invalid by rule (2).

#### 9.7.5 Trait values resolution & merge (normative)

For any host-type in a chain, the **effective trait-type** is the most-derived trait-type attached anywhere in the host chain at or above this level (inherited from the nearest ancestor that declared one, or declared at this level itself).

The **effective trait values** are computed by **shallow merging** the `x-gts-traits` objects encountered along the host chain (root → leaf):

- For each top-level key, the **first** schema in the chain to provide a concrete value for that key "wins". Descendants MAY restate the same value (idempotent) but MUST NOT change it. A schema that changes a concrete value set by an ancestor is **invalid** (immutable-once-set); the registry and OP#6 MUST reject it as a consequence.
- Keys not provided in any `x-gts-traits` are resolved to the `default` declared in the effective trait-type for that key (if any).
- A `default` is **not** a concrete assignment: it does not lock the key, and a descendant MAY provide a concrete value for a key that was previously only filled by a default.
- The merge is **shallow** — only top-level keys are compared. Object-valued trait fields are replaced wholesale by the first concrete assignment; they are not deep-merged.

The effective trait-type itself is a normal JSON Schema. The merged effective trait values MUST validate against it using standard JSON Schema validation. A host schema whose merged effective trait values fail validation — required field unresolved, type mismatch, constraint violation — is invalid.

**Trait completeness rule (validity, not enforcement):** a GTS Type Schema is **invalid** if BOTH of the following hold:

1. It is not marked `x-gts-abstract: true`.
2. Its effective trait values do not satisfy the effective trait-type schema — i.e., at least one field that is `required` by the effective trait-type schema and not covered by a `default` has no concrete value assigned anywhere in the host chain.

Such a schema is invalid by definition. As a consequence:

- The registry MUST reject it at registration time (`/entities`, `/validate-type-schema`). This is the load-bearing check — once a concrete host-type is in the registry, it is guaranteed trait-complete.
- OP#6 instance validation (`/validate-entity`) MUST also fail for any instance referencing such a schema, as defense in depth against registry corruption or implementations predating this rule.

A host-type that intentionally leaves trait values to be resolved by descendants MUST mark itself `x-gts-abstract: true`. There is no implicit "abstract because incomplete" state.

**Defaults are immutable across the trait-type chain.** A descendant trait-type MUST NOT change a `default` declared by an ancestor trait-type. A trait-type that does so is invalid; this is enforced through OP#12 on the trait-type chain itself (just like any other constraint narrowing/loosening rule).

**Example — immutable trait override (failure).**

Consider a host chain: `base → audit_event → most_derived_event`.

- `audit_event` sets `x-gts-traits.topicRef` to `gts.x.core.events.topic.v1~x.core._.audit.v1`.
- `most_derived_event` attempts to set `x-gts-traits.topicRef` to `gts.x.core.events.topic.v1~x.core._.notification.v1`.

`most_derived_event` is invalid: `topicRef` was already set concretely by `audit_event` and the new value differs.

#### 9.7.6 MAJOR version pinning of trait-types

`x-gts-traits-schema` references a trait-type at a specific **MAJOR version** (e.g., `v1`). Moving the host-type to a `v2` of the trait-type — `gts.x.core.traits.event_meta.v1~` → `gts.x.core.traits.event_meta.v2~` — is a **breaking change** for the host-type, equivalent to attaching a different trait family entirely. Authors who want continuous trait-shape evolution use MINOR versions of the same trait-type or derive new trait-types from the original via the canonical form (§3.2.1), preserving compatibility.

See `./examples/events/types/` for complete worked examples demonstrating base trait-types, derived trait-types, host attachment, and parallel derivation.

### 9.8 - YAML support

Accept and emit both JSON and YAML (`.json`, `.yaml`, `.yml`) for schemas and instances.
Ensure conversions are lossless; preserve `$id`, `gtsId`, and custom extensions like `x-gts-ref`.

### 9.9 - TypeSpec support

Support generating JSON Schema and OpenAPI from TypeSpec while preserving GTS semantics.
Ensure generated schemas use GTS identifiers as `$id` for types and keep any `x-gts-*` extensions intact.

### 9.10 - UUID as object IDs

Support UUIDs (format: `uuid`) for instance `id` fields.

### 9.11 - GTS Type Schema Modifiers (`x-gts-final` / `x-gts-abstract`)

A **schema modifier** is a boolean annotation on a GTS Type Schema that restricts how the type participates in the GTS type system. Modifiers can be used to control inheritance and instantiation behavior. There are two keywords for this purpose: `x-gts-final` and `x-gts-abstract`.

#### 9.11.1 Keywords

| Keyword | JSON type | Purpose | Typical location |
|---------|-----------|---------|------------------|
| **`x-gts-final`** | `boolean` | Marks the type as **not inheritable** — no derived schemas may reference it as a base | Leaf schemas; enum-like types with a fixed set of well-known instances |
| **`x-gts-abstract`** | `boolean` | Marks the type as **not directly instantiable** — instances must conform to a concrete derived type | Base/ancestor schemas that serve purely as templates |

**Schema-only keywords:** Both `x-gts-final` and `x-gts-abstract` are **schema annotation keywords** and MUST only appear in JSON Schema documents (documents with `$schema`). They MUST NOT appear in instance documents. Implementations MUST reject instances that contain these keywords.

**Allowed values:** The only meaningful value is `true`. If the keyword is absent or set to `false`, it has no effect (the schema behaves normally — both inheritable and instantiable). Implementations MUST reject non-boolean values.

**Mutual exclusion:** A schema MUST NOT declare both `"x-gts-final": true` and `"x-gts-abstract": true`. This combination is semantically meaningless (a type that can be neither inherited from nor instantiated serves no purpose) and MUST be rejected during schema registration or validation.

| Modifier combination | Inheritance allowed? | Direct instances allowed? |
|---|---|---|
| *(default / neither)* | Yes | Yes |
| `x-gts-abstract: true` | Yes | No |
| `x-gts-final: true` | No | Yes |
| Both `true` | **INVALID** — MUST be rejected | — |

#### 9.11.2 `x-gts-final` semantics

When a schema declares `"x-gts-final": true`:

1. **Registration guard**: When a new schema is registered whose `allOf` / `$ref` chain references a final type as a base, the registry MUST reject the registration (when validation is enabled). Specifically, if the derived schema's `$id` is of the form `gts://gts.A~B~` and schema `A~` has `"x-gts-final": true`, then registering `A~B~` MUST fail.

2. **Validation via `/validate-type-schema` (OP#12)**: When validating a derived schema against its base chain, if any base schema in the chain is marked `x-gts-final`, validation MUST fail with an error indicating that the base type is final and cannot be extended.

3. **Instances are unaffected**: A final type MAY have well-known instances and anonymous instances. `x-gts-final` restricts only schema derivation, not instantiation.

4. **No propagation**: `x-gts-final` applies only to the schema that declares it. It does NOT propagate to base types in the chain. For a chain `A~ → B~ → C~`, if `B~` is final, then `C~` is invalid. But `A~` can still be inherited by types other than `B~`'s descendants.

5. **Keyword placement**: The keyword MUST appear at the **top level** of the JSON Schema document, adjacent to `$id` and `$schema`:

```json
{
  "$id": "gts://gts.x.infra.compute.vm_state.v1~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "x-gts-final": true,
  "type": "object",
  "properties": { "..." : {} }
}
```

For derived schemas using `allOf`, the keyword MUST appear at the top level, NOT inside the `allOf` entries:

```json
{
  "$id": "gts://gts.x.core.events.type.v1~x.vendor._.order_event.v1~",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "x-gts-final": true,
  "type": "object",
  "allOf": [
    { "$ref": "gts://gts.x.core.events.type.v1~" },
    { "..." : {} }
  ]
}
```

#### 9.11.3 `x-gts-abstract` semantics

When a schema declares `"x-gts-abstract": true`:

1. **Instance registration guard**: When a new instance is registered whose **rightmost type** in the chain is an abstract type, the registry MUST reject the registration (when validation is enabled). For example, if `gts.x.core.events.type.v1~` is abstract, registering a well-known instance `gts.x.core.events.type.v1~x.vendor._.some_event.v1` MUST fail (the rightmost type is abstract). However, if a concrete derived schema `gts.x.core.events.type.v1~x.vendor._.order_event.v1~` exists and is not abstract, then registering instance `gts.x.core.events.type.v1~x.vendor._.order_event.v1~x.vendor._.order_placed.v1` succeeds.

2. **Validation via `/validate-instance` and `/validate-entity` (OP#6)**: When validating an instance (through either the instance-specific or unified entity endpoint), the system resolves the rightmost type in the chain. If that type is abstract, validation MUST fail.

3. **Schema derivation is unaffected**: An abstract type is explicitly intended to be inherited from. Registering derived schemas from an abstract type always succeeds (subject to other validation rules).

4. **No propagation**: A derived type is concrete by default. If `A~` is abstract and `B~` derives from `A~`, `B~` is concrete unless it also declares `"x-gts-abstract": true`.

5. **Anonymous instances**: For combined anonymous instance IDs like `gts.A~<UUID>`, the system resolves the type from the prefix. If that type is abstract, the instance MUST be rejected.

#### 9.11.4 Interaction with `x-gts-traits`

- **Abstract types with traits**: An abstract host-type MAY declare `x-gts-traits-schema`. Since abstract types cannot have direct instances, trait values (`x-gts-traits`) do not need to be fully resolved on the abstract type itself — descendants may close out remaining required fields. Trait completeness is enforced on any **non-abstract** host-type (see §9.7.5).

- **Final types with traits**: A final type MAY declare `x-gts-traits` values. Since no derived types can exist and a final type is non-abstract, all required trait fields MUST be resolved on the final type itself (concrete value or `default`). If the effective trait-type requires properties without defaults and the final type does not provide them via `x-gts-traits`, the schema is invalid.

#### 9.11.5 Registration enforcement

Enforcement follows the same pattern as existing `?validate=true` behavior: checks are performed when validation is enabled on registration, and always enforced on explicit validation endpoints (`/validate-type-schema`, `/validate-instance`, `/validate-entity`). This is consistent with existing patterns (e.g., `x-gts-ref` checks in section 9.6).

See `./examples/typespec/vms/types/states/gts.x.infra.compute.vm_state.v1~.schema.json` for an example of a final type, `./examples/modules/types/gts.x.core.modules.capability.v1~.schema.json` for another final type, and `./examples/events/types/gts.x.core.events.type.v1~.schema.json` for an example of an abstract base type.


## 10. Collecting Identifiers with Wildcards

**Important:** An identifier containing a wildcard (`*`) is a **pattern for matching** and may not serve as a canonical identifier for a type or instance.

A single wildcard (`*`) character can be used to find all identifiers matching a given prefix. The wildcard is a greedy operator that matches any sequence of characters after it, including the `~` chain separator.

**Rules for using wildcards:**
1. The wildcard (`*`) must be used only **once**.
2. The wildcard must appear at the **end** of the pattern.
3. The wildcard must not be used in combination with an attribute selector (`@`) or query (`[]`).
4. The pattern must start at the beginning of a valid segment. For example, `gts.x.llm.chat.msg*` is invalid if `msg` is not a complete segment. `gts.x.llm.chat.message.v*` is valid because `v` is the start of the version segment.
5. **Minor version semantics**: When a pattern specifies only a major version (e.g., `v0.*`), it matches candidates with any minor version of that major version (e.g., `v0.1~`, `v0.2~`, etc.). This is because the minor version is optional, and omitting it semantically means "any minor version".

**Valid Examples:**

Given the following identifiers:
```
gts.x.llm.chat.message.v1.0~
gts.x.llm.chat.message.v1.0~x.llm.system_message.v1.0~
gts.x.llm.chat.message.v1.1~
gts.x.llm.chat.message.v1.1~x.llm.user_message.v1.1~
```

- **Pattern:** `gts.x.llm.chat.message.*` - Find all base schemas versions and their derived schemas
  - **Result:** All four identifiers listed above.

- **Pattern:** `gts.x.llm.chat.message.v1.*` - Find all base and deriver types from v1 (any minor version)
  - **Result:** All four identifiers (matches both `v1.0~` and `v1.1~` because pattern without minor version matches any minor version)

- **Pattern:** `gts.x.llm.chat.message.v1~*` - Find all derived types from v1 (any minor version)
  - **Result:** two derived entities: `gts.x.llm.chat.message.v1.0~x.llm.system_message.v1.0~`, `gts.x.llm.chat.message.v1.1~x.llm.user_message.v1.1~`

- **Pattern:** `gts.x.llm.chat.message.v1.0~*` - Find all derived types (schemas) down the chain
  - **Result:** Only one matching entity: `gts.x.llm.chat.message.v1.0~x.llm.system_message.v1.0~`


**Minor Version Matching Examples:**

The following examples demonstrate the special case where patterns without minor versions match candidates with any minor version:

```
Pattern:   gts.vendor.pkg.ns.type.v0~*
Candidate: gts.vendor.pkg.ns.type.v0.1~
Result:    ✅ MATCH (pattern v0~ matches any v0.x)

Pattern:   gts.vendor.pkg.ns.type.v0~*
Candidate: gts.vendor.pkg.ns.type.v0~
Result:    ✅ MATCH (exact match)

Pattern:   gts.vendor.pkg.ns.type.v0.1~*
Candidate: gts.vendor.pkg.ns.type.v0.1~
Result:    ✅ MATCH (exact match with minor version)

Pattern:   gts.vendor.pkg.ns.type.v0~abc.*
Candidate: gts.vendor.pkg.ns.type.v0.1~
Result:    ❌ NO MATCH (pattern v0~abc.* does not match any v0.x)

Pattern:   gts.vendor.pkg.ns.type.v0.1~*
Candidate: gts.vendor.pkg.ns.type.v0.2~
Result:    ❌ NO MATCH (different minor versions)

Pattern:   gts.vendor.pkg.ns.type.v0~*
Candidate: gts.vendor.pkg.ns.type.v1.0~
Result:    ❌ NO MATCH (different major versions)
```

**Invalid Pattern Examples:**
- `gts.x.llm.chat.msg*` - Invalid if `msg` is not a complete segment.
- `gts.x.llm.chat.message.v*~*` - Multiple wildcards are used.


## 11. JSON and JSON Schema Conventions

### 11.0 JSON Schema Dialect

GTS Type Schemas are defined in terms of **JSON Schema Draft-07**. Implementations MUST treat the GTS keywords described in this specification (`$id`, `$ref`, `allOf`, `const`, `x-gts-traits-schema`, `x-gts-traits`, `x-gts-final`, `x-gts-abstract`, etc.) as layered on top of Draft-07 semantics.

- The `$schema` field of every GTS Type Schema MUST be `http://json-schema.org/draft-07/schema#`.
- Implementations MAY accept other JSON Schema dialects for non-GTS schemas, but MUST NOT rely on keywords introduced after Draft-07 (such as `prefixItems`, `unevaluatedProperties`, `unevaluatedItems`, `$dynamicRef`/`$dynamicAnchor`, `dependentRequired`, `dependentSchemas`) when interpreting GTS Type Schemas.
- Reusable subschemas inside a GTS Type Schema SHOULD be placed under the Draft-07 canonical keyword `definitions`. Local JSON Pointer references such as `"$ref": "#/definitions/Foo"` are the recommended form.
- `anyOf`, `oneOf`, and `not` are valid Draft-07 keywords and remain available inside nested sub-schemas (e.g., property sub-schemas, `definitions` entries, `items`). They MUST NOT appear at the **top level** of any GTS Type Schema — see §3.2.1 for the full top-level composition rules.

### 11.1 Global rules: schema vs instance, normalization, and document categories

This section defines recommendations for how GTS-aware systems interpret JSON documents. The rules describe the concepts; the exact field names used for instance IDs and instance types are **implementation-defined** and may be **configuration-driven** (different systems may look for identifiers in different fields).

#### Rule A — Schema vs instance discriminator

**A JSON document is a schema if and only if it contains a top-level `$schema` field.**

- If `$schema` is present → the document MUST be treated as a **schema**.
- If `$schema` is absent → the document MUST be treated as an **instance**.

This discriminator MUST be applied before any ID parsing heuristics.

#### Rule B — GTS schema `$id` normalization

For GTS schemas (documents with `$schema`), it is recommended that `$id` is URI-compatible by using:
- `$id: "gts://<canonical-gts-id>"`

Implementations MUST normalize this by stripping the `gts://` prefix when extracting/returning the canonical GTS identifier. The `gts://` prefix exists only to make `$id` URI-compatible.

#### Rule C — JSON document categories

Implementations MUST clearly distinguish the following **five** categories of JSON documents:

1. **GTS Type Schemas**
   - Have `$schema`
   - Have `$id` starting with `gts://` and the remainder is a valid **GTS Type Identifier** (ends with `~`)
   - This is the canonical JSON representation of a GTS Type Schema. Files named `*.schema.json` carry such documents.
   - Example:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object"
}
```

2. **Non‑GTS schemas**
   - Have `$schema`
   - Do not have a valid GTS `$id`
   - Handling is **implementation-defined** (ignore vs error depending on API context)
   - Example:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://example.com/schemas/order.json",
  "type": "object"
}
```

3. **Instances of unknown / non‑GTS schemas**
   - No `$schema`
   - GTS Type cannot be determined (no acceptable GTS Type reference field found, or the field value is not a valid GTS ID)
   - Handling is **implementation-defined** (ignore vs error depending on API context)
   - Example:

```json
{
  "id": "123",
  "payload": { "foo": "bar" }
}
```

4. **Well-known GTS instances (named)**
   - No `$schema`
   - Instance is identified by a **GTS Instance Identifier** (often a chain) stored in an implementation-chosen instance-ID field
   - The GTS Type is derived from the **left segment(s)** of the chain
   - Example (well-known topic/stream instance):

```json
{
  "id": "gts.x.core.events.topic.v1~x.commerce._.orders.v1.0",
  "name": "orders"
}
```

> NOTE: In this specification, a GTS Instance Identifier is a GTS identifier **without** the trailing `~` (i.e., it does not name a GTS Type).
> Some systems may still accept an `id` field or its equivalent that contains a **GTS Type Identifier** (ending with `~`) and treat it as a *GTS Type reference* rather than a *GTS Instance Identifier*.
> This behavior is **not defined by the GTS spec** and is entirely **implementation-specific / configuration-driven**.

5. **Anonymous GTS instances**
   - No `$schema`
   - Instance `id` is opaque (typically UUID)
   - GTS Type is provided separately via an implementation-chosen GTS Type Identifier field (e.g., `type`, `gtsType`, `gts_type`)
   - Example (anonymous event instance):

```json
{
  "id": "7a1d2f34-5678-49ab-9012-abcdef123456",
  "type": "gts.x.core.events.type.v1~x.commerce.orders.order_placed.v1.0~",
  "occurredAt": "2025-09-20T18:35:00Z"
}
```

> NOTE: In this specification, a GTS Type Identifier is a GTS identifier **with** the trailing `~`.
> Some systems may still accept a `type` field or its equivalent that contains a **GTS Instance Identifier** (not ending with `~`). This behavior is **not defined by the GTS spec** and is entirely **implementation-specific / configuration-driven**.


#### ID and type-field heuristics (implementation-defined)

For **instances** (documents without `$schema`), implementations typically apply heuristics in this order:

1. **Try instance ID fields** (commonly `id`, then aliases like `gtsId`, `gts_id`):
   - If the value is a valid GTS identifier, treat it as a **well-known instance** and derive the `type_id` (the GTS Type Identifier) from the chain (everything up to and including the last `~`).
   - Otherwise treat it as an **anonymous instance** ID value.
2. **For anonymous instances**, determine the GTS Type from a separate field (commonly `type`, or aliases like `gtsType`, `gts_type`; `schema` MAY be supported as a legacy alias but is discouraged for new instances).

**Important**: When determining instance type, a chained GTS ID in the instance ID field ALWAYS takes priority over any explicit type field. The type is derived from the chain's type segments, not from a separate type property.

Different systems may choose different field names and priority orders via configuration. The examples below (and the `./examples/*` folders) use the common defaults: `id` for instance ID and `type` for instance type.

#### `type_id` semantics (normative)

The `type_id` returned by extraction/registration APIs (e.g. `/extract-id`) MUST be either a valid **GTS Type Identifier** (ending with `~`) or `null`. It MUST NOT contain any non-GTS value, including JSON Schema dialect URLs (such as `http://json-schema.org/draft-07/schema#`).

Specifically:

- **Derived GTS schema** (chained `$id`): `type_id` is the **parent GTS Type Identifier** — the chain's left segments up to and including the last `~` of the base.
- **Base GTS schema** (single-segment `$id` with no chain): `type_id` is `null` — a base GTS schema has no GTS parent type.
- **Non-GTS schema** (`$schema` present, no GTS `$id`): `type_id` is `null` — the document is not a GTS entity.
- **Well-known GTS instance** (chained GTS ID in instance ID field): `type_id` is the chain's left segments up to and including the last `~`.
- **Anonymous GTS instance** (UUID `id` + separate `type` field, or combined-anonymous form): `type_id` is the GTS Type Identifier referenced by the `type` field (or derived from the chain prefix in the combined form).
- **Non-GTS instance** (no GTS identifier and no GTS Type reference): `type_id` is `null`.

Implementations MAY expose the JSON Schema dialect URL (`$schema`) separately if needed (e.g., as a distinct `meta_schema` field), but MUST NOT conflate it with `type_id`.

### 11.2 Examples

It is advisable to include instance identifiers in a top-level field such as `id`. However, the choice of the specific field name is left to the discretion of the implementation and can vary from service to service.

**Example #1**: **instance definition** of an object instance (event topic) that has an `id` field that encodes the object type (`gts.x.core.events.topic.v1~`) and identifies the object itself (`x.core.idp.events.v1`). In the example below it makes no sense to add an additional `type` field referring to the object schema because the `id` is already unique and there are no other event topics with the given id in the system:

```json
{
  "id": "gts.x.core.events.topic.v1~x.core.idp.events.v1",
  "description": "User-related events (creation, profile changes, etc.)",
  "retention": "P30D",
  "ordering": "by-partition-key",
}
```

**Example #2**: **instance definition** of an object that has a `gtsId` field that encodes the object type, but also its own integer identifier of the object:

```json
[{
    "id": "123",
    "type": "gts.x.core.events.type.v1~x.core.idp.events.v1~",
    "payload": { "foo": "123", "bar": 42 }
},
{
    "id": "125",
    "type": "gts.x.core.events.type.v1~x.core.idp.events.v1~",
    "payload": { "foo": "xyz", "bar": 123 }
}]
```

**Example #3**: **schema definition** of an event type with the `$id` field equal to the type identifier (ending with `~`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "gts://gts.x.core.events.type.v1~",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "payload": { "type": "object" }
  },
  "required": ["id", "payload"]
}
```


## 12. Notes and Best Practices

- Prefer chains where the base system type is first, followed by vendor-specific refinements, and finally the instance.
- Favor additive changes in MINOR versions. Use a new MAJOR for breaking changes.
- Keep types small and cohesive; use `namespace` to group related types within a package.


## 13. Testing

See [tests/README.md](tests/README.md)


## 14. Registered Vendors

The GTS specification does not require vendors to publish their types publicly, but we encourage them to submit their vendor codes to prevent future conflicts.

Currently registered vendors:

| Vendor | Description       |
|--------|-------------------|
| x      | example vendor    |
