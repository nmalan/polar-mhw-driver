# Polar MHW Heat Budget — Analysis Workflow

## Project goal

Separate the mixed-layer heat budget drivers of marine heatwave (MHW) **onset** and
**decline** in the polar oceans, using ACCESS-OM2 0.25° JRA55 IAF cycle 6 output, for the
AGU monograph polar chapter.

Two methods are kept deliberately separate, so that a disagreement between them is
informative rather than confusing:

- **Our approach** (NB01–NB03): geographic boxes, composites of the mean anomaly per term.
  Follows [rmholmes/access-om2-sst-budget](https://github.com/rmholmes/access-om2-sst-budget),
  extended to composite over all events in a multi-year series.
- **Richaud's approach** (NB04–NB06): 20×20 grid-cell tiles, and *counts of events* by which
  term ranks first or second.

---

## Status

| Step | Description | Status |
|------|-------------|--------|
| 1 | Single-box analysis (NB01) | ✅ Done |
| 2 | Multi-box transect (NB02) | ✅ Done |
| 3 | Circumpolar 2.5° boxes (NB03) | ✅ Done |
| 4 | Global daily budget climatology (NB00) | ✅ Done — `mlt_budget_clim_daily_336-365_global.nc` |
| 5 | Antarctic Richaud method (NB05) | ✅ Built, ultraplot figures |
| 6 | Bipolar standalone (NB06) | 🔄 Running on Gadi |
| 7 | Compare the two methods, write up | 🔲 Todo |

---

## Data (NCI Gadi)

**Base path:** `/g/data/av17/access-nri/OM2/025deg_jra55_iaf_cycle6_online_mlt/`

| File | Description |
|------|-------------|
| `output{NNN}/ocean/ocean_daily.nc` | Daily `temp_in_mld` and `mld` |
| `output{NNN}/ocean/ocean_grid.nc` | `geolat_t`, `geolon_t`, `area_t` (1080 × 1440) |
| `post_processed_diags/om2_025_MLT_clim.nc` | Daily MLT climatology (day-of-year) |
| `post_processed_diags/om2_025_MLT_thresh.nc` | 90th-percentile threshold (day-of-year) |
| `post_processed_diags/mlt_budget_online_stavg/mlt_budget_stavg_daily_online_output{NNN}.nc` | Daily budget terms |
| `…output336-365_monthly_mean.ncea.nc` | Budget climatology (monthly) — **superseded**, kept only for the NB03 §8b comparison |
| `$OUTPUT_DIR/mlt_budget_clim_daily_336-365_global.nc` | Budget climatology (daily, day-of-year, **global**) — built by NB00 |

Some budget years live in a second directory,
`/scratch/e14/rmh561/access-om2/archive/…/post_processed_diags/`. NB00 resolves both by
glob and raises if an output appears in more than one.

**Output numbering:** output305 = 1958, so output *NNN* = 1958 + *NNN* − 305.
Analysis currently uses outputs 357–366 (2010–2019); the climatology uses 336–365 (1989–2018).

---

## ⚠ The two-day calendar skew

**This is the most important thing in this file.** The MLT and budget files do not agree
about what day it is.

`ocean_daily.nc` declares `units = "days since 0001-01-01"` with `calendar = "GREGORIAN"`,
which CF reads as the mixed Julian/Gregorian calendar. The values were written against a
*proleptic* Gregorian epoch. Twelve extra Julian leap days less the ten dropped in October
1582 leaves a **two-day** discrepancy at modern dates, so **`ocean_daily` timestamps decode
two days early**.

The budget diagnostics were re-based with a per-file epoch and an explicit
`calendar = "proleptic_gregorian"`, so **they carry true dates**.

```
mlt    output357  [2009-12-30 .. 2010-12-29]
budget output357  [2010-01-01 .. 2010-12-31]
```

Confirmed three independent ways:

1. `cftime` decodes the same raw value as 2009-12-30 under `standard` and 2010-01-01 under
   `proleptic_gregorian`.
2. Every output pair is offset by the same two days, leap years included.
3. `corr(dMLT/dt, mlt_tendency)` peaks at **0.907 at lag +2**, against 0.296 at lag 0.

### How the analysis handles it

**Detection stays on the as-written MLT timestamps.** Temperature, `om2_025_MLT_clim.nc`
and `om2_025_MLT_thresh.nc` all share the same skew, so it cancels within detection and the
events are correct. Nothing about those files has to change.

**The budget anomaly is relabelled two days earlier to match** — and only *after* its
climatology has been removed. The order is load-bearing: NB00's budget climatology is on
true day-of-year, so relabelling first would shift the day-of-year lookup too. Mid-year
that is a two-day error; across the New Year boundary `dayofyear` wraps and it becomes a
**364-day** error — which is austral summer, peak Antarctic MHW season. Both cases are in
`tests/test_nb06_numerics.py`.

Event times saved in `06_*_mhw_budget_events.nc` are therefore **two days early**; add two
days for true dates. The files record this in their `time_convention` attribute.

**Anything that pairs `ocean_daily` with the budget diagnostics by timestamp has this
offset in it** — including NB04's published Arctic composites. Detection is unaffected;
budget composites are taken two days off their event windows. Raise with Ryan and Benjamin.

---

## Budget terms

| Variable in file | Label in notebooks | Notes |
|-----------------|--------------------|-------|
| `mlt_tendency` | MLT tendency | LHS — rate of change of mixed-layer temperature |
| `surface_flux` + `sw_pen` | Surface Flux (`surf_to_ML`) | Net surface heat flux absorbed in the ML |
| `advection` | Advection | Horizontal + vertical advection |
| `vert_mixing` | Vertical mixing | Turbulent mixing at the ML base |
| `entrainment` | Entrainment | ML deepening/shoaling |
| `residual` | Residual | Budget closure check (should ≈ 0) |

Stored as °C s⁻¹, converted to °C day⁻¹ (× 86400) in the notebooks. The same factor is
applied to both the climatology and the raw series, so the two sides of the anomaly scale
identically.

---

## Notebooks

### `00_budget_clim_daily.ipynb` — prerequisite

Global day-of-year climatology of every budget term for outputs 336–365 (1989–2018), via
`mhw3d.best_practice.compute_climatology`. NB01, NB03, NB05 and NB06 open the file it
writes and fail without it. Global rather than polar-only so both hemispheres share one
construction; regional notebooks slice it by latitude on load.

**Why day-of-year rather than monthly.** The previous method interpolated a 12-value
monthly climatology to daily and applied a 31-day smooth. Twelve values cannot represent a
*truncated* seasonal cycle — near-flat through the ice-covered months, then a short sharp
summer excursion — so the interpolation aliased its shoulders into the budget anomalies, in
exactly the sea-ice regions this chapter is about. On a synthetic truncated cycle
(σ ≈ 22 days) the monthly-interpolated climatology recovers ~64% of the peak amplitude
against ~94% for the day-of-year version; RMSE 0.0064 against 0.0011.

**Design, as built:**

- **Per-variable loop with Zarr staging.** Each raw term is written to a spatially tiled
  Zarr store (`TARGET_YX = 90`), its climatology computed and saved, then the next. A
  day-of-year reduction costs `366 × tile area` per input chunk, so **spatial tile size is
  what matters, not time-contiguity** — verified: `compute_climatology` gives the same
  answer on time-chunked and time-contiguous data (max diff 2.8e-13, float summation
  order). It is `compute_threshold` that needs the whole record, because it unstacks time
  into a year × day-of-year grid.
- **Resume built in.** A term whose `clim_parts_30yr/` file already exists is skipped, and
  parts are written with write-then-rename so a killed job leaves no truncated file.
- **`STAGE = False` gives bit-identical output** — staging is a performance choice, not a
  numerical one.
- **`surf_to_ML` is derived, not computed.** Every step of `compute_climatology` is linear,
  so `clim(surface_flux + sw_pen) == clim(surface_flux) + clim(sw_pen)` exactly. Section 6
  checks the one thing that could break it: the two NaN masks differing.
- **`WINDOW_HALF_WIDTH = 1`** — no ±day pooling before the day-of-year mean. This is what
  mhw3d does in *both* modes: `best_practice.compute_climatology` defaults to 1 and
  `legacy` hardcodes `_pool_window(da, 0)`. Only `compute_threshold` pools ±5 days, where
  it is needed for a 90th percentile. Pooling here would widen the effective smoothing to
  ~41 days once the 31-day smooth is applied, blunting the sharp shoulders this notebook
  exists to resolve.
- **Never the default threaded scheduler.** netCDF4/HDF5 is not thread-safe; concurrent
  reads raise `NetCDF: HDF error` or corrupt the heap. Use
  `Client(processes=True, threads_per_worker=1)` with an explicit `memory_limit` — on Gadi
  `psutil` reports the whole node, not your PBS/ARE allocation.
- **No `rechunker`.** It fails against analysis3-26.05's xarray
  (`extract_zarr_variable_encoding() missing … 'zarr_format'`). Plain `.chunk(...).to_zarr()`
  replaced it.

The mhw3d README is **stale**: it documents `climatologyPeriod=(1982,2011)`, but the actual
signature takes `baseline_period=slice(...)`. Read the source.

### `01_polar_mhw_budget_drivers.ipynb`
Single box (Drake Passage / Antarctic Peninsula margin, 72.5°W–70°W, 66.5°S–64°S),
2010–2019. 8 events detected; budget closure ≈ 0.

### `02_polar_mhw_multibox.ipynb`
Six-box latitude transect (72.5°W–70°W, 64°S–79°S) with a seasonal breakdown. **Still
interpolates the monthly climatology** — the day-of-year change has not been ported.

### `03_polar_mhw_circumpolar.ipynb`
Circumpolar 2.5° × 2.5° boxes south of 60°S. Uses the daily budget climatology by
day-of-year selection. §8b compares the old monthly-interpolated climatology against the
new one.

### `03_extract_arctic_subset.ipynb`
Cuts the global files to ≥60°N for sharing with Benjamin. Not needed by NB06, which reads
the global files directly.

### `04_polar_mhw_arctic.ipynb` — Benjamin's, read-only
The Arctic Richaud-method analysis. Kept here for reference; we do not run it.

### `05_antarctic_richaud_method.ipynb`
Antarctic port of NB04 — same tiling, event bookkeeping, driver ranking and two headline
figures, dropping the tripolar machinery the Southern Ocean does not need. Figures are a
direct copy of NB04's ultraplot cells.

### `06_bipolar_richaud_method.ipynb`
**Standalone bipolar analysis.** Runs the whole pipeline over both polar oceans from the
global files — no dependency on NB04, NB05, or the Arctic subset. Uses `area_t` weighting
and 2D `geolat_t`/`geolon_t` in both hemispheres, so the two halves are literally one code
path. Writes per-hemisphere and combined `ds_events` files plus a primary-driver CSV.

---

## Tiling: fidelity to Richaud's method

NB05 and NB06 reproduce `generate_tiles_boxes` from NB04 cell 8. Identical by construction:
20×20 blocks in index space; kept when the **absolute count** of ocean cells is ≥ 300;
ocean mask from the first 31 days of the first year; centre latitude from `geolat_t`;
area weighting. Tiling in index space rather than degrees is Richaud's own choice — NB04
keeps the degree-based tiler commented out with the note that it *"won't work for the
Arctic, because of the Northpole."*

Four deliberate departures, each switchable with NB04's behaviour as the default, and each
reported at run time:

1. **Longitude centre.** NB04 takes a plain arithmetic mean of `geolon_t`, which is wrong
   on a circle. `LON_CENTER` selects; both are stored. *Measured: 0 of 348 Antarctic and
   0 of 401 Arctic tiles differ by more than a degree, so this is moot in practice.*
2. **`DROP_FOLD_ROW`** — defaults to `False`, matching NB04. *49 of 401 Arctic tiles (12%)
   touch the northernmost grid row, where a tripolar grid folds onto itself.* Worth asking
   Benjamin whether that row is duplicated.
3. **Tile id convention** — half a cell different from NB04's, so ids do not cross-reference.
4. **`ocean_frac` denominator** — the actual block size, not NB04's hardcoded 400.

### Probable defects in NB04 cell 8, verified by running the constructs

- `boxes.append(...)` sits **outside** the `if ~np.isnan(nb):` guard, so the final
  `np.unique` element — `nan` — appends a **duplicate of the last valid tile** with stale
  `gcs`. Reproduced: two tiles in, three boxes out. That tile enters the statistics twice.
- The `seam` flag is `min > max`, which cannot be true, so the check never fires.
- `tiles.where(tiles == nb, drop=True)` drops any all-land row or column of a tile,
  *including interior ones*, so the box mean covers a smaller region than the nominal block
  and `ocean_frac` is computed against 400 on an array that no longer has 400 cells.
  *Measured: 18 Antarctic and 9 Arctic tiles affected — 27 of 749, 3.6%.*

None of these change which tiles are kept.

---

## Driver ranking

`RANK_BY` in NB06 selects the convention. These are **anomalies**, so sign is physical:
a negative surface-flux anomaly cools relative to climatology and genuinely can end a
heatwave.

- **`driver`** (NB06 default) — rank 1 is the largest contributor to what the MHW is doing:
  descending at onset (most positive), **ascending at decline** (most negative).
- **`signed`** (NB04) — rank 1 is the most positive anomaly in both phases. At decline that
  makes rank 1 the term most strongly *opposing* the decline, and pushes the term actually
  ending the event to rank 4 — which is never plotted, since the figures show ranks 1 and 2.
- **`abs`** (NB03) — rank 1 is the largest magnitude regardless of sign. Differs from
  `driver` when a large opposing term outweighs the term doing the work.

NB06's Arctic numbers will therefore **not** match NB04's published figures. Set
`RANK_BY = 'signed'` to reproduce those exactly.

---

## Performance notes (NB06, hard-won)

- **Chunking: name every dimension.** Omitting one does not give one chunk per file —
  xarray falls back to that file's *stored* chunking (`namedarray/utils.py::_get_chunk`:
  `chunks.get(dim, None) or preferred_chunk_sizes`). `ocean_daily.nc` is stored one day at
  a time, so omitting `'time'` produced **3650 one-day chunks**. The two file sets are
  stored differently and need separate dicts.
- **Reduce per band, not per tile.** One `coarsen` over a whole latitude band produces
  every tile at once: **44× fewer tasks** than a loop of per-tile `.weighted().mean()`
  calls, for values identical to 1.8e-16. The per-tile version built ~1.2 M dask tasks for
  a single band — almost all scheduler overhead.
- **Do not rechunk y to realign after the hemisphere slice.** A global rechunk is a
  shuffle: 280 rechunk tasks a band against 8 without it, and it was the only real source
  of worker-to-worker traffic (and of `CommClosedError`s). Let each band straddle two
  neighbouring chunks instead.
- **`open_dataset` without `chunks=` returns numpy, not dask.** The clim/threshold/budget-
  climatology opens lacked it, so their box means ran eagerly and serially in the client
  process with every worker idle.
- **Float32 tolerances.** Comparing two summation orders in float32 with `atol=1e-10` is
  meaningless — the observed difference is 8 ULP. `VERIFY_COARSEN` checks the NaN pattern
  exactly and finite values to 64 float32 ULP scaled by magnitude, which still rejects a
  one-day misalignment by three orders of magnitude.
- **Checkpoints are keyed on the budget climatology filename**
  (`checkpoints_nb06/<clim tag>/<hemisphere>/`), so changing `BUDGET_CLIM_FILE`
  invalidates the cache instead of silently serving box means built on another baseline.

---

## Tests

`tests/test_nb06_numerics.py` execs NB06's own cells against synthetic data — 31 checks
covering the circular longitude mean, `area_t` vs `cos(lat)` equivalence in the south
(agrees to 6e-17), land getting zero weight, fold-row dropping, all three ranking
conventions on a worked decline example, tile areas summing to `area_t`, and the
climatology-then-relabel ordering including the New Year wrap.

```bash
python3 tests/test_nb06_numerics.py
```

---

## Open items

### Next analyses

- [ ] **Seasonal decomposition of the drivers.** `calendar_quarter(t_peak)` is already
      computed in NB06's `decompose_hemisphere`, but `box_df2xr` drops it — `id_vars` is
      `['event_id', 't_start', 't_peak', 't_end', 'term']`, so it never reaches
      `ds_events`. It does not need a rerun though: `t_peak` *is* saved as a coordinate,
      so the season can be recomputed from the existing files. Two things to get right:
      - `t_peak` is on the skewed axis, so **add two days before binning** — otherwise
        events peaking within two days of a quarter boundary land in the wrong season.
      - DJF is austral summer and boreal winter. For a bipolar figure, bin by *local*
        season (summer/autumn/winter/spring) rather than by calendar quarter, or the two
        hemispheres' panels are not comparable.
- [ ] **Drivers of short vs long events (≶ 1 month).** `t_start` and `t_end` are saved
      coordinates, so `duration = t_end - t_start` needs no rerun either. Check the
      duration histogram before fixing the split: `MIN_DUR = 5` sets the floor, and if the
      distribution is strongly skewed a 30-day cut may leave the long bin thin. The
      comparison is pooled across tiles, so only the **total** n per bin matters — not
      every tile needs long events. The binomial error on a ~25% share is ±2.5% at
      n = 300 and ±6.8% at n = 40, so a bin much under a few hundred events cannot
      separate shares differing by less than ~5%. A median split is the data-driven
      fallback if a round 30 days is too thin. (Per-tile counts only become binding if the
      *maps* are split by duration too.)

Both are post-processing on `06_*_mhw_budget_events.nc` — probably a NB07 rather than
edits to NB06, so the expensive run stays untouched.

### Parked: events spanning multiple tiles

A single physical MHW can be detected independently in many neighbouring tiles, so the
pooled statistics count it once per tile. This is inherited from Richaud's method, not
introduced here.

Probably **fine for the shares**: a basin-scale event contributing more (tile, event) pairs
than a one-tile blip means the percentages are effectively weighted by MHW *area* rather
than by event count, which is arguably the more meaningful quantity for a chapter about
where drivers dominate. Worth stating explicitly rather than leaving implicit.

Probably **not fine for the uncertainty**: the binomial error above assumes independent
samples. If events cluster across tiles the effective n is closer to the number of distinct
physical events than to the number of (tile, event) pairs, so quoted confidence intervals
are too narrow — possibly by a lot.

Checkable from the saved files alone, no rerun: cluster (tile, event) pairs into connected
components using tile adjacency plus date overlap, then compare the number of pairs to the
number of components. That ratio is the variance inflation factor, and bootstrapping by
component rather than by pair gives honest intervals. Ask Benjamin whether he treated this
in the published Arctic work.

### Housekeeping

- [ ] Finish the NB06 run; read section 11's primary-driver table
- [ ] Port the day-of-year climatology into NB02 (still interpolates the monthly file)
- [ ] Decide `DROP_FOLD_ROW` for the Arctic — 49 tiles touch the fold
- [ ] Add `area_m2` to `ds_events` if per-unit-area normalisation is wanted (changes the saved files)
- [ ] Expand beyond 2010–2019 (confirm budget availability for outputs 305–356)
- [ ] `.gitignore` for `Claude outputs/`, `memory/`, `plots/`, `docs/*.pdf`
- [ ] Scratch cleanup: `_to_delete/`, `checkpoints_nb05`, `rechunk_tmp/`, 9-year `clim_parts/`

### To raise with Benjamin and Ryan

- The **two-day calendar skew** — affects any timestamp pairing of `ocean_daily` with the
  budget diagnostics, including NB04's Arctic composites
- The duplicate-tile append, the dead `seam` check, and `drop=True` shrinking 27 tiles
- NB04's commented-out `to_netcdf` calls (cells 23 and 31) — nothing is cached or saved
- NB04 still uses the **monthly** budget climatology, interpolated and then 31-day smoothed
- The signed-rank phase asymmetry at decline
- `END_OUTPUT` mismatch: NB04 uses 357–366, NB00 uses 336–365
- What `meshgrid_access-om2_025_60N.nc` and `areacello_access-om2_025_60N.nc` were cut from
