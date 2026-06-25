Repository of mixed layer temperature budget analysis for AGU monograph on marine heatwaves - polar chapter - for the Antarctic and Arctic.

* first pass is a naive conversion of my mid latitude marine heatwave driver code from Holmes and Malan (2026), submitted to JAMES, copy in 'docs' in this repo. Possible issues to be addressed include MHW detection by severity, and the monthly interpolation used to generatre budget climatologies not being detailed enough to capture the truncated polar seasonal cycle.
* Note that is analysis uses MLT (average mixed layer temperature) rather than SST - although the difference should be subtle.
* Model evaluation for the Arctic is still needed
* At the moment this analysis ignores sea ice - I need to revisit the budget code and equations to see how we decided to deal with fluxes from ice to ocean.
* Tom Schmaltz has already made subsets of sea ice extent - these need to be included in the analysis soon
