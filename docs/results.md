# Results — bipolar MHW driver comparison

Notes for the polar chapter draft. Numbers are from `06_bipolar_richaud_method.ipynb`
(commit `d70607e`), not retyped from the figures. Source of truth for the table is
`/scratch/m35/nm5072/Polar_MHWs/06_bipolar_primary_driver_driver.csv`.

**Run configuration.** ACCESS-OM2 0.25° JRA55 IAF cycle 6, outputs 357–366 (2010–2019).
20×20 grid-cell tiles kept at ≥75% ocean: **348 Antarctic, 401 Arctic**. Hobday et al.
(2016) detection, `MIN_DUR = 5`, `MAX_GAP = 2`. Budget anomalies against the day-of-year
climatology for 1989–2018 (outputs 336–365). `area_t` weighting in both hemispheres.
`RANK_BY = 'driver'` — rank 1 is the term contributing most to what the heatwave is doing
in that phase, so descending at onset and **ascending at decline**.

---

## 1. Primary driver, whole domain

Percentage of events in each hemisphere whose primary driver is each term.
**n = 3670 (Antarctic), 5564 (Arctic).** Columns sum to 100% by construction.

| Phase | Term | Antarctic | Arctic | Difference |
|---|---|---:|---:|---:|
| Onset | Surface heat flux | 50.8 | 68.1 | −17.3 |
| Onset | Lateral advection | 11.7 | 18.7 | −7.0 |
| Onset | Vertical mixing | 19.9 | 11.5 | +8.3 |
| Onset | Entrainment | 17.6 | 1.7 | **+16.0** |
| Decline | Surface heat flux | 49.7 | 64.8 | −15.1 |
| Decline | Lateral advection | 6.2 | 14.0 | −7.8 |
| Decline | Vertical mixing | 24.6 | 18.5 | +6.2 |
| Decline | Entrainment | 19.4 | 2.7 | **+16.7** |

### Results I would argue belong in the text

**Surface heat flux dominates everywhere.** It is the primary driver of roughly half of
Antarctic events (50.8% onset, 49.7% decline) and about two thirds of Arctic ones (68.1%,
64.8%). No other term comes close in either hemisphere. Worth stating plainly before the
contrasts, because the contrasts are differences in the *remainder*.

**Entrainment is the sharpest hemispheric contrast, and it is large.** 17.6% of Antarctic
onsets against 1.7% of Arctic ones — a factor of ten. At decline, 19.4% against 2.7%, a
factor of seven. Entrainment is effectively absent as a leading driver in the Arctic while
being the third-ranked process in the Antarctic. This is the headline result of the
comparison.

**Vertical mixing also leans Antarctic** (19.9 vs 11.5 at onset; 24.6 vs 18.5 at decline),
**and lateral advection leans Arctic** (18.7 vs 11.7 at onset; 14.0 vs 6.2 at decline).
Taken with the entrainment result, the picture is that Antarctic MHWs are more often ended
and begun by vertical processes in the water column, Arctic ones more often by lateral
transport.

**Onset and decline are near-mirror images within each hemisphere.** The driver mix barely
changes with phase: surface flux falls 1–3 points, vertical mixing rises 5–7, entrainment
and advection move little. This is worth saying explicitly because the opposite would be
the natural expectation — that the processes which start an event differ from those that
end it. They largely do not, at the level of which term leads.

---

## 2. Seasonality

Events binned by the **local** season of the peak date (austral and boreal summer share a
panel). Counts, with the share of that hemisphere's total:

| Season | Antarctic | | Arctic | |
|---|---:|---:|---:|---:|
| Summer | 1217 | 33.2% | 2192 | 39.4% |
| Autumn | 918 | 25.0% | 1738 | 31.2% |
| Winter | 793 | 21.6% | 838 | 15.1% |
| Spring | 742 | 20.2% | 796 | 14.3% |
| **Total** | **3670** | | **5564** | |

**Both hemispheres' events concentrate in local summer and autumn, the Arctic more
strongly** — 70.6% of Arctic events peak in summer or autumn against 58.2% of Antarctic
ones. The Antarctic distribution is noticeably flatter across the year.

Every season carries at least 742 events, so all eight panels of Fig. Drivers 2 are
adequately populated; none needs a caveat about sample size.

---

## 3. Caveats that must travel with these numbers

**n counts tile–event pairs, not independent events.** A single physical MHW spanning many
tiles is counted once per tile. Two consequences, and both should be stated rather than
left implicit:

- The percentages are effectively weighted by MHW **area** rather than by event count. For
  a question about where drivers dominate this is arguably the more meaningful weighting,
  but it is a choice and should be named as one.
- The nominal binomial error — ±0.8% on a 50% share at n = 3670, ±0.7% at n = 5564 — is
  **optimistic**, because the samples are not independent. The hemispheric differences
  above (6–17 points) are far larger than any plausible inflation of that error, so the
  ranking is safe; a difference of 2–3 points would not be.

**Event timestamps are two days early.** `ocean_daily.nc` declares calendar `GREGORIAN`
with units "days since 0001-01-01" but its values were written against a proleptic
Gregorian epoch, so they decode two days early. Detection is internally consistent
(temperature and threshold share the skew) and the budget anomalies were shifted to match
after their climatology was removed — so the driver results are unaffected. But any
`t_start` / `t_peak` / `t_end` quoted from the saved files, or compared against an external
record, needs two days added. The `.nc` files say so in their `time_convention` attribute.

**49 of 401 Arctic tiles (12%) touch the tripolar fold row**, where the grid folds onto
itself. They are currently kept, matching NB04. Worth resolving with Benjamin before
publication.

**The Arctic numbers here will not match NB04's published figures**, because NB04 ranks
descending in both phases. Under that convention the decline "primary" driver is the term
most strongly *opposing* the decline.

---

## 4. Draft figure captions

The figures carry no titles, so these need to do the work.

**Fig. Drivers 1.** Proportion of marine heatwaves at each 20×20 grid-cell tile whose
primary mixed-layer heat budget driver is the named term, for the Arctic (top two rows)
and Antarctic (lower two rows), at onset and decline. Marker area is proportional to the
within-tile proportion on a scale shared by all sixteen panels. Colours follow Richaud et
al. (2024). White markers show every retained tile, so tiles with no events of a given kind
are distinguishable from tiles with no data. ACCESS-OM2 0.25°, 2010–2019.

**Fig. Drivers 2.** Percentage of marine heatwaves whose primary mixed-layer heat budget
driver is each term, by local season of the event peak, at onset (top) and decline
(bottom). Colour denotes the budget term; solid bars are Arctic, hatched bars Antarctic.
Sample sizes are given in each panel. Note that "summer" is austral for the Antarctic and
boreal for the Arctic. ACCESS-OM2 0.25°, 2010–2019.

---

## 5. Open questions for the chapter

- The entrainment contrast is the strongest result, but its mechanism is not established
  here. Mixed-layer depth seasonality differs sharply between the two basins; whether that
  explains the factor of ten is a separate analysis.
- `RANK_BY` is a convention, not a measurement. The `'signed'` and `'abs'` alternatives are
  implemented and switchable; if the entrainment contrast survives all three, that is worth
  a sentence.
- Tile area is not constant within or between hemispheres, so event counts per tile are
  comparable but anything per unit area is not.
