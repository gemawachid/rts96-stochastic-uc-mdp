"""Compatibility facade for the modular RTS-96 reliability UC package.

The implementation now lives in ``src/rts96_reliability_uc``.  This file keeps
older scripts and notebooks working, including ``python rts96_stochastic_uc_mdp.py``.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rts96_reliability_uc.config import *  # noqa: F401,F403,E402
from rts96_reliability_uc.data import *  # noqa: F401,F403,E402
from rts96_reliability_uc.scenarios import *  # noqa: F401,F403,E402
from rts96_reliability_uc.unit_commitment import *  # noqa: F401,F403,E402
from rts96_reliability_uc.mdp import *  # noqa: F401,F403,E402
from rts96_reliability_uc.evaluation import *  # noqa: F401,F403,E402
from rts96_reliability_uc.baselines import *  # noqa: F401,F403,E402
from rts96_reliability_uc.network import *  # noqa: F401,F403,E402
from rts96_reliability_uc.experiments import *  # noqa: F401,F403,E402
from rts96_reliability_uc.runner import main  # noqa: F401,E402


if __name__ == "__main__":
    main()
