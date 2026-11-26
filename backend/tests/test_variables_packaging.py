"""Guard the variable-registry packaging contract.

`vars.def` is loaded at import time, so if it is missing from an installed
package the backend fails to start rather than degrading. These tests pin the
two things that keep it shipped: the file lives inside `app.core`, and pyproject
declares it as package data.
"""

import tomllib
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_registry_definition_lives_inside_the_package():
    definition = BACKEND / "app" / "core" / "vars.def"
    assert definition.is_file(), "vars.def must live inside the app.core package"


def test_registry_definition_is_declared_as_package_data():
    config = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    declared = config["tool"]["setuptools"]["package-data"]
    assert "vars.def" in declared.get("app.core", []), (
        "vars.def must be declared as app.core package data or wheels omit it"
    )


def test_registry_loads_without_trailing_whitespace_failures():
    from app.api import variables_api

    assert variables_api._REGISTRY, "the registry must not be empty"
    # Every declared kind is one the loader accepts.
    assert set(variables_api._REGISTRY.values()) - {"scratch"} <= {
        "identity",
        "personal",
        "organization",
        "address",
        "communication",
        "workflow",
        "system",
        "basic",
        "page",
        "internal",
    }
