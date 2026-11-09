"""Release checks enforce current package ownership instead of skipping gates."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_check(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_missing_companion_is_a_failure_not_a_successful_skip(tmp_path, monkeypatch):
    check = load_check('smoke_split_repo_imports')
    monkeypatch.setattr(check, 'REPO_PATHS', {'uCode': tmp_path / 'missing'})
    with pytest.raises(RuntimeError, match='Required path missing'):
        check.main()


def test_packaging_requires_bundled_authorities_and_real_readme(tmp_path, monkeypatch):
    check = load_check('validate_split_repo_packaging')
    monkeypatch.setattr(check, 'ROOT', tmp_path)
    project = tmp_path / 'backend'
    (project / 'app').mkdir(parents=True)
    (project / 'app/__init__.py').write_text('')
    (project / 'pyproject.toml').write_text('[project]\nname="ucore"\nversion="1.0"\nreadme="missing.md"\nrequires-python=">=3.12"\n')
    errors = check._validate_spec(check.SPECS[0])
    assert any('README is missing' in error for error in errors)
    assert any('app.flow' in error for error in errors)
    assert any('app.knowledge' in error for error in errors)
    assert any('app.identity' in error for error in errors)


def test_companion_shell_manifest_cannot_pass_native_runtime_gate(monkeypatch):
    check = load_check('smoke_split_repo_imports')
    package = ModuleType('ucode_runtime')
    package.__path__ = []
    reference = ModuleType('ucode_runtime.runtime_info')
    reference.runtime_info = lambda: {'capabilities': ['terminal.shell']}
    monkeypatch.setitem(sys.modules, 'ucode_runtime', package)
    monkeypatch.setitem(sys.modules, 'ucode_runtime.ceefax', ModuleType('ucode_runtime.ceefax'))
    monkeypatch.setitem(sys.modules, 'ucode_runtime.runtime_info', reference)
    with pytest.raises(RuntimeError, match='native BASIC'):
        check._check_imports()


def test_manifest_validation_uses_owned_state_root_and_bundled_identity(tmp_path, monkeypatch):
    check = load_check('validate_extension_manifests')
    monkeypatch.setattr(check.settings, 'udos_home', tmp_path / 'runtime')
    assert check._default_paths()[1] == tmp_path / 'runtime/extensions'
    assert 'uidentity' in check.BUILTIN_IDS
