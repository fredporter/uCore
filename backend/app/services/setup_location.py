"""Offline setup suggestions from the host's public-domain IANA timezone tables.

Read-only OS dataset, no geolocation, stored state, extra service or clock changes.
"""

from pathlib import Path
from zoneinfo import TZPATH, ZoneInfo, ZoneInfoNotFoundError


def location_catalog(roots=None):
    """Return timezone representative cities and countries; never guess a UTC city."""
    roots = [Path(root) for root in (roots or TZPATH)]
    countries = {}
    locations = {}
    for root in roots:
        try:
            country_lines = (root / "iso3166.tab").read_text().splitlines()
            zone_lines = (root / "zone.tab").read_text().splitlines()
        except (OSError, UnicodeError):
            continue
        for line in country_lines:
            if line and not line.startswith("#"):
                fields = line.split("\t")
                if len(fields) >= 2:
                    countries[fields[0]] = fields[1]
        for line in zone_lines:
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < 3 or fields[0] not in countries:
                continue
            zone = fields[2]
            locations.setdefault(
                zone,
                {
                    "timezone": zone,
                    "city": zone.rsplit("/", 1)[-1].replace("_", " "),
                    "country": countries[fields[0]],
                    "country_code": fields[0],
                    "point": seed_coordinates(fields[1]),
                },
            )
    return {
        "locations": sorted(locations.values(), key=lambda row: (row["country"], row["city"])),
        "countries": sorted(set(countries.values())),
        "source": "system-iana-tzdata",
    }


def timezone_suggestion(zone, catalog):
    if not isinstance(zone, str) or not zone or len(zone) > 100:
        return None
    try:
        ZoneInfo(zone)
    except (ValueError, ZoneInfoNotFoundError):
        return None
    match = next((row for row in catalog["locations"] if row["timezone"] == zone), None)
    if match:
        return match
    # IANA aliases can resolve to a canonical zone in the host tree.
    for root in TZPATH:
        path = Path(root)
        try:
            canonical = (path / zone).resolve().relative_to(path.resolve()).as_posix()
        except (ValueError, OSError):
            continue
        match = next((row for row in catalog["locations"] if row["timezone"] == canonical), None)
        if match:
            return match
    return None


def _usable_map(data):
    if not isinstance(data, dict) or (
        data.get("format") != "ucode-layer-map-v1"
        or data.get("projection") != "equirectangular"
    ):
        return False
    bounds = data.get("bounds")
    name, cols, rows = (data.get(key) for key in ("name", "cols", "rows"))
    if (
        not isinstance(name, str) or not name.strip()
        or type(cols) is not int or type(rows) is not int
        or not (1 <= cols <= 1000 and 1 <= rows <= 1000)
        or not isinstance(bounds, dict)
    ):
        return False
    for minimum, maximum, limit in (("latMin", "latMax", 90), ("lonMin", "lonMax", 180)):
        lower, upper = bounds.get(minimum), bounds.get(maximum)
        if not (
            type(lower) in (int, float) and type(upper) in (int, float)
            and -limit <= lower < upper <= limit
        ):
            return False
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        return False
    has_cells = False
    for layer in layers:
        if not isinstance(layer, dict) or not isinstance(layer.get("cells"), list):
            return False
        for cell in layer["cells"]:
            if not isinstance(cell, dict):
                return False
            if not all(
                type(cell.get(key)) is int and 0 <= cell[key] < limit
                for key, limit in (("col", cols), ("row", rows), ("pattern", 64))
            ):
                return False
            has_cells = True
    return has_cells


def seed_readiness():
    """Inspect installed Layer 0 knowledge and owning uCode map seeds, without writes."""
    import json
    import os

    from app.core.settings import settings

    public = settings.public_vault_root
    library = public / "global-knowledge"
    ucode = Path(os.environ.get("UCORE_UCODE_PATH", str(settings.udos_root / "uCode")))
    standards = library / "standards" / "GRIDCORE-STANDARDS.json"
    try:
        standard = json.loads(standards.read_text())
        protocols = isinstance(standard, dict) and all(
            isinstance(standard.get(key), dict) and bool(standard[key])
            for key in ("spatial_mapping", "geometry")
        )
    except (OSError, ValueError, TypeError):
        protocols = False
    try:
        knowledge = (
            library.is_dir()
            and next(
                (p for p in library.rglob("*.md") if p.is_file() and p.stat().st_size > 0), None
            )
            is not None
        )
    except OSError:
        knowledge = False
    maps = []
    for name in ["world-map", "region"]:
        try:
            source = ucode / "seeds" / "gridcore" / "layers" / (name + ".json")
            data = json.loads(source.read_text())
            if not _usable_map(data):
                continue
            maps.append(
                {
                    "id": name,
                    "name": data["name"],
                    "format": data["format"],
                    "projection": data["projection"],
                    "bounds": data["bounds"],
                    "cols": data["cols"],
                    "rows": data["rows"],
                }
            )
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return {
        "knowledge_library": knowledge,
        "gridcore_protocols": protocols,
        "gridcore_mapping": (ucode / "packages/gridcore/src/seeds/layer-map.ts").is_file(),
        "maps": maps,
    }


def seed_coordinates(value):
    """Parse IANA's public representative point, not a measured user location."""
    import re

    match = re.fullmatch(r"([+-])(\d{2})(\d{2})(\d{2})?([+-])(\d{3})(\d{2})(\d{2})?", value)
    if not match:
        return None
    a, b, c, d, e, f, g, h = match.groups()
    if any(int(v or 0) >= 60 for v in [c, d, g, h]):
        return None
    lat = (int(b) + int(c) / 60 + int(d or 0) / 3600) * (-1 if a == "-" else 1)
    lon = (int(f) + int(g) / 60 + int(h or 0) / 3600) * (-1 if e == "-" else 1)
    return {"latitude": lat, "longitude": lon} if abs(lat) <= 90 and abs(lon) <= 180 else None
