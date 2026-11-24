#!/usr/bin/env python3
"""Prose and GridCore content-contract checks for uCore front-end styles.

The ecosystem has exactly two style contracts:

  Prose      PROSE-STANDARDS.md           --usx-*       usx-prose.css
  GridCore   GRIDCORE-LATTICE-SPEC.md     --gridcore-*  gridcore.css

This script enforces the parts of those contracts that can be measured
mechanically. It reads the canonical standards data when it is available and
falls back to an explicit, reported skip when it is not.

Rules
  prose.reference     every var(--usx-*) / var(--gridcore-*) resolves
  prose.literals      no raw colour outside themes, palettes and recipes
  gridcore.palette    --gridcore-palette-N matches the canonical 8 colours
  contract.contrast   theme text and status pairs meet the minimum ratio

Exit codes: 0 clean, 1 violations, 2 unusable input.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCAN_ROOTS = ("packages/usx-tokens", "frontend-vue/src")
DEFINITION_ROOTS = ("packages/usx-tokens",)
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
}
SOURCE_SUFFIXES = {".css", ".scss", ".ts", ".tsx", ".vue"}

TOKEN_NAMESPACES = ("usx", "gridcore")
PROPERTY_DEF = re.compile(r"(--(?:usx|gridcore)-[a-z0-9-]+)\s*:")
PROPERTY_USE = re.compile(r"var\(\s*(--(?:usx|gridcore)-[a-z0-9-]+)\s*(,?)")
HEX_LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b")
COLOR_FUNCTION = re.compile(r"\b(?:rgba?|hsla?)\s*\(", re.IGNORECASE)
PALETTE_DEF = re.compile(r"(--gridcore-palette-(\d+))\s*:\s*([^;]+);")

ALLOW_LITERALS_MARKER = "content-contract: allow-literals"
ALLOW_LITERAL_PATHS = (
    "packages/usx-tokens/tokens/",
    "packages/usx-tokens/themes/",
    "packages/usx-tokens/palettes/",
    "frontend-vue/src/recipes/",
    "frontend-vue/src/styles/themes/",
    # A skin is a palette by definition; it swaps values, it does not consume them.
    "frontend-vue/src/styles/flowbite-skin.css",
    # Recipe gallery renders light and dark fixtures side by side on purpose.
    "frontend-vue/src/surfaces/recipes/",
    # Third-party brand surfaces keep the vendor's colours (Google blue/red/…).
    "frontend-vue/src/surfaces/google/",
    # Chart and diagram series colours are content, emitted into SVG/HTML.
    "frontend-vue/src/utils/svgChartRenderer.ts",
    "frontend-vue/src/utils/diagramHydrator.ts",
    # Banana Studio previews the canonical image/palette presets side by side.
    "frontend-vue/src/surfaces/browserui/panels/BananaStudio.vue",
    # GridCore renderer palette and raster constants are rendering behaviour,
    # not CSS chrome (GRIDCORE_VARIABLEIZATION_SPEC.md §2, out of scope).
    "frontend-vue/src/grid-core/",
    # gridcore.css defines the GridCore contract itself, including its canon
    # palette; the gridcore.palette rule verifies those values instead.
    "frontend-vue/src/styles/gridcore.css",
)

# Defined at runtime by frontend-vue/src/stores/settings.ts. It now also has a
# static default in tokens-typography.css, so nothing is allowlisted here: a
# regression should fail the check.
RUNTIME_INJECTED: set[str] = set()

# Retro display palettes are intentional per USX-STYLE-SPEC.md, so they report
# as warnings until they are confined to the GridCore viewport as the spec asks.
RETRO_THEMES = {"c64", "teletext"}

CONTRAST_PAIRS = (
    ("--usx-color-on-surface", "--usx-color-background", "body text on canvas"),
    ("--usx-color-on-surface-muted", "--usx-color-background", "muted text on canvas"),
    ("--usx-color-on-surface", "--usx-color-surface", "body text on panel"),
    ("--usx-color-on-surface-muted", "--usx-color-surface", "muted text on panel"),
    ("--usx-color-success", "--usx-color-background", "success text on canvas"),
    ("--usx-color-warning", "--usx-color-background", "warning text on canvas"),
    ("--usx-color-danger", "--usx-color-background", "danger text on canvas"),
    ("--usx-color-info", "--usx-color-background", "info text on canvas"),
    ("--usx-color-primary", "--usx-color-primary-surface", "primary text on primary surface"),
    ("--usx-color-success", "--usx-color-success-surface", "success text on success surface"),
    ("--usx-color-warning", "--usx-color-warning-surface", "warning text on warning surface"),
    ("--usx-color-danger", "--usx-color-danger-surface", "danger text on danger surface"),
    ("--usx-color-info", "--usx-color-info-surface", "info text on info surface"),
    ("--usx-color-secondary", "--usx-color-secondary-surface", "secondary text on secondary surface"),
    ("--usx-color-on-primary", "--usx-color-primary", "label on primary"),
    ("--usx-color-on-secondary", "--usx-color-secondary", "label on secondary"),
    ("--usx-color-on-accent", "--usx-color-accent", "label on accent"),
    ("--usx-color-on-success", "--usx-color-success", "label on success"),
    ("--usx-color-on-warning", "--usx-color-warning", "label on warning"),
    ("--usx-color-on-danger", "--usx-color-danger", "label on danger"),
    ("--usx-color-on-info", "--usx-color-info", "label on info"),
)

DEFAULT_MIN_CONTRAST = 4.5
PALETTE_KEYS = ("teletext_primary",)


class Finding:
    """One contract violation or advisory."""

    def __init__(self, rule: str, severity: str, location: str, message: str) -> None:
        self.rule = rule
        self.severity = severity
        self.location = location
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
        }


def relative(path: Path) -> str:
    for base in (REPO_ROOT, REPO_ROOT.parent):
        try:
            return str(path.resolve().relative_to(base))
        except ValueError:
            continue
    return str(path)


def dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[Finding] = []
    for item in findings:
        key = (item.rule, item.location, item.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def iter_sources(roots: list[Path]):
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            # Tests assert on fixture colours; they are not shipped styling.
            if path.name.endswith((".test.ts", ".spec.ts", ".test.tsx")):
                continue
            yield path


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""




def first_line_allows_literals(text: str) -> bool:
    return ALLOW_LITERALS_MARKER in "\n".join(text.splitlines()[:12])


def check_references(sources: list[Path]) -> list[Finding]:
    """Every referenced contract variable must be defined somewhere."""
    defined: set[str] = set()
    uses: dict[str, list[tuple[Path, bool]]] = {}

    for path in sources:
        text = read(path)
        defined.update(PROPERTY_DEF.findall(text))
        for name, fallback in PROPERTY_USE.findall(text):
            uses.setdefault(name, []).append((path, bool(fallback)))

    findings: list[Finding] = []
    for name in sorted(uses):
        if name in defined or name in RUNTIME_INJECTED or name.endswith("-"):
            continue
        for path, has_fallback in uses[name]:
            if has_fallback:
                findings.append(
                    Finding(
                        "prose.reference",
                        "warning",
                        relative(path),
                        f"{name} has no contract definition; only the inline fallback applies",
                    )
                )
            else:
                findings.append(
                    Finding(
                        "prose.reference",
                        "error",
                        relative(path),
                        f"{name} has no contract definition and no fallback",
                    )
                )
    return dedupe(findings)


def check_literals(sources: list[Path]) -> list[Finding]:
    """Colour literals belong to canon files and recipes, not to components."""
    findings: list[Finding] = []
    for path in sources:
        rel = relative(path)
        if any(rel.startswith(prefix) for prefix in ALLOW_LITERAL_PATHS):
            continue
        text = read(path)
        if first_line_allows_literals(text):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*")):
                continue
            hits = HEX_LITERAL.findall(line)
            if COLOR_FUNCTION.search(line):
                hits.append(COLOR_FUNCTION.search(line).group(0).strip() + ")")
            for hit in hits:
                findings.append(
                    Finding(
                        "prose.literals",
                        "error",
                        f"{rel}:{number}",
                        f"raw colour {hit} — use a contract variable",
                    )
                )
    return findings


def resolve_standards_dir() -> Path | None:
    candidates: list[Path] = []
    env = os.environ.get("UDOS_GLOBAL_KNOWLEDGE")
    if env:
        candidates.append(Path(env).expanduser() / "standards")
    candidates.extend(
        [
            REPO_ROOT.parent / "global-knowledge" / "standards",
            REPO_ROOT.parent.parent / "global-knowledge" / "standards",
            Path.home() / "Public" / "global-knowledge" / "standards",
        ]
    )
    for candidate in candidates:
        if (candidate / "USX-STANDARDS.json").is_file():
            return candidate
    return None


def load_palette_sources() -> tuple[dict[str, str] | None, dict[str, str] | None]:
    """Return (gridcore canon, usx copy).

    GridCore owns the lattice palette; USX-STANDARDS keeps a display copy for
    the docs. The checker verifies the code against GridCore and reports drift
    between the two standards files.
    """
    standards = resolve_standards_dir()
    if standards is None:
        return None, None

    gridcore: dict[str, str] | None = None
    usx: dict[str, str] | None = None

    try:
        data = json.loads((standards / "GRIDCORE-STANDARDS.json").read_text(encoding="utf-8"))
        indices = data.get("palette", {}).get("indices")
        if isinstance(indices, list):
            gridcore = {
                str(entry["index"]): str(entry.get("hex", "")).upper()
                for entry in indices
                if isinstance(entry, dict) and "index" in entry
            }
    except (OSError, json.JSONDecodeError):
        gridcore = None

    try:
        data = json.loads((standards / "USX-STANDARDS.json").read_text(encoding="utf-8"))
        for key in PALETTE_KEYS:
            palette = data.get("colors", {}).get(key)
            if isinstance(palette, dict):
                usx = {
                    str(index): str(entry.get("hex", "")).upper()
                    for index, entry in palette.items()
                    if isinstance(entry, dict)
                }
                break
    except (OSError, json.JSONDecodeError):
        usx = None

    return gridcore, usx


def check_palette_compat(
    gridcore: dict[str, str] | None, usx: dict[str, str] | None
) -> list[Finding]:
    """The two standards files must agree on the lattice palette."""
    if gridcore is None or usx is None:
        return []
    findings: list[Finding] = []
    for index in sorted(set(gridcore) | set(usx), key=lambda item: int(item)):
        left, right = gridcore.get(index), usx.get(index)
        if left == right:
            continue
        findings.append(
            Finding(
                "gridcore.palette",
                "warning",
                "global-knowledge/standards",
                f"index {index}: GRIDCORE-STANDARDS has {left or 'none'}, "
                f"USX-STANDARDS has {right or 'none'}",
            )
        )
    return findings



def check_palette(sources: list[Path], canon: dict[str, str] | None) -> list[Finding]:
    """The lattice palette is canon, not theme: it must match the standards data."""
    defined: dict[str, tuple[str, str]] = {}
    palette_home = REPO_ROOT / "frontend-vue" / "src" / "styles" / "gridcore.css"
    for path in [*sources, palette_home] if palette_home.is_file() else sources:
        for name, index, value in PALETTE_DEF.findall(read(path)):
            defined.setdefault(index, (value.strip(), relative(path)))

    if canon is None:
        return [
            Finding(
                "gridcore.palette",
                "warning",
                "global-knowledge/standards/USX-STANDARDS.json",
                "standards data not found; palette equality not verified",
            )
        ]

    findings: list[Finding] = []
    for index in sorted(set(canon) | set(defined), key=lambda item: int(item)):
        expected = canon.get(index)
        actual = defined.get(index)
        if expected is None:
            findings.append(
                Finding("gridcore.palette", "error", actual[1] if actual else "-",
                        f"palette index {index} is not part of the canonical palette")
            )
            continue
        if actual is None:
            findings.append(
                Finding("gridcore.palette", "error", "frontend-vue/src/styles/gridcore.css",
                        f"palette index {index} is missing; canon is {expected}")
            )
            continue
        value, location = actual
        if value.upper() != expected:
            findings.append(
                Finding("gridcore.palette", "error", location,
                        f"palette {index} is {value}; canon is {expected}")
            )
    return findings


HEX_VALUE = re.compile(r"#[0-9a-fA-F]{3,8}")
VAR_IN_VALUE = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*(?:,\s*([^()]*))?\)")
DECLARATION = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;{}]+);")


def parse_hex(value: str) -> tuple[int, int, int] | None:
    match = HEX_VALUE.search(value or "")
    if not match:
        return None
    digits = match.group(0)[1:]
    if len(digits) == 3:
        digits = "".join(char * 2 for char in digits)
    if len(digits) == 8:
        digits = digits[:6]
    if len(digits) != 6:
        return None
    return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def contrast_ratio(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        ratio = value / 255
        return ratio / 12.92 if ratio <= 0.03928 else ((ratio + 0.055) / 1.055) ** 2.4

    def luminance(rgb: tuple[int, int, int]) -> float:
        red, green, blue = (channel(component) for component in rgb)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def resolve_table(table: dict[str, str]) -> dict[str, str]:
    resolved = dict(table)
    for _ in range(8):
        changed = False
        for key, value in list(resolved.items()):
            replacement = VAR_IN_VALUE.sub(
                lambda match: resolved.get(match.group(1), (match.group(2) or "").strip()) or "",
                value,
            )
            if replacement != value:
                resolved[key] = replacement
                changed = True
        if not changed:
            break
    return {key: value for key, value in resolved.items() if "var(" not in value}


def theme_tables(base_file: Path, theme_dir: Path) -> dict[str, dict[str, str]]:
    base = resolve_table(dict(DECLARATION.findall(read(base_file))))
    tables: dict[str, dict[str, str]] = {}
    for path in sorted(theme_dir.glob("*.css")):
        overrides = dict(DECLARATION.findall(read(path)))
        tables[path.stem] = resolve_table({**base, **overrides})
    return tables


def check_contrast(
    base_file: Path, theme_dir: Path, minimum: float
) -> list[Finding]:
    """Each theme must keep its text and status pairs readable on its own canvas."""
    if not base_file.is_file() or not theme_dir.is_dir():
        return [
            Finding(
                "contract.contrast",
                "warning",
                "packages/usx-tokens/themes",
                "theme sources not found; contrast not verified",
            )
        ]

    findings: list[Finding] = []
    for theme, table in theme_tables(base_file, theme_dir).items():
        severity = "warning" if theme in RETRO_THEMES else "error"
        measured = 0
        for foreground, background, label in CONTRAST_PAIRS:
            foreground_rgb = parse_hex(table.get(foreground, ""))
            background_rgb = parse_hex(table.get(background, ""))
            if foreground_rgb is None or background_rgb is None:
                continue
            measured += 1
            ratio = contrast_ratio(foreground_rgb, background_rgb)
            if ratio + 1e-9 < minimum:
                findings.append(
                    Finding(
                        "contract.contrast",
                        severity,
                        f"theme {theme}: {label}",
                        f"{ratio:.2f}:1 is below {minimum:g}:1",
                    )
                )
        if measured == 0:
            findings.append(
                Finding(
                    "contract.contrast",
                    "warning",
                    f"theme {theme}",
                    "no measurable colour pairs; tokens are not plain hex",
                )
            )
    return findings


def collect_sources(roots: list[Path]) -> list[Path]:
    """Scan the requested roots, always including the canonical definition set."""
    unique: dict[Path, Path] = {}
    for path in iter_sources(list(roots) + [REPO_ROOT / value for value in DEFINITION_ROOTS]):
        unique.setdefault(path.resolve(), path)
    return list(unique.values())


ANY_PROPERTY_DEF = re.compile(r"(--([a-z][a-z0-9]*)-[a-z0-9-]+)'?\s*:")
ANY_PROPERTY_USE = re.compile(r"var\(\s*(--([a-z][a-z0-9]*)-[a-z0-9-]+)")

# Prefixes that are documented cross-file scopes. Anything else outside the
# contract namespaces may live in exactly the files that define it.
NAMESPACE_SCOPES = {
    "wf": (
        "frontend-vue/src/styles/usx-workflow-zen.css",
        "frontend-vue/src/surfaces/workflow/WorkflowSurface.vue",
        "frontend-vue/src/surfaces/workflow/panels/TasksPanel.vue",
        "frontend-vue/src/surfaces/workflow/panels/FeedsPanel.vue",
        "frontend-vue/src/surfaces/browserui/BrowserUISurface.vue",
    ),
    "uihub": ("frontend-vue/src/styles/flowbite-skin.css",),
    # EditorPanel exposes --document-* to the markdown editor chrome.
    "document": (
        "frontend-vue/src/skills/organisms/EditorPanel.vue",
        "frontend-vue/src/skills/molecules/editor/MarkdownEditor.vue",
    ),
    # FilepickerSidebar exposes --filepicker-* to the filter rows it hosts.
    "filepicker": (
        "frontend-vue/src/skills/molecules/FilepickerSidebar.vue",
        "frontend-vue/src/skills/molecules/BinderMissionFilter.vue",
        "frontend-vue/src/skills/molecules/WorkspaceFilter.vue",
    ),
}
CONTRACT_NAMESPACES = {"usx", "gridcore"}


def check_namespaces(sources: list[Path]) -> list[Finding]:
    """Local custom properties may not leak across files.

    A component may define its own `--tabs-*` variables. What it may not do is
    consume a prefix that another file owns, or export a local prefix into the
    global cascade: that is how the `--gh-*` / `--hn-*` / `--bs-*` drift started.
    """
    defined: dict[str, set[str]] = {}
    used: dict[str, set[str]] = {}
    locations: dict[tuple[str, str], str] = {}

    for path in sources:
        rel = relative(path)
        if first_line_allows_literals(read(path)):
            continue
        for line_number, line in enumerate(read(path).splitlines(), start=1):
            for name, prefix in ANY_PROPERTY_DEF.findall(line):
                defined.setdefault(prefix, set()).add(rel)
                locations.setdefault((prefix, rel), f"{rel}:{line_number}")
            for name, prefix in ANY_PROPERTY_USE.findall(line):
                used.setdefault(prefix, set()).add(rel)
                locations.setdefault((prefix, rel), f"{rel}:{line_number}")

    findings: list[Finding] = []
    for prefix in sorted(used):
        if prefix in CONTRACT_NAMESPACES:
            continue
        allowed = set(NAMESPACE_SCOPES.get(prefix, ())) | defined.get(prefix, set())
        for rel in sorted(used[prefix] - allowed):
            findings.append(
                Finding(
                    "prose.namespace",
                    "error",
                    locations.get((prefix, rel), rel),
                    f"--{prefix}-* is owned by {', '.join(sorted(defined.get(prefix, {'?'})))} "
                    "and cannot be read here; use a contract token",
                )
            )
    return dedupe(findings)


def run_checks(roots: list[Path], minimum: float) -> list[Finding]:
    sources = collect_sources(roots)
    findings: list[Finding] = []
    findings.extend(check_references(sources))
    findings.extend(check_literals(sources))
    findings.extend(check_namespaces(sources))
    lattice, usx_palette = load_palette_sources()
    findings.extend(check_palette(sources, lattice))
    findings.extend(check_palette_compat(lattice, usx_palette))
    findings.extend(
        check_contrast(
            REPO_ROOT / "packages" / "usx-tokens" / "tokens" / "tokens-color.css",
            REPO_ROOT / "packages" / "usx-tokens" / "themes",
            minimum,
        )
    )
    return findings


RULES = (
    ("prose.reference", "contract references resolve"),
    ("prose.literals", "no raw colour outside canon"),
    ("prose.namespace", "variables stay in a contract namespace"),
    ("gridcore.palette", "lattice palette matches canon"),
    ("contract.contrast", "theme contrast meets the minimum"),
)


def report(findings: list[Finding], limit: int) -> None:
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]

    print("Prose / GridCore content contract")
    for rule, description in RULES:
        rule_errors = sum(1 for item in errors if item.rule == rule)
        rule_warnings = sum(1 for item in warnings if item.rule == rule)
        state = "FAIL" if rule_errors else ("warn" if rule_warnings else "ok")
        print(
            f"  {rule:18} {state:4}  {rule_errors:4d} error(s)  "
            f"{rule_warnings:4d} warning(s)  {description}"
        )

    for group, label in ((errors, "Errors"), (warnings, "Warnings")):
        if not group:
            continue
        print(f"\n{label}:")
        for shown, item in enumerate(group):
            if shown >= limit:
                print(f"  ... {len(group) - limit} more (--json for the full list)")
                break
            print(f"  [{item.rule}] {item.location} — {item.message}")

    print(
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s) "
        f"across {len(findings)} finding(s)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help="path to scan, relative to the repository root (repeatable)",
    )
    parser.add_argument(
        "--min-contrast",
        type=float,
        default=DEFAULT_MIN_CONTRAST,
        help=f"minimum WCAG contrast ratio (default {DEFAULT_MIN_CONTRAST})",
    )
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    parser.add_argument(
        "--limit", type=int, default=40, help="maximum findings printed per severity"
    )
    args = parser.parse_args(argv)

    roots = [
        (Path(value) if Path(value).is_absolute() else REPO_ROOT / value)
        for value in (args.root or DEFAULT_SCAN_ROOTS)
    ]
    if not any(root.exists() for root in roots):
        print("Content contract: no scannable roots found", file=sys.stderr)
        return 2

    findings = run_checks(roots, args.min_contrast)
    if args.json:
        print(json.dumps([item.as_dict() for item in findings], indent=2))
    else:
        report(findings, args.limit)
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

