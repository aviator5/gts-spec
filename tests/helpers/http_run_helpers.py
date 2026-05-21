"""Shared test helpers for HttpRunner-based GTS tests.

Provides reusable Step builders for registering and validating schemas,
instances, and entities via the GTS HTTP API.
"""

from httprunner import Step, RunRequest


def register(gts_id, schema_body, label="register schema"):
    """Register a schema via POST /entities."""
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        **schema_body,
    }
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def register_derived(gts_id, base_ref, overlay, label="register derived", top_level=None):
    """Register a derived schema that uses the strict canonical form (§3.2.1).

    Emits a derived GTS Type Schema with:
    - top-level `allOf: [{"$ref": base_ref}]` (exactly one item, the parent ref)
    - the `overlay` dict spread at the top level alongside `allOf`
    - optional extra `top_level` keys (e.g. {"x-gts-final": True})

    All of `properties`, `required`, narrowed constraints, GTS modifiers, and trait
    keywords belong at the top level — never inside `allOf`.
    """
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "allOf": [{"$$ref": base_ref}],
    }
    if overlay:
        body.update(overlay)
    if top_level:
        body.update(top_level)
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def register_trait_type(trait_id, schema_body, label="register trait type"):
    """Register a trait-type — a regular GTS Type Schema published under a
    trait-namespaced `$id` (e.g. `gts://gts.x.core.traits.event_meta.v1~`).

    Thin wrapper around `register` kept for readability in OP#13 tests.
    """
    return register(trait_id, schema_body, label)


def register_host_with_trait_ref(
    gts_id, base_ref, trait_urn, overlay=None, traits=None,
    label="register host with trait ref", top_level=None,
):
    """Register a derived host-type that attaches a trait-type by URN.

    Always emits strict Form A:
    - `allOf: [{"$ref": base_ref}]` at top level
    - `x-gts-traits-schema: trait_urn` (string) at top level
    - optional `x-gts-traits: traits` (plain object) at top level
    - `overlay` and `top_level` dicts spread at the top level

    Use `register_trait_type` to publish the trait-type itself first.
    """
    body = {
        "$$id": gts_id,
        "$$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "allOf": [{"$$ref": base_ref}],
        "x-gts-traits-schema": trait_urn,
    }
    if traits is not None:
        body["x-gts-traits"] = traits
    if overlay:
        body.update(overlay)
    if top_level:
        body.update(top_level)
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


def register_instance(instance_body, label="register instance"):
    """Register an instance via POST /entities."""
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(instance_body)
        .validate()
        .assert_equal("status_code", 200)
    )


def validate_type_schema(type_id, expect_ok, label="validate type schema"):
    """Validate a derived GTS Type Schema via POST /validate-type-schema."""
    step = (
        RunRequest(label)
        .post("/validate-type-schema")
        .with_json({"type_id": type_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    return Step(step)


def validate_entity(entity_id, expect_ok, label="validate entity", expected_entity_type=None):
    """Validate an entity via POST /validate-entity."""
    step = (
        RunRequest(label)
        .post("/validate-entity")
        .with_json({"entity_id": entity_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    if expected_entity_type is not None:
        step = step.assert_equal("body.entity_type", expected_entity_type)
    return Step(step)


def validate_instance(instance_id, expect_ok, label="validate instance", expected_id=None):
    """Validate an instance via POST /validate-instance."""
    step = (
        RunRequest(label)
        .post("/validate-instance")
        .with_json({"instance_id": instance_id})
        .validate()
        .assert_equal("status_code", 200)
        .assert_equal("body.ok", expect_ok)
    )
    if expected_id is not None:
        step = step.assert_equal("body.id", expected_id)
    return Step(step)
