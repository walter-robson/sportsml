"""Drop a .pth file into the active venv so all editable package paths resolve.

Hatch's wheel-level editable install registers only one path per package name;
because we use a shared ``sportsml/`` namespace across many sport plugin
wheels, we need every package directory on ``sys.path`` to assemble the
namespace correctly. This is a single source of truth for that path list.
"""

from __future__ import annotations

import site
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "api",
    REPO_ROOT / "packages" / "sports" / "basketball" / "nba",
    REPO_ROOT / "packages" / "sports" / "basketball" / "ncaa",
    REPO_ROOT / "packages" / "sports" / "basketball" / "euroleague",
    REPO_ROOT / "packages" / "sports" / "football" / "nfl",
    REPO_ROOT / "packages" / "sports" / "baseball" / "mlb",
    REPO_ROOT / "packages" / "sports" / "hockey" / "nhl",
    REPO_ROOT / "dagster_project",
]


def main() -> int:
    site_dirs = site.getsitepackages()
    target_site = next((Path(d) for d in site_dirs if d.endswith("site-packages")), None)
    if target_site is None:
        print("No site-packages directory found.", file=sys.stderr)
        return 1
    pth_file = target_site / "sportsml-paths.pth"
    pth_file.write_text("\n".join(str(p) for p in PACKAGE_PATHS) + "\n")
    print(f"Wrote {pth_file} ({len(PACKAGE_PATHS)} paths).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
