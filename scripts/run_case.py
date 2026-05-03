"""Run the verified RTS-96 UC + MDP case study.

This script keeps imports explicit so the project can be run from the research
folder without installing a package.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from rts96_stochastic_uc_mdp import main


if __name__ == "__main__":
    main()
