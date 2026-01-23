from pathlib import Path
from typing import get_type_hints

import yaml


def dump_ddict_schema(ddict_type: type, out_path: Path) -> None:
    hints = get_type_hints(ddict_type)
    schema = {
        name: getattr(hint, "__name__", str(hint)) for name, hint in hints.items()
    }
    out_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
