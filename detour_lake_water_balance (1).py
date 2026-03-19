"""
Preliminary Water Balance Assessment — Detour Lake Open Pit Mine
Ontario, Canada

Author : Isaiah Ephraim
         B.Eng Mining Engineering
         Federal University of Technology, Akure, Nigeria

Companion paper:
    Ephraim, I.G. (2026) Preliminary Water Balance Assessment for a Large
    Open Pit Mine: A Case Study of Detour Lake Mine, Ontario, Canada.
    Zenodo. https://doi.org/10.5281/zenodo.19111972

Groundwater inflow values sourced from:
    Ephraim, I.G. (2026) Steady-State Groundwater Inflow Estimation for
    Large Open Pit Mining Operations: Analytical Radial Flow Assessment —
    Detour Lake Mine, Ontario, Canada.

All input data are derived from publicly available sources.
No proprietary mine data were used.

Data sources
------------
- Detour Gold Corporation (2018) NI 43-101 Technical Report on the
  Detour Lake Mine, Ontario, Canada. Filed on SEDAR.
- Environment and Climate Change Canada: climate.weather.gc.ca
- NASA POWER database: power.larc.nasa.gov
- Natural Resources Canada — Canadian Digital Elevation Model

Usage
-----
    python detour_lake_water_balance.py

Requirements
------------
    numpy
    matplotlib

Install with:
    pip install numpy matplotlib
"""

import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# =============================================================================
# 1. SITE PARAMETERS
# All values sourced from Detour Gold Corporation (2018) NI 43-101
# Technical Report unless stated otherwise.
# =============================================================================

# --- Climate (Technical Report Section 5.2) ----------------------------------
ANNUAL_PRECIP_MM    = 806.0     # mean annual precipitation (mm/yr)
MEAN_ANNUAL_TEMP_C  = 0.5       # mean annual temperature (°C)
WIND_SPEED_KMH      = 12.6      # mean annual wind speed (km/h)

# Mean monthly temperatures (°C) — interpolated from Jan and Jul averages
# reported in Technical Report Section 5.2
MONTHLY_TEMP_C = [
    -18.7,  # January
    -16.5,  # February
     -9.0,  # March
      0.5,  # April
      8.5,  # May
     14.0,  # June
     16.5,  # July
     15.0,  # August
      9.5,  # September
      3.0,  # October
     -4.5,  # November
    -13.5,  # December
]

# Monthly precipitation distribution (% of annual total)
# Derived from northern Ontario climate normals — ECCC stations
# Cochrane and Kapuskasing
MONTHLY_PRECIP_PCT_RAW = [
    5.0,   # January
    4.5,   # February
    5.5,   # March
    7.0,   # April
    8.5,   # May
    9.5,   # June
   10.5,   # July
    9.5,   # August
    8.5,   # September
    8.0,   # October
    7.5,   # November
    6.0,   # December
]

# Normalise to sum to 100%
_total = sum(MONTHLY_PRECIP_PCT_RAW)
MONTHLY_PRECIP_PCT = [p / _total * 100 for p in MONTHLY_PRECIP_PCT_RAW]

# --- Pit geometry (Ephraim, I.G., 2026) --------------------------------------------
PIT_RADIUS_M        = 1200.0    # equivalent pit radius (m)
PIT_AREA_M2         = math.pi * PIT_RADIUS_M ** 2   # 4,523,893 m²
PIT_AREA_HA         = PIT_AREA_M2 / 10_000
PIT_AREA_KM2        = PIT_AREA_M2 / 1_000_000

# Contributing catchment area = 2.5 × pit area
# Based on subdued topography and ~30 m local relief (Tech Report S5.2)
CATCHMENT_MULTIPLIER    = 2.5
CATCHMENT_AREA_M2       = PIT_AREA_M2 * CATCHMENT_MULTIPLIER
CATCHMENT_AREA_HA       = CATCHMENT_AREA_M2 / 10_000

# --- Runoff coefficients -----------------------------------------------------
C_RAIN  = 0.35   # rainfall runoff coefficient — glaciated low-relief terrain
                 # Source: Chow et al. (1988)
C_SNOW  = 0.80   # snowmelt runoff coefficient — frozen ground conditions
                 # Source: Woo (2012)

# Snowmelt split between April and May
SNOWMELT_APR_FRACTION = 0.60
SNOWMELT_MAY_FRACTION = 0.40

# --- Groundwater inflow (Ephraim, I.G., 2026) --------------------------------------
# Thiem equation: Q = (2π·K·b·Δh) / ln(r2/r1)
# Parameters: r1=1200m, r2=5000m, b=200m, Δh=100m
GW_SCENARIO_1_M3DAY = 761.0       # conservative bedrock  K = 1×10⁻⁷ m/s
GW_SCENARIO_2_M3DAY = 76_079.0    # fracture-enhanced     K = 1×10⁻⁵ m/s

# --- Evaporation -------------------------------------------------------------
# Estimated using simplified temperature-based approach pending full
# Penman calculation with NASA POWER inputs at 50.02°N, 79.72°W
# Ice-covered months (T < 0°C) are assigned zero evaporation
EVAP_TEMP_COEFFICIENT = 5.5   # mm/°C/month — calibrated to ~486 mm/yr
EVAP_TEMP_INTERCEPT   = 20.0  # mm/month base when T > 0°C

# --- Process plant (Technical Report Section 1.6 and 17.4.2) ----------------
THROUGHPUT_T_DAY            = 55_000    # design throughput (tonnes/day)
NET_WATER_PER_TONNE_M3      = 0.3       # net consumptive water use (m³/tonne)
                                        # Source: Norgate and Lovel (2006)

# --- TMA seepage (ICOLD, 2001; Vick, 1990) -----------------------------------
TMA_CAPACITY_MT             = 660       # total TMA capacity (million tonnes)
TMA_TAILINGS_DENSITY_T_M3   = 1.4       # typical gold tailings density
TMA_FILL_FRACTION           = 0.30      # assumed current fill (~30%)
TMA_SEEPAGE_BASE_PCT        = 0.005     # base case seepage rate (0.5%/yr)
TMA_COLLECTION_EFFICIENCY   = 0.50      # fraction recovered by seepage ponds

# --- Storage -----------------------------------------------------------------
MINE_WATER_POND_MM3         = 3.5       # mine water pond capacity (Mm³)

# --- Site coordinates (verified) ---------------------------------------------
SITE_LAT    = 50.02     # °N
SITE_LON    = -79.72    # °W

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


# =============================================================================
# 2. HELPER FUNCTIONS
# =============================================================================

def monthly_precip_mm():
    """Return monthly precipitation in mm."""
    return [ANNUAL_PRECIP_MM * p / 100 for p in MONTHLY_PRECIP_PCT]


def snow_and_rain_totals():
    """Split annual precipitation into snowfall and rainfall components."""
    precip = monthly_precip_mm()
    snow = sum(precip[i] for i in range(12) if MONTHLY_TEMP_C[i] < 0)
    rain = sum(precip[i] for i in range(12) if MONTHLY_TEMP_C[i] >= 0)
    return snow, rain


def monthly_evaporation_mm():
    """
    Estimate monthly open-water evaporation.
    Zero for ice-covered months (mean T < 0°C).
    Temperature-based estimate for ice-free months.
    Note: replace with full Penman calculation using NASA POWER
    data at 50.02°N, 79.72°W before final submission.
    """
    evap = []
    for t in MONTHLY_TEMP_C:
        if t <= 0:
            evap.append(0.0)
        else:
            evap.append(max(0.0, EVAP_TEMP_COEFFICIENT * t + EVAP_TEMP_INTERCEPT))
    return evap


def gw_inflow_mm3yr(q_m3day):
    """Convert groundwater inflow from m³/day to Mm³/yr."""
    return q_m3day * 365 / 1_000_000


def process_water_mm3yr():
    """Annual net process plant water consumption (Mm³/yr)."""
    return THROUGHPUT_T_DAY * 365 * NET_WATER_PER_TONNE_M3 / 1_000_000


def tma_seepage_mm3yr(seepage_pct=None):
    """
    Net annual TMA seepage loss (Mm³/yr).
    seepage_pct : float, optional
        Override the base case seepage percentage (default 0.005 = 0.5%).
    """
    if seepage_pct is None:
        seepage_pct = TMA_SEEPAGE_BASE_PCT
    tma_volume_mm3 = TMA_CAPACITY_MT / TMA_TAILINGS_DENSITY_T_M3
    tma_current_mm3 = tma_volume_mm3 * TMA_FILL_FRACTION
    gross_seepage = tma_current_mm3 * seepage_pct
    net_seepage = gross_seepage * (1 - TMA_COLLECTION_EFFICIENCY)
    return net_seepage


# =============================================================================
# 3. WATER BALANCE CALCULATIONS
# =============================================================================

def compute_annual_balance(gw_scenario=1,
                            precip_factor=1.0,
                            gw_factor=1.0,
                            seepage_pct=None):
    """
    Compute the annual water balance.

    Parameters
    ----------
    gw_scenario   : int   — 1 = conservative bedrock, 2 = fracture-enhanced
    precip_factor : float — multiplier applied to annual precipitation
    gw_factor     : float — multiplier applied to groundwater inflow
    seepage_pct   : float — TMA seepage rate override (fraction per year)

    Returns
    -------
    dict with all inflow, outflow, and storage change values in Mm³/yr
    """
    precip       = monthly_precip_mm()
    snow_mm, rain_mm = snow_and_rain_totals()
    evap         = monthly_evaporation_mm()
    annual_evap  = sum(evap)

    # Apply precipitation sensitivity factor
    adj_precip_mm   = ANNUAL_PRECIP_MM * precip_factor
    adj_snow_mm     = snow_mm * precip_factor
    adj_rain_mm     = rain_mm * precip_factor

    # Inflows
    P_mm3    = (adj_precip_mm / 1000) * PIT_AREA_M2 / 1_000_000
    Q_rain   = (adj_rain_mm  / 1000) * C_RAIN * CATCHMENT_AREA_M2 / 1_000_000
    Q_snow   = (adj_snow_mm  / 1000) * C_SNOW * CATCHMENT_AREA_M2 / 1_000_000
    Q_in     = Q_rain + Q_snow

    q_base   = GW_SCENARIO_1_M3DAY if gw_scenario == 1 else GW_SCENARIO_2_M3DAY
    GW_in    = gw_inflow_mm3yr(q_base) * gw_factor

    total_inflow = P_mm3 + Q_in + GW_in

    # Outflows
    E        = (annual_evap / 1000) * PIT_AREA_M2 / 1_000_000
    W_proc   = process_water_mm3yr()
    S_tma    = tma_seepage_mm3yr(seepage_pct)

    total_outflow = E + W_proc + S_tma

    delta_S  = total_inflow - total_outflow

    return {
        "precipitation_mm3":    P_mm3,
        "surface_runoff_mm3":   Q_in,
        "gw_inflow_mm3":        GW_in,
        "total_inflow_mm3":     total_inflow,
        "evaporation_mm3":      E,
        "process_water_mm3":    W_proc,
        "tma_seepage_mm3":      S_tma,
        "total_outflow_mm3":    total_outflow,
        "delta_S_mm3":          delta_S,
    }


def compute_monthly_balance(gw_scenario=1):
    """
    Compute the monthly water balance under a given groundwater scenario.

    Returns
    -------
    dict with lists of monthly values (Mm³)
    """
    precip       = monthly_precip_mm()
    evap         = monthly_evaporation_mm()
    snow_mm, _   = snow_and_rain_totals()

    q_base       = GW_SCENARIO_1_M3DAY if gw_scenario == 1 else GW_SCENARIO_2_M3DAY
    gw_annual    = gw_inflow_mm3yr(q_base)
    gw_monthly   = gw_annual / 12

    w_monthly    = process_water_mm3yr() / 12
    s_monthly    = tma_seepage_mm3yr()   / 12

    # Snowmelt runoff distributed to April (60%) and May (40%)
    q_snow_total = (snow_mm / 1000) * C_SNOW * CATCHMENT_AREA_M2 / 1_000_000
    q_snow_apr   = q_snow_total * SNOWMELT_APR_FRACTION
    q_snow_may   = q_snow_total * SNOWMELT_MAY_FRACTION

    monthly_p       = []
    monthly_runoff  = []
    monthly_gw      = []
    monthly_evap    = []
    monthly_process = []
    monthly_net     = []
    monthly_cumul   = []
    cumul           = 0.0

    for i in range(12):
        p_mm3 = (precip[i] / 1000) * PIT_AREA_M2 / 1_000_000

        # Rainfall runoff (ice-free months only)
        if i == 3:      # April — snowmelt pulse (60%) + any rainfall
            r_mm3 = q_snow_apr
        elif i == 4:    # May — snowmelt pulse (40%) + rainfall
            r_mm3 = q_snow_may + (precip[i] / 1000) * C_RAIN * CATCHMENT_AREA_M2 / 1_000_000
        elif MONTHLY_TEMP_C[i] >= 0:
            r_mm3 = (precip[i] / 1000) * C_RAIN * CATCHMENT_AREA_M2 / 1_000_000
        else:
            r_mm3 = 0.0

        e_mm3   = (evap[i] / 1000) * PIT_AREA_M2 / 1_000_000
        net     = p_mm3 + r_mm3 + gw_monthly - e_mm3 - w_monthly - s_monthly
        cumul  += net

        monthly_p.append(round(p_mm3, 3))
        monthly_runoff.append(round(r_mm3, 3))
        monthly_gw.append(round(gw_monthly, 3))
        monthly_evap.append(round(e_mm3, 3))
        monthly_process.append(round(w_monthly, 3))
        monthly_net.append(round(net, 3))
        monthly_cumul.append(round(cumul, 3))

    return {
        "months":           MONTHS,
        "precip_mm":        [round(p, 1) for p in monthly_precip_mm()],
        "precip_mm3":       monthly_p,
        "runoff_mm3":       monthly_runoff,
        "gw_mm3":           monthly_gw,
        "evap_mm3":         monthly_evap,
        "process_mm3":      monthly_process,
        "net_mm3":          monthly_net,
        "cumulative_mm3":   monthly_cumul,
    }


def sensitivity_analysis():
    """
    One-at-a-time sensitivity analysis on the three most uncertain
    parameters: precipitation (±20%), groundwater inflow (±15%),
    and TMA seepage rate (0.1% to 1.0%).

    Returns
    -------
    list of dicts describing each scenario
    """
    base = compute_annual_balance(gw_scenario=1)["delta_S_mm3"]
    results = [{"label": "Base case", "variation": "—",
                "delta_S": base, "shift": 0.0}]

    for factor, label in [(0.80, "Precipitation −20%"),
                           (1.20, "Precipitation +20%")]:
        b = compute_annual_balance(gw_scenario=1,
                                   precip_factor=factor)["delta_S_mm3"]
        results.append({"label": label, "variation": f"{factor:.2f}×",
                         "delta_S": b, "shift": b - base})

    for factor, label in [(0.85, "GW inflow −15%"),
                           (1.15, "GW inflow +15%")]:
        b = compute_annual_balance(gw_scenario=1,
                                   gw_factor=factor)["delta_S_mm3"]
        results.append({"label": label, "variation": f"{factor:.2f}×",
                         "delta_S": b, "shift": b - base})

    for pct, label in [(0.001, "TMA seepage 0.1%/yr"),
                        (0.010, "TMA seepage 1.0%/yr")]:
        b = compute_annual_balance(gw_scenario=1,
                                   seepage_pct=pct)["delta_S_mm3"]
        results.append({"label": label, "variation": f"{pct*100:.1f}%",
                         "delta_S": b, "shift": b - base})

    return results


# =============================================================================
# 4. REPORTING
# =============================================================================

def print_annual_summary():
    print("\n" + "=" * 65)
    print("ANNUAL WATER BALANCE SUMMARY — DETOUR LAKE OPEN PIT")
    print("=" * 65)

    for scenario, label in [(1, "Scenario 1 — Conservative bedrock (K = 1×10⁻⁷ m/s)"),
                             (2, "Scenario 2 — Fracture-enhanced (K = 1×10⁻⁵ m/s)")]:
        b = compute_annual_balance(gw_scenario=scenario)
        gw_day = GW_SCENARIO_1_M3DAY if scenario == 1 else GW_SCENARIO_2_M3DAY
        print(f"\n{label}")
        print(f"  GW inflow: {gw_day:,.0f} m³/day"
              f" = {b['gw_inflow_mm3']:.3f} Mm³/yr")
        print(f"\n  INFLOWS (Mm³/yr):")
        print(f"    Direct precipitation :  {b['precipitation_mm3']:.3f}")
        print(f"    Surface runoff       :  {b['surface_runoff_mm3']:.3f}")
        print(f"    Groundwater inflow   :  {b['gw_inflow_mm3']:.3f}")
        print(f"    ─────────────────────────────")
        print(f"    TOTAL                :  {b['total_inflow_mm3']:.3f}")
        print(f"\n  OUTFLOWS (Mm³/yr):")
        print(f"    Evaporation          :  {b['evaporation_mm3']:.3f}")
        print(f"    Process plant demand :  {b['process_water_mm3']:.3f}")
        print(f"    TMA net seepage      :  {b['tma_seepage_mm3']:.3f}")
        print(f"    ─────────────────────────────")
        print(f"    TOTAL                :  {b['total_outflow_mm3']:.3f}")
        print(f"\n  NET ΔS (before dewatering): {b['delta_S_mm3']:+.3f} Mm³/yr")
        status = "SURPLUS — dewatering required" if b["delta_S_mm3"] > 0 \
                 else "DEFICIT — draw on storage"
        print(f"  STATUS: {status}")


def print_monthly_table(gw_scenario=1):
    label = "conservative" if gw_scenario == 1 else "fracture-enhanced"
    print(f"\n{'='*65}")
    print(f"MONTHLY WATER BALANCE — SCENARIO {gw_scenario} ({label})")
    print(f"{'='*65}")
    mb = compute_monthly_balance(gw_scenario)
    hdr = f"{'Month':<5} {'Precip':>7} {'Runoff':>8} {'GW':>8}"
    hdr += f" {'Evap':>8} {'Process':>8} {'Net ΔS':>8} {'Cumul':>8}"
    print(f"\n{hdr}")
    print(f"{'':5} {'mm':>7} {'Mm³':>8} {'Mm³':>8}"
          f" {'Mm³':>8} {'Mm³':>8} {'Mm³':>8} {'Mm³':>8}")
    print("-" * 65)
    for i in range(12):
        row = (f"{mb['months'][i]:<5} "
               f"{mb['precip_mm'][i]:>7.1f} "
               f"{mb['runoff_mm3'][i]:>8.3f} "
               f"{mb['gw_mm3'][i]:>8.3f} "
               f"{mb['evap_mm3'][i]:>8.3f} "
               f"{mb['process_mm3'][i]:>8.3f} "
               f"{mb['net_mm3'][i]:>8.3f} "
               f"{mb['cumulative_mm3'][i]:>8.3f}")
        print(row)
    print(f"\nMine water pond capacity : {MINE_WATER_POND_MM3} Mm³")
    peak_idx = mb['net_mm3'].index(max(mb['net_mm3']))
    peak_in  = (mb['precip_mm3'][peak_idx] + mb['runoff_mm3'][peak_idx]
                + mb['gw_mm3'][peak_idx])
    print(f"Peak monthly inflow      : {peak_in:.3f} Mm³ "
          f"({mb['months'][peak_idx]}) = "
          f"{peak_in/MINE_WATER_POND_MM3*100:.0f}% of pond capacity")


def print_sensitivity():
    print(f"\n{'='*65}")
    print("SENSITIVITY ANALYSIS — SCENARIO 1 (conservative groundwater)")
    print(f"{'='*65}")
    results = sensitivity_analysis()
    print(f"\n{'Parameter':<25} {'Annual ΔS (Mm³/yr)':>20} {'Shift':>10}")
    print("-" * 58)
    for r in results:
        print(f"{r['label']:<25} {r['delta_S']:>20.3f} {r['shift']:>+10.3f}")


# =============================================================================
# 5. FIGURES
# =============================================================================

def plot_monthly_balance(gw_scenario=1, save_path="figure1_monthly_balance.png"):
    """
    Figure 1 — Monthly water balance bar chart with cumulative storage line.
    """
    mb = compute_monthly_balance(gw_scenario)
    x  = np.arange(12)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("white")

    # Stacked inflow bars
    bars_p = ax1.bar(x, mb["precip_mm3"],  color="#AED6F1", label="Precipitation")
    bars_r = ax1.bar(x, mb["runoff_mm3"],  color="#2E86C1",
                     bottom=mb["precip_mm3"], label="Surface runoff")
    bottom_in = [mb["precip_mm3"][i] + mb["runoff_mm3"][i] for i in range(12)]
    bars_g = ax1.bar(x, mb["gw_mm3"],      color="#1A5276",
                     bottom=bottom_in, label="Groundwater inflow")

    # Outflow bars (negative direction)
    neg_proc  = [-v for v in mb["process_mm3"]]
    neg_evap  = [-v for v in mb["evap_mm3"]]
    ax1.bar(x, neg_proc, color="#E74C3C", label="Process demand")
    ax1.bar(x, neg_evap, color="#F39C12",
            bottom=neg_proc, label="Evaporation")

    # Cumulative storage line
    ax2 = ax1.twinx()
    ax2.plot(x, mb["cumulative_mm3"], color="#1E8449",
             linewidth=2.5, marker="o", markersize=6,
             label="Cumulative ΔS")
    ax2.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax2.axhline(MINE_WATER_POND_MM3, color="#922B21",
                linewidth=1.5, linestyle=":",
                label=f"Pond capacity ({MINE_WATER_POND_MM3} Mm³)")
    ax2.set_ylabel("Cumulative storage change (Mm³)", fontsize=11)
    ax2.tick_params(labelsize=10)

    ax1.set_xticks(x)
    ax1.set_xticklabels(MONTHS, fontsize=11)
    ax1.set_xlabel("Month", fontsize=12)
    ax1.set_ylabel("Monthly water volume (Mm³)", fontsize=11)
    scenario_label = "conservative" if gw_scenario == 1 else "fracture-enhanced"
    ax1.set_title(
        f"Figure 1. Monthly water balance — Detour Lake open pit\n"
        f"Scenario {gw_scenario} ({scenario_label} groundwater conditions)",
        fontsize=12, pad=12
    )
    ax1.tick_params(labelsize=10)
    ax1.axhline(0, color="black", linewidth=0.8)

    # Combined legend
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2,
               loc="upper right", fontsize=9, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"\nFigure saved: {save_path}")
    plt.close()


def plot_sensitivity(save_path="figure2_sensitivity.png"):
    """
    Figure 2 — Horizontal bar chart of sensitivity analysis results.
    """
    results   = sensitivity_analysis()
    labels    = [r["label"] for r in results]
    shifts    = [r["shift"] for r in results]
    colours   = ["#2E86C1" if s >= 0 else "#E74C3C" for s in shifts]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("white")
    bars = ax.barh(labels, shifts, color=colours, edgecolor="white", height=0.6)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Shift in annual ΔS from base case (Mm³/yr)", fontsize=11)
    ax.set_title(
        "Figure 2. Sensitivity of annual water balance to key parameters\n"
        "Scenario 1 — conservative groundwater conditions",
        fontsize=12, pad=10
    )
    ax.tick_params(labelsize=10)
    for bar, val in zip(bars, shifts):
        if val != 0:
            ax.text(val + (0.02 if val > 0 else -0.02), bar.get_y() + bar.get_height() / 2,
                    f"{val:+.3f}", va="center",
                    ha="left" if val > 0 else "right", fontsize=9)
    surplus_patch = mpatches.Patch(color="#2E86C1", label="Surplus increase")
    deficit_patch = mpatches.Patch(color="#E74C3C", label="Deficit increase")
    ax.legend(handles=[surplus_patch, deficit_patch], fontsize=9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"Figure saved: {save_path}")
    plt.close()


# =============================================================================
# 6. MAIN
# =============================================================================

if __name__ == "__main__":

    print("\nDETOUR LAKE MINE — PRELIMINARY WATER BALANCE ASSESSMENT")
    print("Isaiah Ephraim | Zenodo preprint")
    print(f"Site coordinates: {SITE_LAT}°N, {SITE_LON}°W")

    # --- Geometry summary
    print(f"\nPIT GEOMETRY")
    print(f"  Equivalent pit radius    : {PIT_RADIUS_M:.0f} m")
    print(f"  Pit surface area         : {PIT_AREA_M2:,.0f} m² "
          f"({PIT_AREA_HA:.1f} ha)")
    print(f"  Contributing catchment   : {CATCHMENT_AREA_M2/1e6:.2f} km² "
          f"({CATCHMENT_AREA_HA:.0f} ha)")

    # --- Precipitation split
    snow, rain = snow_and_rain_totals()
    print(f"\nPRECIPITATION SPLIT")
    print(f"  Annual total             : {ANNUAL_PRECIP_MM:.0f} mm/yr")
    print(f"  Snowfall (SWE)           : {snow:.1f} mm  (Nov–Mar)")
    print(f"  Rainfall                 : {rain:.1f} mm  (Apr–Oct)")

    # --- Annual balance both scenarios
    print_annual_summary()

    # --- Monthly balance scenario 1
    print_monthly_table(gw_scenario=1)

    # --- Sensitivity analysis
    print_sensitivity()

    # --- Figures
    print("\nGenerating figures...")
    plot_monthly_balance(gw_scenario=1)
    plot_sensitivity()

    print("\nDone. All results printed above.")
    print("Figures saved as PNG files in the current directory.")
    print("\nNOTE: Evaporation is estimated from a temperature-based")
    print("approximation. Replace with full Penman calculation using")
    print(f"NASA POWER data at {SITE_LAT}°N, {abs(SITE_LON)}°W before")
    print("final submission.")
