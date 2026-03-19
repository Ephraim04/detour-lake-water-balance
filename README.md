# Detour Lake Mine — Preliminary Water Balance Assessment

**Author:** Isaiah Ephraim
**Affiliation:** B.Eng Mining Engineering, Federal University of Technology, Akure, Nigeria
**Contact:** isaiahephraim04@gmail.com
**Profile:** [Academia.edu](https://futa.academia.edu/IsaiahEphraim) | [LinkedIn](https://linkedin.com/in/isaiahephraim) | [GitHub](https://github.com/Ephraim04)

---

## Overview

This repository contains the Python code used to compute, tabulate, and
visualise the preliminary water balance for the Detour Lake open pit mine
in northeastern Ontario, Canada.

The analysis is the computational basis for:

> Ephraim, I.G. (2026) *Preliminary Water Balance Assessment for a Large
> Open Pit Mine: A Case Study of Detour Lake Mine, Ontario, Canada.*
> Zenodo. [DOI to be added on publication]

Groundwater inflow values are taken from the companion study:

> Ephraim, I.G. (2026) *Steady-State Groundwater Inflow Estimation for Large
> Open Pit Mining Operations: Analytical Radial Flow Assessment —
> Detour Lake Mine, Ontario, Canada.*
> Zenodo. https://doi.org/10.5281/zenodo.19111972

All input data are derived from publicly available sources. No proprietary
mine data were used or required.

---

## What the script does

Running `detour_lake_water_balance.py` produces:

- Annual water balance summary for two groundwater scenarios
- Full monthly water balance table (Scenario 1 — conservative)
- Sensitivity analysis table (three parameters, six variations)
- Figure 1 — monthly inflow/outflow bar chart with cumulative storage line
- Figure 2 — horizontal bar chart of sensitivity results

---

## Data sources

| Component | Source |
|---|---|
| Climate parameters | Detour Gold Corporation (2018) NI 43-101 Technical Report, Section 5.2 |
| Monthly precipitation | Environment and Climate Change Canada — climate.weather.gc.ca |
| Evaporation inputs | NASA POWER database — power.larc.nasa.gov (50.02°N, 79.72°W) |
| Pit geometry | Ephraim, I.G. (2026) — equivalent pit radius 1,200 m |
| Groundwater inflow | Ephraim, I.G. (2026) — Thiem equation, two K scenarios |
| Catchment area | Canadian Digital Elevation Model — Natural Resources Canada |
| Runoff coefficient | Chow et al. (1988) — glaciated low-relief terrain range |
| Process water demand | Detour Gold Corporation (2018), Section 17.4.2 |
| TMA seepage range | ICOLD (2001); Vick (1990) |

---

## Installation

Python 3.8 or later is required.

Install dependencies:

```bash
pip install numpy matplotlib
```

No other packages are needed.

---

## Usage

Run the script from the command line:

```bash
python detour_lake_water_balance.py
```

All results print to the terminal. Two PNG figures are saved in the
current directory:

- `figure1_monthly_balance.png`
- `figure2_sensitivity.png`

---

## Key parameters

All input parameters are defined at the top of the script under clearly
labelled sections. To update a value, change it in that section — the
rest of the calculations update automatically.

The most important parameters to verify before submission are:

| Parameter | Current value | Verification needed |
|---|---|---|
| Pit radius | 1,200 m | Confirm from NI 43-101 pit shell |
| Catchment multiplier | 2.5× pit area | Replace with GIS-delineated value |
| Evaporation method | Temperature-based approximation | Replace with full Penman using NASA POWER inputs |
| Monthly temperature | Interpolated from Jan/Jul averages | Replace with monthly ECCC station records |
| Process water factor | 0.3 m³/tonne | Confirm with site operational data if available |

---

## Groundwater scenarios

Two scenarios are carried forward from Ephraim, I.G. (2026):

| Scenario | K (m/s) | Q (m³/day) | Q (Mm³/yr) |
|---|---|---|---|
| 1 — Conservative bedrock | 1×10⁻⁷ | 761 | 0.278 |
| 2 — Fracture-enhanced | 1×10⁻⁵ | 76,079 | 27.769 |

To run the monthly balance for Scenario 2, change the `gw_scenario`
argument in the `print_monthly_table()` and `plot_monthly_balance()`
calls at the bottom of the script.

---

## Key results

| Condition | Annual balance | Status |
|---|---|---|
| Conservative bedrock | −0.263 Mm³/yr | Deficit — manageable within pond storage |
| Fracture-enhanced shear zone | +27.228 Mm³/yr | Surplus — pond fills in ~46 days |

Seasonally, the system runs at deficit for ten months. April delivers the
peak monthly inflow — approximately 1.506 Mm³ under baseline conditions,
representing 43% of total mine water pond capacity in a single month.

---

## File structure

```
detour_lake_water_balance.py      Main script — all calculations and figures
README.md                         This file
figure1_monthly_balance.png       Generated on first run
figure2_sensitivity.png           Generated on first run
```

---

## Reproducing the paper results

Every number in the companion paper can be reproduced by running the
script with default parameters. The script is self-contained — no
external data files are required because all input values are hard-coded
with their sources documented inline.

---

## Known limitations

- Evaporation uses a simplified temperature-based estimate. The full
  Penman equation with NASA POWER solar radiation and humidity data at
  50.02°N, 79.72°W should be applied before final submission.

- Pit surface area uses a circular approximation based on the equivalent
  radius from Ephraim, I.G. (2026). Verify against the actual pit shell
  from the NI 43-101 before detailed design work.

- Monthly temperature distribution is interpolated from January and July
  averages. Monthly ECCC station records would improve precision.

- TMA seepage is estimated from published literature ranges because no
  quantitative measurements were reported in the 2018 Technical Report.

These limitations are consistent with the preliminary scope of the
assessment and are discussed in full in the companion paper.

---

## Related repositories

| Study | Repository |
|---|---|
| Paper 1 — Groundwater inflow model | https://github.com/Ephraim04/detour-lake-groundwater-inflow |
| Paper 2 — Water balance (this repo) | https://github.com/Ephraim04/detour-lake-water-balance |

---

## References

1. Detour Gold Corporation, 2018. *NI 43-101 Technical Report on the Detour Lake Mine, Ontario, Canada*. Effective date: 27 June 2018.
2. Ephraim, I.G., 2026. Steady-state groundwater inflow estimation for large open pit mining operations. Zenodo. https://doi.org/10.5281/zenodo.19111972
3. Environment and Climate Change Canada, 2023. Canadian climate normals. Available at: https://climate.weather.gc.ca [Accessed: March 2026].
4. NASA, 2023. POWER climatology resource for agroclimatology. Available at: https://power.larc.nasa.gov [Accessed: March 2026].
5. Chow, V.T., Maidment, D.R. and Mays, L.W., 1988. *Applied Hydrology*. New York: McGraw-Hill.
6. Freeze, R.A. and Cherry, J.A., 1979. *Groundwater*. Englewood Cliffs, NJ: Prentice-Hall.

---

## Citation

If you use this code, please cite:

> Ephraim, I.G. (2026) Preliminary Water Balance Assessment for a Large
> Open Pit Mine: A Case Study of Detour Lake Mine, Ontario, Canada.
> Zenodo. [DOI to be added on publication]

---

## License

MIT License. See LICENSE file for details.
