from app.services.setup_location import (
    location_catalog,
    seed_coordinates,
    seed_readiness,
    timezone_suggestion,
)


def test_offline_catalog_and_timezone_suggestion(tmp_path):
    (tmp_path / "iso3166.tab").write_text("AU\tAustralia\nUS\tUnited States\n")
    (tmp_path / "zone.tab").write_text(
        "AU\t-3157+11551\tAustralia/Perth\nUS\t+404251-0740023\tAmerica/New_York\n"
    )
    catalog = location_catalog([tmp_path])
    assert timezone_suggestion("Australia/Perth", catalog)["country"] == "Australia"
    assert timezone_suggestion("America/New_York", catalog)["city"] == "New York"
    assert timezone_suggestion("UTC", catalog) is None
    assert timezone_suggestion("../etc/passwd", catalog) is None
    assert catalog["locations"][0]["point"] == {"latitude": -31.95, "longitude": 115.85}
    assert seed_coordinates("invalid") is None
    assert seed_coordinates("+9100+18100") is None


def test_seed_readiness_checks_owners_without_installing(tmp_path, monkeypatch):
    import json

    from app.core.settings import settings

    monkeypatch.setattr(settings, "public_vault_root", tmp_path / "Public")
    monkeypatch.setenv("UCORE_UCODE_PATH", str(tmp_path / "uCode"))
    empty = seed_readiness()
    assert (
        not empty["knowledge_library"] and not empty["gridcore_protocols"] and empty["maps"] == []
    )
    assert not (tmp_path / "Public").exists()
    library = tmp_path / "Public/global-knowledge"
    (library / "standards").mkdir(parents=True)
    (library / "README.md").write_text("Knowledge baseline")
    (library / "standards/GRIDCORE-STANDARDS.json").write_text(
        json.dumps({"geometry": {"dot": 4}, "spatial_mapping": {"format": "grid"}})
    )
    seeds = tmp_path / "uCode/seeds/gridcore/layers"
    seeds.mkdir(parents=True)
    (seeds / "world-map.json").write_text(
        json.dumps(
            {
                "format": "ucode-layer-map-v1",
                "projection": "equirectangular",
                "name": "World",
                "bounds": {"latMin": -60, "latMax": 85, "lonMin": -180, "lonMax": 180},
                "cols": 40,
                "rows": 25,
                "layers": [{"id": "terrain", "cells": [{"col": 0, "row": 0, "pattern": 32}]}],
            }
        )
    )
    mapper = tmp_path / "uCode/packages/gridcore/src/seeds/layer-map.ts"
    mapper.parent.mkdir(parents=True)
    mapper.write_text("shared mapping implementation")
    result = seed_readiness()
    assert (
        result["knowledge_library"] and result["gridcore_protocols"] and result["gridcore_mapping"]
    )
    assert result["maps"][0]["id"] == "world-map"
    (seeds / "world-map.json").write_text("{}")
    assert seed_readiness()["maps"] == []
