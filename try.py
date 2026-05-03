"""Small scratch entry point for the RTS-96 reliability UC project.

Run this file from the project root if you want a quick import check without
launching the full MIP/MDP experiment.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from rts96_reliability_uc import (  # noqa: E402
    ANNUAL_PEAK_MW,
    LOLP_EPS,
    RTS96_GENERATORS,
    VRE_PENETRATION,
)


def main() -> None:
    total_capacity = sum(gen.p_max for gen in RTS96_GENERATORS)
    print("RTS-96 reliability UC project")
    print(f"Generators: {len(RTS96_GENERATORS)}")
    print(f"Installed capacity: {total_capacity:.0f} MW")
    print(f"Annual peak: {ANNUAL_PEAK_MW:.0f} MW")
    print(f"VRE penetration: {VRE_PENETRATION:.0%}")
    print(f"LOLP epsilon: {LOLP_EPS:.3f}")


if __name__ == "__main__":
    main()
