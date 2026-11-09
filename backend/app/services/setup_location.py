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
        except OSError:
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


def seed_readiness():
    """Inspect installed Layer 0 knowledge and owning uCode map seeds, without writes."""
    import json
    import math
    import os

    from app.core.settings import settings

    public = settings.public_vault_root
    library = public / "global-knowledge"
    ucode = Path(os.environ.get("UCORE_UCODE_PATH", str(settings.udos_root / "uCode")))
    standards = library / "standards" / "GRIDCORE-STANDARDS.json"
    try:
        standard = json.loads(standards.read_text())
        protocols = bool(standard.get("spatial_mapping")) and bool(standard.get("geometry"))
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
            if (
                data.get("format") != "ucode-layer-map-v1"
                or data.get("projection") != "equirectangular"
            ):
                continue
            bounds = data["bounds"]
            cols, rows = data["cols"], data["rows"]
            if not all(
                isinstance(bounds[k], (int, float)) and math.isfinite(bounds[k])
                for k in ["latMin", "latMax", "lonMin", "lonMax"]
            ) or not (bounds["latMin"] < bounds["latMax"] and bounds["lonMin"] < bounds["lonMax"]):
                continue
            if (
                not isinstance(cols, int)
                or not isinstance(rows, int)
                or not (1 <= cols <= 1000 and 1 <= rows <= 1000)
                or not isinstance(data.get("layers"), list)
                or not any(
                    isinstance(layer, dict)
                    and isinstance(layer.get("cells"), list)
                    and layer["cells"]
                    for layer in data["layers"]
                )
            ):
                continue
            maps.append(
                {
                    "id": name,
                    "name": data["name"],
                    "format": data["format"],
                    "projection": data["projection"],
                    "bounds": bounds,
                    "cols": cols,
                    "rows": rows,
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
