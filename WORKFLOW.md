# Polar MHW Heat Budget — Analysis Workflow

## Project goal
Identify and separate the mixed-layer heat budget drivers of marine heatwave (MHW) **onset** and **decline** for a selected box in the Antarctic / Southern Ocean, using ACCESS-OM2 0.25° IAF cycle 6 output.

Closely follows the approach in [rmholmes/access-om2-sst-budget](https://github.com/rmholmes/access-om2-sst-budget), extended to composite over all events in a multi-year time series.

---

## Status

| Step | Description | Status |
|------|-------------|--------|
| 1 | Define study region and box | ✅ Done |
| 2 | Set up local git repo | ✅ Done |
| 3 | Write first analysis notebook | ✅ Done |
| 4 | Push to GitHub remote | ✅ Done |
| 5 | Verify data/budget file availability on Gadi | ✅ Done (2010–2019 confirmed) |
| 6 | Run notebook on Gadi | ✅ Done |
| 7 | Evaluate results, expand to more boxes | 🔲 Todo |

---

## Study box

- **Location:** Drake Passage / Antarctic Peninsula margin
- **Box:** 72.5°W–70°W, 66.5°S–64°S  (10×10 grid cells at 0.25° = 2.5°×2.5°)
- **Criterion:** South of 60°S, between 60–90°W
- **Note:** Box can be moved by editing `sreg` in the config cell of the notebook.

---

## Data (NCI Gadi)

**Base path:** `/g/data/av17/access-nri/OM2/025deg_jra55_iaf_cycle6_online_mlt/`

| File | Description |
|------|-------------|
| `output{NNN}/ocean/ocean_daily.nc` | Daily SST (`temp_in_mld`) and MLD |
| `post_processed_diags/om2_025_MLT_clim.nc` | Pre-computed daily climatology |
| `post_processed_diags/om2_025_MLT_thresh.nc` | Pre-computed 90th-percentile threshold |
| `post_processed_diags/mlt_budget_online_stavg/mlt_budget_stavg_daily_online_output{NNN}.nc` | Daily budget terms |
| `post_processed_diags/mlt_budget_online_stavg/mlt_budget_stavg_daily_online_output336-365_monthly_mean.ncea.nc` | Budget climatology (monthly) |

**Output numbering:** output305 = 1958, output366 = 2019 (one file per year).  
**Currently loading:** outputs 357–366 (2010–2019) — confirmed working.

**Check available budget files on Gadi:**
```bash
ls /g/data/av17/access-nri/OM2/025deg_jra55_iaf_cycle6_online_mlt/post_processed_diags/mlt_budget_online_stavg/ \
  | grep -E "output35[7-9]|output36[0-6]"
```

---

## Budget terms

| Variable in file | Label in notebook | Notes |
|-----------------|-------------------|-------|
| `mlt_tendency` | MLT tendency | LHS — rate of change of mixed-layer temperature |
| `surface_flux` + `sw_pen` | Surface Flux | Net surface heat flux absorbed in ML |
| `advection` | Advection | Horizontal + vertical advection |
| `vert_mixing` | Vertical mixing | Turbulent mixing at ML base |
| `entrainment` | Entrainment | ML deepening/shoaling |
| `residual` | Residual | Budget closure check (should ≈ 0) |

Units: stored as °C s⁻¹, converted to °C day⁻¹ (×86400) in notebook.

---

## Notebooks

### `notebooks/01_polar_mhw_budget_drivers.ipynb`
**Purpose:** First-pass analysis for a single box, 2010–2019.

**Workflow inside the notebook:**
1. Config — region, paths, output range, detection parameters
2. Context map (South Polar Stereo)
3. Load full SST time series (lazy, Dask)
4. Load pre-computed climatology + threshold → compute area-mean
5. **MHW detection** — Hobday et al. (2016): MIN_DUR=5 days, MAX_GAP=2 days
6. Overview plot — all detected events on the temperature time series
7. Load full budget time series (lazy, Dask)
8. Load budget climatology → interpolate monthly → smooth daily anomaly
9. Compute full-series budget anomalies (triggers compute)
10. **Onset / decline decomposition** — for each event, mean budget anomaly during onset (start→peak) and decline (peak→end)
11. Summary DataFrame (`df`) with one row per (event × term)
12. Composite bar chart — mean onset vs decline across all events + individual event scatter
13. Box plots — distribution across events
14. Budget closure check

---

## Key decisions and rationale

- **10×10 box (not 20×20):** Model resolution is 0.25° (vs 0.1° in Benjamin Richaud's study), so a 10×10 box gives a comparable spatial scale (~2.5°×2.5°).
- **No sea-ice concentration filter:** Following Benjamin's suggestion; not needed for our domain definition.
- **2010–2019 initially:** Budget files may not exist for all 62 years; verify on Gadi before expanding.
- **Budget anomaly method:** Monthly climatology interpolated to daily and smoothed with a 31-day window (consistent with the 11-day centred smoothing used in MHW threshold calculation).
- **Onset = start → peak; Decline = peak → end:** Peak defined as day of maximum temperature anomaly above threshold within the event.

---

## Results (first run — single box, 2010–2019)

- **8 MHW events detected** in the Drake Passage box (72.5°W–70°W, 66.5°S–64°S)
- Temperature values physically realistic; budget closure ≈ 0 throughout
- Overview plot visually consistent with threshold exceedances

## Planned next steps

- [ ] Expand to full time series (confirm budget file availability for outputs 305–356)
- [ ] Interpret composite results: which terms dominate onset vs decline?
- [ ] Try several different boxes (move `sreg`) to assess spatial variability across 60–90°W
- [ ] Add spatial maps of temperature anomaly at onset/peak/decline (following reference notebook)
- [ ] Consider splitting by season (austral summer vs winter MHWs)
- [ ] Consider expanding to a tiling approach (following Benjamin's methodology) once single-box analysis is validated
