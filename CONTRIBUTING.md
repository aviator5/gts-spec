# Contributing to GTS Specification

Thank you for your interest in contributing to the Global Type System (GTS) Specification! This document provides guidelines and information for contributors.

## Quick Start

### Prerequisites

- **Git** for version control
- **JSON Schema validator** (optional, for testing schema examples)
- **Python 3.8+** (optional, for running reference implementations)
- **Your favorite editor** (VS Code with JSON Schema support recommended)

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd gts-spec

# Optional: Install Python dependencies for reference implementations
pip install jsonschema

# Optional: Install JSON Schema validator
npm install -g ajv-cli
```

### Repository Layout

```
gts-spec/
├── README.md                 # Main specification document
├── CONTRIBUTING.md           # This file
├── LICENSE                   # License information
└── examples/                 # Example GTS Types and instances
    ├── events/               # Event-related examples
    │   ├── types/            # GTS Type Schemas (JSON Schema documents)
    │   └── instances/        # JSON instance examples
    └── ...                   # Other domain examples
```

## Development Workflow

### 1. Create a Feature Branch or fork the repository

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-event-examples`
- `fix/schema-validation-error`
- `docs/clarify-chaining-rules`
- `spec/minor-version-compatibility`

### 2. Make Your Changes

Follow the specification standards and patterns described below.

### 3. Validate Your Changes

```bash
# Validate all schemas in a directory
ajv compile --strict=false -s "examples/events/types/*.schema.json"

# Run Python reference implementation tests (if available)
python -m pytest tests/
```

### 4. Commit Changes

Follow a structured commit message format:

```text
<type>(<module>): <description>
```

- `<type>`: change category (see table below)
- `<module>` (optional): the area touched (e.g., spec, examples, schemas)
- `<description>`: concise, imperative summary

Accepted commit types:

| Type       | Meaning                                                     |
|------------|-------------------------------------------------------------|
| spec       | Specification changes or clarifications                     |
| fix        | Bug fixes in schemas or examples                            |
| docs       | Documentation updates                                       |
| examples   | Adding or updating example schema representations and instances |
| test       | Adding or modifying validation tests                        |
| style      | Formatting changes (whitespace, JSON formatting, etc.)      |
| chore      | Misc tasks (tooling, scripts)                               |
| breaking   | Backward incompatible specification changes                 |

Examples:

```text
spec(versioning): clarify minor version compatibility rules
fix(schemas): correct `$id` pattern in event schema
examples(idp): add contact_created event instance
test(validation): add schema validation tests
```

Best practices:

- Keep the title concise (ideally ≤ 50 chars)
- Use imperative mood (e.g., "Fix schema", not "Fixed schema")
- Make commits atomic (one logical change per commit)
- Add details in the body when necessary (what/why, not how)
- For breaking changes, either use `spec!:` or include a `BREAKING CHANGE:` footer

Specification development guidelines:

- Follow GTS identifier format rules strictly
- Ensure all schemas use correct `$id` values
- Validate schemas against JSON Schema Draft 7 or later
- Include both GTS Type Schemas (the canonical JSON definitions of types) and GTS Instance examples
- Document any deviations or implementation-specific choices

## Releases

The specification version is declared in `README.md` via a machine-readable marker on the first line:

```html
<!-- gts-spec-version: X.Y -->
```

This marker is the canonical source of truth and is parsed by CI. The visible `> **VERSION**: ...` line below it is for human readers only and may be reworded freely, but its `X.Y` value MUST match the marker. When bumping the spec version, update both lines in the same change.

A versioned Docker image of the conformance test suite is published to GHCR on every git tag matching `vX.Y.Z`, where:

- `X.Y` MUST match the spec version declared in `README.md`. The release workflow enforces this and will fail the build on mismatch.
- `Z` increments independently for changes to the test suite itself (additions, fixes, refactors) within the same spec version.

When the specification moves to the next minor version (e.g. `0.11` → `0.12`), the README version line is updated in the same change, and the next release tag starts at `vX.Y.0`.

### Cutting a release (maintainers only)

Releases are produced from `github.com/GlobalTypeSystem/gts-spec`. The workflow is restricted to that repository; pushing a tag from a fork has no effect.

```bash
git tag v0.11.3
git push origin v0.11.3
```

The [`Release Tests Image`](.github/workflows/release-tests-image.yml) workflow:

1. Verifies the tag's `major.minor` matches the spec version in `README.md`.
2. Builds the test runner image for `linux/amd64` and `linux/arm64`.
3. Pushes it to `ghcr.io/globaltypesystem/gts-spec-tests` with two tags: the exact release `vX.Y.Z` and the rolling per-spec-version `vX.Y`. No floating `latest` tag is published — see `tests/README.md` for the rationale and consumer-side tag selection guidance.
4. Creates a GitHub Release with auto-generated notes.
