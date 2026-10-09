"""Examples; ledger helpers load only when requested by a Django-ready caller."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .demo_star_upper_gi import (
        DemoStarUpperGiExportPaths,
        build_demo_star_upper_gi_export_paths,
        build_star_upper_gi_demo_interface,
    )


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(name)
    from . import demo_star_upper_gi

    return getattr(demo_star_upper_gi, name)


__all__ = [
    "DemoStarUpperGiExportPaths",
    "build_demo_star_upper_gi_export_paths",
    "build_star_upper_gi_demo_interface",
]
