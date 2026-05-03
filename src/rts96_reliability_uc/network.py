"""Network construction and power-flow validation helpers."""

import logging

from .data import HOURLY_PROFILE

try:
    import pandapower as pp
    import pandapower.networks as pn
except ModuleNotFoundError:
    pp = None
    pn = None

def build_pandapower_network():
    if pp is None or pn is None:
        print("  pandapower unavailable; skipping network validation.")
        return None
    try:
        net = pn.case24_ieee_rts()
        print("  Loaded IEEE RTS-24 bus from pandapower (case24_ieee_rts).")
    except Exception:
        net = pp.create_empty_network()
        print("  Built fallback network (case24_ieee_rts unavailable).")
    return net


def run_power_flow_validation(net, hour=17):
    """DC power flow at the given hour (0-indexed)."""
    if net is None or pp is None:
        return {"converged": False, "hour": hour, "error": "pandapower unavailable"}
    lf = HOURLY_PROFILE['winter_weekday'][hour]/100.0
    for i in net.load.index:
        net.load.at[i,"p_mw"] *= lf
    pp_logger = logging.getLogger("pandapower.auxiliary")
    old_level = pp_logger.level
    try:
        pp_logger.setLevel(logging.ERROR)
        pp.rundcpp(net, numba=False)
        return {"converged":True,"hour":hour,
                "max_line_load_%":float(net.res_line["loading_percent"].max())
                                  if not net.res_line.empty else 0.0,
                "total_gen_mw":float(net.res_gen["p_mw"].sum())
                               if not net.res_gen.empty else 0.0}
    except Exception as ex:
        return {"converged":False,"error":str(ex)}
    finally:
        pp_logger.setLevel(old_level)


# ══════════════════════════════════════════════════════════════════════════════
#  8. PENETRATION SWEEP
