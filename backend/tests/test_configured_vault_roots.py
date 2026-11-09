"""All document clients must resolve configured roots from the same owner."""
import os
import subprocess
import sys
from pathlib import Path


def test_custom_vault_roots_agree_across_binder_import_reader_and_editor(tmp_path):
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, 'PYTHONPATH': str(root / 'backend'),
           'UDOS_HOME': str(tmp_path / 'runtime'),
           'UDOS_VAULT_ROOT': str(tmp_path / 'Personal'),
           'UDOS_SHARED_ROOT': str(tmp_path / 'Community'),
           'UDOS_PUBLIC_ROOT': str(tmp_path / 'Reference')}
    code = '''
from app.core.settings import settings
from app.api.vault_api import VAULT_LAYERS
from app.api.user_workflow import _vault_layer_by_id
from app.services.library_index import get_default_vault_paths, WORKSPACE_ROOTS
from app.flow.binder_engine import VAULT_ROOT
from app.surfaces.documentation_api import _CONTENT_ROOTS
from pathlib import Path
roots = {"user": settings.vault_root, "shared": settings.shared_vault_root, "public": settings.public_vault_root}
for name, path in roots.items():
    assert get_default_vault_paths()[name] == path
    assert Path(_vault_layer_by_id(name)["path"]) == path
    assert _CONTENT_ROOTS[name if name != "user" else "vault"] == path
assert VAULT_ROOT == settings.vault_root
assert WORKSPACE_ROOTS == [settings.shared_vault_root, settings.public_vault_root]
'''
    subprocess.run([sys.executable, '-c', code], cwd=root, env=env, check=True, capture_output=True, text=True)
    assert not (tmp_path / 'Personal').exists()
