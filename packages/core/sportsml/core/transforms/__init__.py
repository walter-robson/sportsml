"""Thin wrappers around Dagster ``@asset`` patterns.

v0: empty surface. Sport plugins declare assets directly with Dagster's
own decorators; we keep this module so future common helpers (typed
asset factory, schema-validation wrappers) have a home.
"""

from __future__ import annotations

# TODO(v0.5): Provide a typed-asset factory that auto-derives output schema
# from an ObjectType subclass.
