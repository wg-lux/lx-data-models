"""Guard shell entry against replacing a live development environment."""

import re
from pathlib import Path


def test_shell_reload_preserves_environment_and_editor_helpers() -> None:
    source = (Path(__file__).resolve().parents[1] / "devenv.nix").read_text()
    assert "venv.enable = false;" in source
    assert "sync.enable = false;" in source
    assert (
        'SYNC_CMD = "uv sync --extra dev --extra docs --frozen --python ${python}/bin/python";'
        in source
    )
    assert '"agent:sync"' in source and "exec = SYNC_CMD;" in source
    match = re.search(r"enterShell = ''(?P<hook>.*?)'';", source, re.DOTALL)
    assert match is not None
    hook = match.group("hook")
    assert 'export VIRTUAL_ENV="$UV_PROJECT_ENVIRONMENT"' in hook
    assert 'export PATH="$VIRTUAL_ENV/bin:$PATH"' in hook
    assert "uv sync" not in hook and "$SYNC_CMD" not in hook
    assert "source .devenv/state/venv/bin/activate" not in hook
    for helper in ("use_editor_kb", "use_packaged_kb", "show_kb_mode"):
        assert f"{helper}()" in hook
    assert 'export LX_DTYPES_KB_REGISTRY="$LX_DTYPES_EDITOR_KB_REGISTRY"' in hook
