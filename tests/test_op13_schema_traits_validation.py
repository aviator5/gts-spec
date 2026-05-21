"""OP#13 — Schema Traits Validation tests for the URN-string trait-type model.

In this model:
- `x-gts-traits-schema` value is a single string URN referencing a registered
  trait-type (a regular GTS Type Schema).
- A host-type attaches one trait-type by URN. Descendants inherit by default
  and MAY refine the trait-type via parallel derivation (the descendant's
  trait-type must be derived from the ancestor's trait-type).
- `x-gts-traits` is a plain JSON object — an instance of the effective
  trait-type. Values from all levels of the host chain are merged shallowly
  with immutable-once-set semantics.

See README.md §9.7 and ADR-0002 for the full spec.
"""

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    register as _register,
    register_derived as _register_derived,
    register_trait_type as _register_trait_type,
    register_host_with_trait_ref as _register_host_with_trait_ref,
    validate_entity as _validate_entity,
    validate_type_schema as _validate_type_schema,
)
from httprunner import HttpRunner, Config, Step, RunRequest


# ---------------------------------------------------------------------------
# Helpers and constants
# ---------------------------------------------------------------------------


TOPIC_REF_DEFAULT = "gts.x.core.events.topic.v1~x.core._.default.v1"
TOPIC_REF_ORDERS = "gts.x.core.events.topic.v1~x.test13._.orders.v1"
TOPIC_REF_AUDIT = "gts.x.core.events.topic.v1~x.test13._.audit.v1"
TOPIC_REF_NOTIF = "gts.x.core.events.topic.v1~x.test13._.notif.v1"


def _trait_event_meta(trait_id, with_topic_default=True, with_retention_default=True,
                      additional=None, required=None):
    """Build a basic event_meta trait-type body (topicRef + retention)."""
    topic_prop = {
        "type": "string",
        "x-gts-ref": "gts.x.core.events.topic.v1~",
    }
    if with_topic_default:
        topic_prop["default"] = TOPIC_REF_DEFAULT
    retention_prop = {"type": "string"}
    if with_retention_default:
        retention_prop["default"] = "P30D"
    body = {
        "type": "object",
        "properties": {
            "topicRef": topic_prop,
            "retention": retention_prop,
        },
    }
    if additional:
        body["properties"].update(additional)
    if required:
        body["required"] = required
    return body


def _post_schema_raw(body, label):
    """Direct /entities POST for malformed bodies that helpers can't build."""
    return Step(
        RunRequest(label)
        .post("/entities")
        .with_json(body)
        .validate()
        .assert_equal("status_code", 200)
    )


# ---------------------------------------------------------------------------
# Value-validation cases (merged effective values vs effective trait-type)
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitsValid_AllResolved(HttpRunner):
    """OP#13 - derived host provides every trait value concretely. Passes."""

    config = Config("OP#13 - All Traits Resolved").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.allres.v1~",
            _trait_event_meta("allres", with_topic_default=False, with_retention_default=False),
            "register trait-type (no defaults)",
        ),
        _register(
            "gts://gts.x.test13.h.allres.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.allres.v1~",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base host attaching trait-type",
        ),
        _register_derived(
            "gts://gts.x.test13.h.allres.event.v1~x.test13._.order_event.v1~",
            "gts://gts.x.test13.h.allres.event.v1~",
            {
                "x-gts-traits": {
                    "topicRef": TOPIC_REF_ORDERS,
                    "retention": "P90D",
                },
            },
            "register derived host with all traits resolved",
        ),
        _validate_type_schema(
            "gts.x.test13.h.allres.event.v1~x.test13._.order_event.v1~",
            True,
            "validate - all traits resolved",
        ),
    ]


class TestCaseOp13_TraitsValid_DefaultsUsed(HttpRunner):
    """OP#13 - trait-type provides defaults for all fields; derived host omits values.

    Defaults fill in, so a non-abstract concrete derived host is still trait-complete.
    """

    config = Config("OP#13 - Defaults cover all traits").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.dfl.v1~",
            _trait_event_meta("dfl"),
            "register trait-type (all fields default)",
        ),
        _register(
            "gts://gts.x.test13.h.dfl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.dfl.v1~",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.dfl.event.v1~x.test13._.simple_event.v1~",
            "gts://gts.x.test13.h.dfl.event.v1~",
            {},
            "register derived host with no x-gts-traits",
        ),
        _validate_type_schema(
            "gts.x.test13.h.dfl.event.v1~x.test13._.simple_event.v1~",
            True,
            "validate - defaults satisfy all required fields",
        ),
    ]


class TestCaseOp13_TraitsInvalid_MissingRequired(HttpRunner):
    """OP#13 - trait-type field is `required` and has no default; nothing in the host
    chain resolves it. Concrete derived host is invalid.
    """

    config = Config("OP#13 - Missing required trait field").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.miss.v1~",
            _trait_event_meta("miss", with_topic_default=False, required=["topicRef"]),
            "register trait-type (topicRef required, no default)",
        ),
        _register(
            "gts://gts.x.test13.h.miss.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.miss.v1~",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.miss.event.v1~x.test13._.incomplete.v1~",
            "gts://gts.x.test13.h.miss.event.v1~",
            {"x-gts-traits": {"retention": "P90D"}},
            "register concrete derived without topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.h.miss.event.v1~x.test13._.incomplete.v1~",
            False,
            "validate should fail - topicRef unresolved on non-abstract host",
        ),
    ]


class TestCaseOp13_TraitsInvalid_WrongType(HttpRunner):
    """OP#13 - trait value has the wrong JSON type for the trait-type schema. Invalid."""

    config = Config("OP#13 - Trait value wrong type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.wtype.v1~",
            _trait_event_meta("wtype"),
            "register trait-type",
        ),
        _register(
            "gts://gts.x.test13.h.wtype.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.wtype.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.wtype.event.v1~x.test13._.wrong_type.v1~",
            "gts://gts.x.test13.h.wtype.event.v1~",
            {"x-gts-traits": {"retention": 30}},  # should be string
            "register derived with int instead of string for retention",
        ),
        _validate_type_schema(
            "gts.x.test13.h.wtype.event.v1~x.test13._.wrong_type.v1~",
            False,
            "validate should fail - retention is not a string",
        ),
    ]


class TestCaseOp13_TraitsInvalid_UnknownProperty(HttpRunner):
    """OP#13 - trait value provides a key not present in the effective trait-type.

    The trait-type has `additionalProperties: false`, so the unknown key is invalid.
    """

    config = Config("OP#13 - Unknown trait property").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.unkn.v1~",
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "retention": {"type": "string", "default": "P30D"},
                },
            },
            "register trait-type with additionalProperties=false",
        ),
        _register(
            "gts://gts.x.test13.h.unkn.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.unkn.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.unkn.event.v1~x.test13._.unknown_prop.v1~",
            "gts://gts.x.test13.h.unkn.event.v1~",
            {"x-gts-traits": {"retention": "P90D", "mysteryKey": "x"}},
            "register derived with unknown trait key",
        ),
        _validate_type_schema(
            "gts.x.test13.h.unkn.event.v1~x.test13._.unknown_prop.v1~",
            False,
            "validate should fail - mysteryKey is not in trait-type",
        ),
    ]


class TestCaseOp13_TraitsValid_PartialOverride(HttpRunner):
    """OP#13 - descendant provides a concrete value for a field that the ancestor
    only had as `default`. This is allowed (default is not a concrete assignment)."""

    config = Config("OP#13 - Partial override of defaulted ancestor").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.part.v1~",
            _trait_event_meta("part"),
            "register trait-type (defaults present)",
        ),
        _register(
            "gts://gts.x.test13.h.part.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.part.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host (no x-gts-traits — relies on defaults)",
        ),
        _register_derived(
            "gts://gts.x.test13.h.part.event.v1~x.test13._.override_default.v1~",
            "gts://gts.x.test13.h.part.event.v1~",
            {"x-gts-traits": {"topicRef": TOPIC_REF_ORDERS}},
            "register derived overriding the default topicRef with a concrete value",
        ),
        _validate_type_schema(
            "gts.x.test13.h.part.event.v1~x.test13._.override_default.v1~",
            True,
            "validate - first concrete assignment wins; defaults aren't 'set'",
        ),
    ]


class TestCaseOp13_TraitsValid_BaseConcreteSomeFields(HttpRunner):
    """OP#13 - base host sets some trait values concretely; derived adds the rest.

    (Replaces the old TraitsValid_BothKeywordsInSameSchema test — in the new model
    `x-gts-traits-schema` lives only on the base, but `x-gts-traits` can appear at
    any level. The mid-level can both attach a derived trait-type AND set values.)
    """

    config = Config("OP#13 - Concrete values distributed across chain").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.distr.v1~",
            _trait_event_meta("distr", with_topic_default=False, with_retention_default=False),
            "register trait-type (no defaults)",
        ),
        _register(
            "gts://gts.x.test13.h.distr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.distr.v1~",
                "x-gts-traits": {"topicRef": TOPIC_REF_DEFAULT},
                "x-gts-abstract": True,
                "properties": {"id": {"type": "string"}},
            },
            "register base host with topicRef set (abstract until retention is set)",
        ),
        _register_derived(
            "gts://gts.x.test13.h.distr.event.v1~x.test13._.complete.v1~",
            "gts://gts.x.test13.h.distr.event.v1~",
            {"x-gts-traits": {"retention": "P90D"}},
            "register derived adding retention value",
        ),
        _validate_type_schema(
            "gts.x.test13.h.distr.event.v1~x.test13._.complete.v1~",
            True,
            "validate - merged values resolve all fields",
        ),
    ]


class TestCaseOp13_TraitsInvalid_3Level_MissingInLeaf(HttpRunner):
    """OP#13 - 3-level chain; intermediate is abstract and underspecified;
    leaf is concrete but also underspecified. Leaf is invalid.
    """

    config = Config("OP#13 - 3-level chain missing field in leaf").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.l3miss.v1~",
            _trait_event_meta("l3miss", with_topic_default=False, with_retention_default=False),
            "register trait-type (no defaults)",
        ),
        _register(
            "gts://gts.x.test13.h.l3miss.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.l3miss.v1~",
                "x-gts-abstract": True,
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.l3miss.event.v1~x.test13._.mid.v1~",
            "gts://gts.x.test13.h.l3miss.event.v1~",
            {
                "x-gts-traits": {"retention": "P60D"},
                "x-gts-abstract": True,
            },
            "register abstract mid (sets retention only)",
        ),
        _register_derived(
            "gts://gts.x.test13.h.l3miss.event.v1~x.test13._.mid.v1~x.test13._.leaf.v1~",
            "gts://gts.x.test13.h.l3miss.event.v1~x.test13._.mid.v1~",
            {},
            "register concrete leaf without topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.h.l3miss.event.v1~x.test13._.mid.v1~x.test13._.leaf.v1~",
            False,
            "validate should fail - topicRef unresolved at concrete leaf",
        ),
    ]


class TestCaseOp13_TraitsInvalid_OverrideInChain(HttpRunner):
    """OP#13 - immutable-once-set: descendant cannot change ancestor's concrete trait value."""

    config = Config("OP#13 - Override of concrete ancestor value").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.ovr.v1~",
            _trait_event_meta("ovr"),
            "register trait-type (defaults present)",
        ),
        _register(
            "gts://gts.x.test13.h.ovr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.ovr.v1~",
                "x-gts-traits": {"retention": "P30D"},
                "properties": {"id": {"type": "string"}},
            },
            "register base host concretely setting retention=P30D",
        ),
        _register_derived(
            "gts://gts.x.test13.h.ovr.event.v1~x.test13._.try_override.v1~",
            "gts://gts.x.test13.h.ovr.event.v1~",
            {"x-gts-traits": {"retention": "P90D"}},
            "register derived attempting to override retention",
        ),
        _validate_type_schema(
            "gts.x.test13.h.ovr.event.v1~x.test13._.try_override.v1~",
            False,
            "validate should fail - immutable-once-set violated",
        ),
    ]


class TestCaseOp13_TraitsInvalid_OverrideTopicRef3Level(HttpRunner):
    """OP#13 - 3-level chain; mid sets topicRef; leaf tries to change it. Leaf invalid."""

    config = Config("OP#13 - 3-level override of topicRef").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.ovr3.v1~",
            _trait_event_meta("ovr3"),
            "register trait-type (defaults present)",
        ),
        _register(
            "gts://gts.x.test13.h.ovr3.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.ovr3.v1~",
                "x-gts-abstract": True,
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base",
        ),
        _register_derived(
            "gts://gts.x.test13.h.ovr3.event.v1~x.test13._.audit.v1~",
            "gts://gts.x.test13.h.ovr3.event.v1~",
            {
                "x-gts-traits": {"topicRef": TOPIC_REF_AUDIT},
                "x-gts-abstract": True,
            },
            "register abstract mid concretely setting topicRef=audit",
        ),
        _register_derived(
            "gts://gts.x.test13.h.ovr3.event.v1~x.test13._.audit.v1~x.test13._.notif_leaf.v1~",
            "gts://gts.x.test13.h.ovr3.event.v1~x.test13._.audit.v1~",
            {"x-gts-traits": {"topicRef": TOPIC_REF_NOTIF}},
            "register leaf attempting to change topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.h.ovr3.event.v1~x.test13._.audit.v1~x.test13._.notif_leaf.v1~",
            False,
            "validate should fail - leaf overrides mid's concrete topicRef",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ChangeDefaultInMid(HttpRunner):
    """OP#13 - changing a `default` declared in an ancestor trait-type is forbidden.

    Expressed via parallel trait-type derivation: a derived trait-type that redeclares
    a property with a different `default` is invalid (OP#12 on the trait-type chain).
    """

    config = Config("OP#13 - Default override in derived trait-type").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.chgdfl.v1~",
            _trait_event_meta("chgdfl"),
            "register base trait-type (retention default=P30D)",
        ),
        # derived trait-type changing the default for retention to P365D — invalid
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.chgdfl.v1~x.test13._.bad.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.chgdfl.v1~"}],
                "properties": {
                    "retention": {"type": "string", "default": "P365D"},
                },
            },
            "register derived trait-type changing retention default",
        ),
        _validate_type_schema(
            "gts.x.test13.t.chgdfl.v1~x.test13._.bad.v1~",
            False,
            "validate should fail - default redeclared with different value",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ConstraintViolation(HttpRunner):
    """OP#13 - trait value violates a JSON Schema constraint declared in the trait-type."""

    config = Config("OP#13 - Trait value constraint violation").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.cstr.v1~",
            {
                "type": "object",
                "properties": {
                    "retentionDays": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 3650,
                        "default": 30,
                    },
                },
            },
            "register trait-type (retentionDays 1..3650)",
        ),
        _register(
            "gts://gts.x.test13.h.cstr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.cstr.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.cstr.event.v1~x.test13._.too_long.v1~",
            "gts://gts.x.test13.h.cstr.event.v1~",
            {"x-gts-traits": {"retentionDays": 99999}},
            "register derived with retentionDays out of range",
        ),
        _validate_type_schema(
            "gts.x.test13.h.cstr.event.v1~x.test13._.too_long.v1~",
            False,
            "validate should fail - 99999 exceeds maximum",
        ),
    ]


class TestCaseOp13_TraitsInvalid_MinimumViolation(HttpRunner):
    """OP#13 - integer trait value below the minimum constraint."""

    config = Config("OP#13 - Minimum violation").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.mn.v1~",
            {
                "type": "object",
                "properties": {
                    "retentionDays": {
                        "type": "integer",
                        "minimum": 7,
                        "default": 30,
                    },
                },
            },
            "register trait-type",
        ),
        _register(
            "gts://gts.x.test13.h.mn.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.mn.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.mn.event.v1~x.test13._.too_short.v1~",
            "gts://gts.x.test13.h.mn.event.v1~",
            {"x-gts-traits": {"retentionDays": 1}},
            "register derived with retentionDays below minimum",
        ),
        _validate_type_schema(
            "gts.x.test13.h.mn.event.v1~x.test13._.too_short.v1~",
            False,
            "validate should fail - 1 < minimum 7",
        ),
    ]


# ---------------------------------------------------------------------------
# Trait-type derivation via parallel inheritance (replaces "ref-based" /
# "narrowing" / "AP-blocks-extension" composition tests of the old model)
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitTypeDerivation_Narrowing_Valid(HttpRunner):
    """OP#13 - derived trait-type may narrow constraints (compatible refinement).

    Replaces TraitsValid_NarrowingInDerived from the old model.
    """

    config = Config("OP#13 - Trait-type narrowing accepted").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.narrow.v1~",
            {
                "type": "object",
                "properties": {
                    "retentionDays": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 3650,
                        "default": 30,
                    },
                },
            },
            "register base trait-type",
        ),
        # derived trait-type tightening the range
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.narrow.v1~x.test13._.shortlived.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.narrow.v1~"}],
                "properties": {
                    "retentionDays": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                        "default": 30,
                    },
                },
            },
            "register derived trait-type narrowing maximum to 30",
        ),
        _validate_type_schema(
            "gts.x.test13.t.narrow.v1~x.test13._.shortlived.v1~",
            True,
            "validate - narrowing is a valid OP#12 derivation",
        ),
    ]


class TestCaseOp13_TraitTypeDerivation_LooseningViolation(HttpRunner):
    """OP#13 - derived trait-type cannot loosen a constraint of its parent.

    Replaces TraitsInvalid_NarrowingViolation.
    """

    config = Config("OP#13 - Trait-type loosening rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.loose.v1~",
            {
                "type": "object",
                "properties": {
                    "retentionDays": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                        "default": 30,
                    },
                },
            },
            "register base trait-type (max=30)",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.loose.v1~x.test13._.longer.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.loose.v1~"}],
                "properties": {
                    "retentionDays": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 3650,
                        "default": 30,
                    },
                },
            },
            "register derived trait-type loosening max to 3650",
        ),
        _validate_type_schema(
            "gts.x.test13.t.loose.v1~x.test13._.longer.v1~",
            False,
            "validate should fail - loosening violates OP#12",
        ),
    ]


class TestCaseOp13_TraitTypeDerivation_ExtendField_Valid(HttpRunner):
    """OP#13 - derived trait-type can add new fields (replaces RefBasedTraitSchema).

    A derived trait-type adds an `auditRetention` field; host hierarchy resolves it.
    """

    config = Config("OP#13 - Trait-type extends with new field").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.ext.v1~",
            _trait_event_meta("ext"),
            "register base trait-type",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.ext.v1~x.test13._.audited.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.ext.v1~"}],
                "properties": {
                    "auditRetention": {"type": "string", "default": "P365D"},
                },
            },
            "register derived trait-type adding auditRetention",
        ),
        _validate_type_schema(
            "gts.x.test13.t.ext.v1~x.test13._.audited.v1~",
            True,
            "validate derived trait-type",
        ),
    ]


class TestCaseOp13_TraitTypeDerivation_DefaultsInherited_Valid(HttpRunner):
    """OP#13 - defaults declared in a base trait-type are visible through derivation.

    Replaces TraitsValid_DefaultsFromRefSchema.
    """

    config = Config("OP#13 - Defaults from base trait-type cover derived").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.dflinh.v1~",
            _trait_event_meta("dflinh"),
            "register base trait-type (defaults)",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.dflinh.v1~x.test13._.audited.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.dflinh.v1~"}],
                "properties": {
                    "auditRetention": {"type": "string", "default": "P365D"},
                },
            },
            "register derived trait-type adding auditRetention (default)",
        ),
        _register(
            "gts://gts.x.test13.h.dflinh.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.dflinh.v1~x.test13._.audited.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register host attaching the derived trait-type",
        ),
        _validate_type_schema(
            "gts.x.test13.h.dflinh.event.v1~",
            True,
            "validate - all defaults inherited, host is trait-complete",
        ),
    ]


class TestCaseOp13_TraitsInvalid_RefBasedMissingTrait(HttpRunner):
    """OP#13 - trait-type required field with no default; derived host doesn't set it.

    Replaces TraitsInvalid_RefBasedMissingTrait under the new model.
    """

    config = Config("OP#13 - Required field in trait-type unresolved").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.reqf.v1~",
            {
                "type": "object",
                "required": ["topicRef"],
                "properties": {
                    "topicRef": {"type": "string"},
                    "retention": {"type": "string", "default": "P30D"},
                },
            },
            "register trait-type with required topicRef and no default",
        ),
        _register(
            "gts://gts.x.test13.h.reqf.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.reqf.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host (no traits provided)",
        ),
        _validate_type_schema(
            "gts.x.test13.h.reqf.event.v1~",
            False,
            "validate should fail - concrete host with unresolved required field",
        ),
    ]


# ---------------------------------------------------------------------------
# Parallel derivation (host-type and trait-type chains run in parallel)
# ---------------------------------------------------------------------------


class TestCaseOp13_ParallelDerivation_DescendantTraitTypeDerivedFromAncestor_Ok(HttpRunner):
    """OP#13 §9.7.4 - descendant host's trait-type is derived from ancestor's. Valid."""

    config = Config("OP#13 - Parallel derivation OK").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.pard.base.v1~",
            _trait_event_meta("pardbase"),
            "register base trait-type",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.pard.base.v1~x.test13._.audit_meta.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.pard.base.v1~"}],
                "properties": {
                    "auditRetention": {"type": "string", "default": "P365D"},
                },
            },
            "register derived trait-type adding auditRetention",
        ),
        _register(
            "gts://gts.x.test13.h.pard.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.pard.base.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register host base attaching base trait-type",
        ),
        _register_derived(
            "gts://gts.x.test13.h.pard.event.v1~x.test13._.audit_evt.v1~",
            "gts://gts.x.test13.h.pard.event.v1~",
            {
                "x-gts-traits-schema": "gts://gts.x.test13.t.pard.base.v1~x.test13._.audit_meta.v1~",
            },
            "register derived host attaching derived trait-type (parallel chain)",
        ),
        _validate_type_schema(
            "gts.x.test13.h.pard.event.v1~x.test13._.audit_evt.v1~",
            True,
            "validate - parallel derivation is valid",
        ),
    ]


class TestCaseOp13_ParallelDerivation_DescendantTraitTypeNotDerived_Rejected(HttpRunner):
    """OP#13 §9.7.4 - descendant attaches a trait-type that is NOT derived from
    the ancestor's trait-type. Parallel-derivation rule violated.
    """

    config = Config("OP#13 - Parallel derivation: unrelated trait-type rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.parX.familyA.v1~",
            _trait_event_meta("parXa"),
            "register trait-type family A",
        ),
        _register_trait_type(
            "gts://gts.x.test13.t.parX.familyB.v1~",
            _trait_event_meta("parXb"),
            "register trait-type family B (unrelated to A)",
        ),
        _register(
            "gts://gts.x.test13.h.parX.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.parX.familyA.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register host base attaching trait-type family A",
        ),
        _register_derived(
            "gts://gts.x.test13.h.parX.event.v1~x.test13._.swap.v1~",
            "gts://gts.x.test13.h.parX.event.v1~",
            {
                "x-gts-traits-schema": "gts://gts.x.test13.t.parX.familyB.v1~",
            },
            "register derived host attaching unrelated trait-type family B",
        ),
        _validate_type_schema(
            "gts.x.test13.h.parX.event.v1~x.test13._.swap.v1~",
            False,
            "validate should fail - trait-type not in parent's chain",
        ),
    ]


class TestCaseOp13_ParallelDerivation_DescendantOverridesDefaulted_Ok(HttpRunner):
    """OP#13 - ancestor relied on `default`; descendant provides a concrete value.

    This is allowed (default is not a concrete assignment).
    """

    config = Config("OP#13 - Default override is first concrete assignment").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.parovr.v1~",
            _trait_event_meta("parovr"),
            "register trait-type (defaults)",
        ),
        _register(
            "gts://gts.x.test13.h.parovr.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.parovr.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host (no traits set; defaults apply)",
        ),
        _register_derived(
            "gts://gts.x.test13.h.parovr.event.v1~x.test13._.concrete.v1~",
            "gts://gts.x.test13.h.parovr.event.v1~",
            {"x-gts-traits": {"retention": "P365D"}},
            "register derived providing concrete retention",
        ),
        _validate_type_schema(
            "gts.x.test13.h.parovr.event.v1~x.test13._.concrete.v1~",
            True,
            "validate - defaults are not 'set'; descendant may assign",
        ),
    ]


# ---------------------------------------------------------------------------
# Abstract / concrete trait completeness (validity-by-definition rule)
# ---------------------------------------------------------------------------


class TestCaseOp13_AbstractHost_RequiredTraitUnresolved_Ok(HttpRunner):
    """OP#13 §9.7.5 - x-gts-abstract:true host is exempt from completeness checks."""

    config = Config("OP#13 - Abstract host with unresolved traits OK").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.absok.v1~",
            {
                "type": "object",
                "required": ["topicRef"],
                "properties": {
                    "topicRef": {"type": "string"},
                },
            },
            "register trait-type with required topicRef (no default)",
        ),
        _register(
            "gts://gts.x.test13.h.absok.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.absok.v1~",
                "x-gts-abstract": True,
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base host (no x-gts-traits)",
        ),
        _validate_type_schema(
            "gts.x.test13.h.absok.event.v1~",
            True,
            "validate - abstract types are exempt from completeness",
        ),
    ]


class TestCaseOp13_AbstractToConcrete_DescendantResolves_Ok(HttpRunner):
    """OP#13 - abstract base with gaps + concrete descendant that closes them."""

    config = Config("OP#13 - Concrete descendant resolves abstract gaps").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.a2c.v1~",
            {
                "type": "object",
                "required": ["topicRef"],
                "properties": {
                    "topicRef": {"type": "string"},
                    "retention": {"type": "string", "default": "P30D"},
                },
            },
            "register trait-type (topicRef required, no default)",
        ),
        _register(
            "gts://gts.x.test13.h.a2c.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.a2c.v1~",
                "x-gts-abstract": True,
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.a2c.event.v1~x.test13._.concrete.v1~",
            "gts://gts.x.test13.h.a2c.event.v1~",
            {"x-gts-traits": {"topicRef": TOPIC_REF_ORDERS}},
            "register concrete derived providing topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.h.a2c.event.v1~x.test13._.concrete.v1~",
            True,
            "validate - concrete descendant resolves required field",
        ),
    ]


class TestCaseOp13_AbstractToConcrete_DescendantDoesNotResolve_Rejected(HttpRunner):
    """OP#13 - abstract base with gaps; concrete descendant ALSO leaves gaps. Invalid."""

    config = Config("OP#13 - Concrete descendant leaves required gap").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.a2cbad.v1~",
            {
                "type": "object",
                "required": ["topicRef"],
                "properties": {
                    "topicRef": {"type": "string"},
                    "retention": {"type": "string", "default": "P30D"},
                },
            },
            "register trait-type (topicRef required, no default)",
        ),
        _register(
            "gts://gts.x.test13.h.a2cbad.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.a2cbad.v1~",
                "x-gts-abstract": True,
                "properties": {"id": {"type": "string"}},
            },
            "register abstract base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.a2cbad.event.v1~x.test13._.still_open.v1~",
            "gts://gts.x.test13.h.a2cbad.event.v1~",
            {},
            "register concrete derived without filling topicRef",
        ),
        _validate_type_schema(
            "gts.x.test13.h.a2cbad.event.v1~x.test13._.still_open.v1~",
            False,
            "validate should fail - non-abstract concrete host has unresolved required",
        ),
    ]


# ---------------------------------------------------------------------------
# MAJOR version pinning of trait-types
# ---------------------------------------------------------------------------


class TestCaseOp13_MajorVersionPin_V1ToV2_Rejected(HttpRunner):
    """OP#13 §9.7.6 - host pins MAJOR v1 of trait-type; descendant trying to attach v2
    is a different family, not a valid parallel-derivation chain. Rejected.
    """

    config = Config("OP#13 - MAJOR version switch rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.major.v1~",
            _trait_event_meta("majorV1"),
            "register trait-type v1",
        ),
        _register_trait_type(
            "gts://gts.x.test13.t.major.v2~",
            _trait_event_meta("majorV2"),
            "register trait-type v2 (separate family)",
        ),
        _register(
            "gts://gts.x.test13.h.major.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.major.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register host attaching trait-type v1",
        ),
        _register_derived(
            "gts://gts.x.test13.h.major.event.v1~x.test13._.v2_attempt.v1~",
            "gts://gts.x.test13.h.major.event.v1~",
            {
                "x-gts-traits-schema": "gts://gts.x.test13.t.major.v2~",
            },
            "register derived host attaching v2 trait-type",
        ),
        _validate_type_schema(
            "gts.x.test13.h.major.event.v1~x.test13._.v2_attempt.v1~",
            False,
            "validate should fail - v2 is not derived from v1",
        ),
    ]


# ---------------------------------------------------------------------------
# Validation via /validate-entity (instance-side)
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitsValid_ValidateEntity(HttpRunner):
    """OP#13 - validate a registered host type schema via /validate-entity."""

    config = Config("OP#13 - validate-entity passes for valid host").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.vent.v1~",
            _trait_event_meta("vent"),
            "register trait-type",
        ),
        _register(
            "gts://gts.x.test13.h.vent.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.vent.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.vent.event.v1~x.test13._.complete.v1~",
            "gts://gts.x.test13.h.vent.event.v1~",
            {"x-gts-traits": {"topicRef": TOPIC_REF_ORDERS, "retention": "P90D"}},
            "register complete derived host",
        ),
        _validate_entity(
            "gts.x.test13.h.vent.event.v1~x.test13._.complete.v1~",
            True,
            "validate-entity should pass for trait-complete host schema",
        ),
    ]


class TestCaseOp13_TraitsInvalid_ValidateEntity_MissingTrait(HttpRunner):
    """OP#13 - validate-entity fails for a host schema with unresolved required trait."""

    config = Config("OP#13 - validate-entity fails for incomplete host").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.ventm.v1~",
            {
                "type": "object",
                "required": ["topicRef"],
                "properties": {
                    "topicRef": {"type": "string"},
                },
            },
            "register trait-type (topicRef required, no default)",
        ),
        _register(
            "gts://gts.x.test13.h.ventm.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.ventm.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register base host (concrete, incomplete)",
        ),
        _validate_entity(
            "gts.x.test13.h.ventm.event.v1~",
            False,
            "validate-entity should fail - unresolved required trait field",
        ),
    ]


# ---------------------------------------------------------------------------
# Edge cases — base schema without traits, instance with trait keywords, etc.
# ---------------------------------------------------------------------------


class TestCaseOp13_TraitsValid_BaseSchemaNoTraits(HttpRunner):
    """OP#13 - a host-type that does NOT attach a trait-type is fine. No completeness check."""

    config = Config("OP#13 - Host without trait-type OK").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.h.notraits.event.v1~",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            },
            "register base host with no x-gts-traits-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.h.notraits.event.v1~",
            True,
            "validate - no traits attached, nothing to validate",
        ),
    ]


class TestCaseOp13_TraitsInvalid_DerivedHasTraitsButNoTraitSchema(HttpRunner):
    """OP#13 - derived host provides `x-gts-traits` but no trait-type is in the chain.

    This is a meaningless declaration and is rejected.
    """

    config = Config("OP#13 - x-gts-traits without trait-type rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.test13.h.notrt.event.v1~",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            },
            "register base host (no trait-type attached)",
        ),
        _register_derived(
            "gts://gts.x.test13.h.notrt.event.v1~x.test13._.has_traits.v1~",
            "gts://gts.x.test13.h.notrt.event.v1~",
            {"x-gts-traits": {"random": "value"}},
            "register derived with x-gts-traits but no trait-type in chain",
        ),
        _validate_type_schema(
            "gts.x.test13.h.notrt.event.v1~x.test13._.has_traits.v1~",
            False,
            "validate should fail - x-gts-traits used without trait-type in chain",
        ),
    ]


class TestCaseOp13_TraitsInvalid_TraitsSchemaNotAString(HttpRunner):
    """OP#13 - x-gts-traits-schema is not a string. Invalid value type.

    Replaces TraitsInvalid_TraitsSchemaNotObject — value type changed in the new model.
    """

    config = Config("OP#13 - x-gts-traits-schema must be a string").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.h.bad_ts.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": {"type": "object"},  # old-style inline schema
                "properties": {"id": {"type": "string"}},
            },
            "register host with inline-object x-gts-traits-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.h.bad_ts.event.v1~",
            False,
            "validate should fail - x-gts-traits-schema is not a string URN",
        ),
    ]


class TestCaseOp13_TraitsInvalid_TraitsSchemaNotValidUrn(HttpRunner):
    """OP#13 - x-gts-traits-schema string is not a valid GTS Type URN."""

    config = Config("OP#13 - x-gts-traits-schema invalid URN").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.h.bad_urn.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": "not-a-gts-urn",
                "properties": {"id": {"type": "string"}},
            },
            "register host with malformed trait-type URN",
        ),
        _validate_type_schema(
            "gts.x.test13.h.bad_urn.event.v1~",
            False,
            "validate should fail - URN is not a valid GTS Type identifier",
        ),
    ]


class TestCaseOp13_TraitsInvalid_TraitsInInstance(HttpRunner):
    """OP#13 - x-gts-traits / x-gts-traits-schema MUST NOT appear in instance documents."""

    config = Config("OP#13 - Trait keywords in instance rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.inst.v1~",
            _trait_event_meta("inst"),
            "register trait-type",
        ),
        _register(
            "gts://gts.x.test13.h.inst.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.inst.v1~",
                "properties": {
                    "id": {"type": "string"},
                },
            },
            "register host",
        ),
        _post_schema_raw(
            {
                "id": "gts.x.test13.h.inst.event.v1~x.test13._.bad_inst.v1",
                "x-gts-traits": {"topicRef": TOPIC_REF_ORDERS},
            },
            "register an instance with x-gts-traits leaked into it",
        ),
        _validate_entity(
            "gts.x.test13.h.inst.event.v1~x.test13._.bad_inst.v1",
            False,
            "validate should fail - x-gts-traits in instance is illegal",
        ),
    ]


class TestCaseOp13_TraitsInvalid_BaseHasTraitsButNoTraitSchema(HttpRunner):
    """OP#13 - a base host declares x-gts-traits without declaring x-gts-traits-schema."""

    config = Config("OP#13 - Base x-gts-traits without trait-type rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.h.lone_traits.event.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits": {"random": "value"},
                "properties": {"id": {"type": "string"}},
            },
            "register base host with x-gts-traits but no x-gts-traits-schema",
        ),
        _validate_type_schema(
            "gts.x.test13.h.lone_traits.event.v1~",
            False,
            "validate should fail - x-gts-traits requires a trait-type in chain",
        ),
    ]


# ---------------------------------------------------------------------------
# `const` narrowing in trait values (carried over)
# ---------------------------------------------------------------------------


class TestCaseOp13_ConstNarrowing_LeafMatches_Ok(HttpRunner):
    """OP#13 - mid sets const via derived trait-type; leaf provides that exact value. OK."""

    config = Config("OP#13 - const narrowing leaf matches").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.const.base.v1~",
            {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                },
            },
            "register base trait-type",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.const.base.v1~x.test13._.audit_only.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.const.base.v1~"}],
                "properties": {
                    "channel": {"type": "string", "const": "audit"},
                },
            },
            "register derived trait-type narrowing channel to const 'audit'",
        ),
        _register(
            "gts://gts.x.test13.h.const.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.const.base.v1~x.test13._.audit_only.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register host attaching the narrowed trait-type",
        ),
        _register_derived(
            "gts://gts.x.test13.h.const.event.v1~x.test13._.match.v1~",
            "gts://gts.x.test13.h.const.event.v1~",
            {"x-gts-traits": {"channel": "audit"}},
            "register derived providing matching const value",
        ),
        _validate_type_schema(
            "gts.x.test13.h.const.event.v1~x.test13._.match.v1~",
            True,
            "validate - leaf value matches const constraint",
        ),
    ]


class TestCaseOp13_ConstNarrowing_LeafViolation_Rejected(HttpRunner):
    """OP#13 - mid declares const via derived trait-type; leaf supplies a different value."""

    config = Config("OP#13 - const narrowing leaf violation").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.constv.base.v1~",
            {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                },
            },
            "register base trait-type",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.constv.base.v1~x.test13._.audit_only.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.test13.t.constv.base.v1~"}],
                "properties": {
                    "channel": {"type": "string", "const": "audit"},
                },
            },
            "register derived trait-type narrowing channel to const 'audit'",
        ),
        _register(
            "gts://gts.x.test13.h.constv.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.constv.base.v1~x.test13._.audit_only.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register host",
        ),
        _register_derived(
            "gts://gts.x.test13.h.constv.event.v1~x.test13._.mismatch.v1~",
            "gts://gts.x.test13.h.constv.event.v1~",
            {"x-gts-traits": {"channel": "notification"}},
            "register derived with channel value not matching const",
        ),
        _validate_type_schema(
            "gts.x.test13.h.constv.event.v1~x.test13._.mismatch.v1~",
            False,
            "validate should fail - leaf value violates const",
        ),
    ]


# ---------------------------------------------------------------------------
# Cycle detection (trait-type cycles via x-gts-traits-schema recursion)
# ---------------------------------------------------------------------------


class TestCaseOp13_CycleDetection_SelfRef_Rejected(HttpRunner):
    """OP#13 - a trait-type attaches itself as its own trait-type (self-cycle).

    The spec permits recursion in principle, but registries MUST detect cycles
    of finite depth that would otherwise loop forever during effective-type
    resolution.
    """

    config = Config("OP#13 - self-referential trait-type rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.selfref.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.selfref.v1~",
                "properties": {
                    "anything": {"type": "string"},
                },
            },
            "register a trait-type that references itself",
        ),
        _validate_type_schema(
            "gts.x.test13.t.selfref.v1~",
            False,
            "validate should fail - self-cycle detected",
        ),
    ]


class TestCaseOp13_CycleDetection_TwoNodeCycle_Rejected(HttpRunner):
    """OP#13 - trait-type A attaches B as its trait-type; B attaches A. Cycle."""

    config = Config("OP#13 - two-node trait-type cycle rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        # In a registry with single-pass registration, A would have to forward-ref B.
        # Some implementations require both to exist; we register A first as a bare type,
        # then register B attaching A, then update A to attach B.
        # For an interop-friendly test, we use _post_schema_raw to upsert both as cycle.
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.cycleA.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.cycleB.v1~",
                "properties": {"a": {"type": "string"}},
            },
            "register A pointing at B (forward-ref)",
        ),
        _post_schema_raw(
            {
                "$$id": "gts://gts.x.test13.t.cycleB.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.cycleA.v1~",
                "properties": {"b": {"type": "string"}},
            },
            "register B pointing at A (closes the cycle)",
        ),
        _validate_type_schema(
            "gts.x.test13.t.cycleA.v1~",
            False,
            "validate should fail - 2-node trait-type cycle",
        ),
    ]


# ---------------------------------------------------------------------------
# Instance validation (defense-in-depth for OP#6)
# ---------------------------------------------------------------------------


class TestCaseOp13_InstanceValidation_TypeWithUnresolvedTraits_Rejected(HttpRunner):
    """OP#13 / OP#6 - validate-entity on an instance whose type is trait-incomplete.

    Even if a registry somehow accepted such a type, OP#6 MUST reject instance
    validation as defense-in-depth.
    """

    config = Config("OP#13 - instance of trait-incomplete type rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register_trait_type(
            "gts://gts.x.test13.t.inccpl.v1~",
            {
                "type": "object",
                "required": ["topicRef"],
                "properties": {
                    "topicRef": {"type": "string"},
                },
            },
            "register trait-type (topicRef required, no default)",
        ),
        _register(
            "gts://gts.x.test13.h.inccpl.event.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": "gts://gts.x.test13.t.inccpl.v1~",
                "properties": {"id": {"type": "string"}},
            },
            "register concrete host without resolving topicRef",
        ),
        _validate_entity(
            "gts.x.test13.h.inccpl.event.v1~",
            False,
            "validate-entity should fail - host type is trait-incomplete",
        ),
    ]


if __name__ == "__main__":
    TestCaseOp13_TraitsValid_AllResolved().test_start()
