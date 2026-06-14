"""sportsml.core — sport-agnostic abstractions for the platform.

Public surface:
- ``ontology`` — base ObjectType / Property / Link declarations + core types.
- ``models`` — ModelTemplate ABC, run lifecycle, registry, tenant context.
- ``apps`` — App ABC and registry.
- ``tenancy`` — TenantContext factory.

Sport-specific code lives in ``sportsml.sports.*`` and is wired in via the
registries here. Nothing in ``sportsml.core`` may import from a sport plugin.
"""

from __future__ import annotations
