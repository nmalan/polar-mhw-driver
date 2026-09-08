Repository of mixed layer temperature budget analysis for AGU monograph on marine heatwaves - polar chapter - for the Antarctic and Arctic.

* first pass is a naive conversion of my mid latitude marine heatwave driver code from Holmes and Malan (2026), submitted to JAMES, copy in 'docs' in this repo. Possible issues to be addressed include MHW detection by severity.
* Note that is analysis uses MLT (average mixed layer temperature) rather than SST - although the difference should be subtle.
* Model evaluation for the Arctic is still needed
* At the moment this analysis ignores sea ice - I need to revisit the budget code and equations to see how we decided to deal with fluxes from ice to ocean.
* Tom Schmaltz has already made subsets of sea ice extent - these need to be included in the analysis soon
* **Budget climatologies (resolved):** the budget climatology was a monthly mean interpolated to daily in-notebook, which could not represent the truncated polar seasonal cycle and aliased it into the budget anomalies. It is now computed directly from the daily budget output with `mhw3d.best_practice.compute_climatology` over outputs 336-365 (1989-2018) - see `notebooks/00_budget_clim_daily.ipynb`. The output is **global**, so the same file serves the Antarctic and Arctic analyses and is generally better posed than the monthly file wherever a sharp or short seasonal feature matters. NB03 uses it; **NB01 and NB02 still use the old monthly file** and need the same change before their results are compared with NB03.
