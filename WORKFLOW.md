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
| 8 | Replace monthly budget climatology with daily, global (mhw3d) | 🔲 Notebook ready — run `00_budget_clim_daily.ipynb` on Gadi |

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
| `post_processed_diags/mlt_budget_online_stavg/mlt_budget_stavg_daily_online_output336-365_monthly_mean.ncea.nc` | Budget climatology (monthly) — **superseded**, kept for the NB03 §8b comparison |
| `$OUTPUT_DIR/mlt_budget_clim_daily_336-365_global.nc` | Budget climatology (daily, day-of-year, **global**) — built by `notebooks/00_budget_clim_daily.ipynb` |

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

### `notebooks/00_budget_clim_daily.ipynb`
**Global** gridded day-of-year climatology of every budget term, from the daily online
budget files for outputs 336–365 (1989–2018), via `mhw3d.best_practice.compute_climatology`.
Numbered 00 because it is a prerequisite: NB01–NB03 open the file it writes and will fail
without it. Global rather than polar-only so the Antarctic and Arctic analyses share one
climatology; regional notebooks slice it by latitude on load. Terms: `mlt_tendency`,
`surf_to_ML`, `advection`, `vert_mixing`, `entrainment`, `residual`, and
`surface_flux`/`sw_pen` separately so the shortwave contribution can be diagnosed.

Output is in native °C s⁻¹ — NB03 applies the same `SEC_PER_DAY` factor to both the
climatology and the raw series, so the two sides of the anomaly are scaled identically.

Practicalities:

- **One streaming pass, no banding.** `compute_climatology` is lazy end to end and its one
  internal rechunk touches only the day-of-year axis, so the whole globe runs as a single
  dask graph and `to_netcdf` streams it. Splitting the globe into five 216-row latitude bands
  comes to 151,315 tasks against 151,175 for one pass — the same work and the same
  intermediate size, plus five sets of file opens and a merge.
- **Input chunking is the knob that matters**, because `rolling(time=11)` builds a windowed
  view and dask rechunks to bound it. Section 4 builds the graph and reports task count and
  chunk sizes *without computing anything*, so `YT_CHUNK` can be tuned in seconds. The
  measured trade-off at global scale is tabulated in the notebook header.
- **Align the write chunks.** The output is rechunked to match the on-disk NetCDF chunking
  before writing; without that, HDF5 read-modify-writes the same chunk repeatedly (4.0 min →
  1.1 min on a test case, and a smaller file).
- **Never the default threaded scheduler.** netCDF4/HDF5 is not thread-safe and concurrent
  reads raise `NetCDF: HDF error` or corrupt the heap. The notebook opens a distributed
  `Client(processes=True, threads_per_worker=1)`.
- **No checkpoint.** A single streaming write either finishes or it doesn't. If a run dies,
  narrow `CLIM_TERMS` and do the terms in groups — they are separate variables in the source
  files, so a subset costs little extra I/O.
- `TEST_MODE = True` runs 60 latitude rows × 120 longitudes end to end in minutes.
- The walltime and memory in the notebook's PBS block are guesses, not measurements.

**Grid note:** ACCESS-OM2 is tripolar north of ~65°N, where `yt_ocean` is nominal rather
than true latitude. This does not affect the climatology — it is a pointwise day-of-year
reduction — but Arctic *region selection* should use the 2D `geolat_t`/`geolon_t` fields.

### `notebooks/01_polar_mhw_budget_drivers.ipynb`
**Purpose:** Single box, 2010–2019. ✅ Ran successfully on Gadi (8 events detected).

### `notebooks/02_polar_mhw_multibox.ipynb`
**Purpose:** 6-box latitude transect (72.5°W–70°W, 64°S–79°S), 2010–2019, with seasonal breakdown.
- Loads SST and budget data once for the full bounding region, then loops over boxes.
- Season assigned by month of `t_peak` (DJF/MAM/JJA/SON).
- Plots: grouped bar charts, heatmaps by box, 4×2 seasonal heatmap grid.

### `notebooks/01_polar_mhw_budget_drivers.ipynb`  ← original single-box
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
- **Climatology baseline 1989–2018 (outputs 336–365):** the period of the online-diagnostic rerun in
  Holmes & Malan (2026) and of the existing MLT climatology and threshold files. `00_budget_clim_daily.ipynb`
  warns and records which outputs it actually found, so a short baseline cannot pass silently.
- **Budget anomaly method:** Day-of-year climatology computed directly from the daily budget output with
  `mhw3d.best_practice.compute_climatology` (`windowHalfWidth=5`, `smoothMeanWidth=31`), matching the
  construction of `om2_025_MLT_clim.nc` / `om2_025_MLT_thresh.nc` so budget anomalies and MHW detection
  share a baseline. **Superseded:** the earlier method took the monthly climatology, interpolated it to
  daily and applied a 31-day smooth. Twelve monthly values cannot represent a truncated seasonal cycle —
  near-flat through the ice-covered months, then a short sharp summer excursion — so the interpolation
  aliased its shoulders into the budget anomalies in exactly the sea-ice regions this chapter is about.
  On a synthetic truncated cycle (σ ≈ 22 days) the monthly-interpolated climatology recovers only ~64% of
  the peak amplitude; the day-of-year climatology recovers ~94%.
- **Onset = start → peak; Decline = peak → end:** Peak defined as day of maximum temperature anomaly above threshold within the event.

---

## Results (first run — single box, 2010–2019)

- **8 MHW events detected** in the Drake Passage box (72.5°W–70°W, 66.5°S–64°S)
- Temperature values physically realistic; budget closure ≈ 0 throughout
- Overview plot visually consistent with threshold exceedances

## Planned next steps

- [ ] Run `00_budget_clim_daily.ipynb` on Gadi, then NB03 §8b to confirm the old/new climatology difference
- [ ] Port the same climatology change into NB01 and NB02 (they still interpolate the monthly file)
- [ ] Re-run `03_extract_arctic_subset.ipynb` once the global climatology exists — it now copies it too

- [ ] Expand to full time series (confirm budget file availability for outputs 305–356)
- [ ] Interpret composite results: which terms dominate onset vs decline?
- [ ] Run notebook 02 on Gadi and evaluate 6-box + seasonal results
- [ ] Add spatial maps of temperature anomaly at onset/peak/decline (following reference notebook)
- [ ] Consider expanding to a tiling approach (following Benjamin's methodology) once multi-box analysis is validated
