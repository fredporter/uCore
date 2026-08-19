# path-policy: allow-literals
from scripts.check_home_path_policy import violations


def test_rejects_new_legacy_home_state_path():
    diff = "+++ b/backend/example.py\n+STATE = Path.home() / '.ucore' / 'state.json'\n"
    assert violations(diff)


def test_accepts_udos_home_path():
    diff = "+++ b/backend/example.py\n+STATE = settings.udos_home / 'state.json'\n"
    assert violations(diff) == []


def test_accepts_canonical_default_home():
    diff = '+++ b/backend/example.py\n+HOME = Path.home() / "Code" / ".udos"\n'
    assert violations(diff) == []


def test_explicit_line_exception_is_auditable():
    diff = "+++ b/backend/example.py\n+LEGACY = '~/.ucore'  # path-policy: allow\n"
    assert violations(diff) == []
