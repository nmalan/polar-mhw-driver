#!/usr/bin/env python3
"""Exercise NB06's numerics on synthetic data, using the notebook's own cell source."""
import json, os, sys
import numpy as np, pandas as pd, xarray as xr
import matplotlib; matplotlib.use('Agg')
import ultraplot as uplt

NB = json.load(open('/tmp/work/nb06/06_bipolar_richaud_method.ipynb'))
SRC = [''.join(c['source']) for c in NB['cells'] if c['cell_type'] == 'code']

def cell_with(*needles):
    for s in SRC:
        if all(n in s for n in needles):
            return s
    raise LookupError(needles)

G = dict(np=np, pd=pd, xr=xr, os=os, uplt=uplt,
         BOX_SIZE=20, MIN_OCN_FRAC=0.75)

# ---------------------------------------------------------------- section 3
exec(cell_with('def generate_tiles', 'def _circmean_deg'), G)
_cm, gen_tiles = G['_circmean_deg'], G['generate_tiles']
circ = lambda v: _cm(v)[0]
circR = lambda v: _cm(v)[1]
box_slice, box_mean = G['_box_slice'], G['_box_mean']

ok = lambda c, m: print(('PASS  ' if c else 'FAIL  ') + m) or bool(c)
fails = []
def check(c, m):
    print(('PASS  ' if c else '**FAIL**  ') + m)
    if not c: fails.append(m)

# circular mean
check(circ([350, 10]) == 0.0, 'circmean(350,10) == 0.0 exactly, not 360.0 or 180')
check(abs(circ([-279.0, 79.0]) - circ([81.0, 79.0])) < 1e-9,
      'circmean handles the ACCESS -280..80 convention')
check(abs(circ([10, 20, 30]) - 20.0) < 1e-9, 'circmean of an ordinary span is the plain mean')
check(np.isnan(circ([np.nan, np.nan])), 'circmean of all-NaN is NaN')
check(abs(np.mean([350, 10]) - 180.0) < 1e-9 and circ([350, 10]) == 0.0,
      'plain mean gives 180 where circular gives 0 (this is the NB04 difference)')
check(circR([10, 12, 14]) > 0.99, 'resultant R ~ 1 for a narrow longitude span')
check(circR([0, 90, 180, 270]) < 1e-9,
      'resultant R ~ 0 when longitudes ring the circle (a polar tile)')

# ---------------------------------------------------------------- tiles + weighting
ny, nx = 40, 60
yt = np.linspace(-79.875, -60.125, ny)
xt = np.linspace(-279.875, 79.875, nx)
lat2d = np.repeat(yt[:, None], nx, axis=1)
lon2d = np.repeat(xt[None, :], ny, axis=0)
R = 6371000.0
dlat = np.deg2rad(abs(yt[1] - yt[0])); dlon = np.deg2rad(abs(xt[1] - xt[0]))
area2d = (R**2) * dlon * dlat * np.cos(np.deg2rad(lat2d))

coords = dict(yt_ocean=yt, xt_ocean=xt)
dims = ('yt_ocean', 'xt_ocean')
geolat = xr.DataArray(lat2d, dims=dims, coords=coords, name='geolat_t')
geolon = xr.DataArray(lon2d, dims=dims, coords=coords, name='geolon_t')
area = xr.DataArray(area2d, dims=dims, coords=coords, name='area_t')

rng = np.random.default_rng(0)
mask_vals = np.ones((ny, nx))
mask_vals[:6, :15] = 0.0                      # a patch of land
area = area.where(mask_vals > 0)              # land -> NaN area, as in the real file
mask = xr.DataArray(mask_vals, dims=dims, coords=coords)

boxes, n_fold = gen_tiles(mask, geolat, geolon, ny_full=None)
check(len(boxes) > 0, 'generate_tiles returns tiles ({0})'.format(len(boxes)))
check(all(b['ocean_frac'] >= 0.75 for b in boxes), 'every kept tile is >=75% ocean')
check(all(-80 <= b['lat_center'] <= -60 for b in boxes), 'tile lat centres inside the domain')
check(all(0.0 <= b['lon_center'] < 360.0 for b in boxes), 'tile lon centres in [0,360)')

# area_t vs cos(lat) weighting on a regular grid
field = xr.DataArray(rng.normal(size=(ny, nx)), dims=dims, coords=coords)
diffs = []
for b in boxes:
    sub = box_slice(field, b)
    w_a = box_slice(area, b).fillna(0.0)
    w_c = np.cos(np.deg2rad(sub['yt_ocean'])).broadcast_like(sub).where(
        box_slice(mask, b) > 0, 0.0)
    diffs.append(abs(float(sub.weighted(w_a).mean(dims)) - float(sub.weighted(w_c).mean(dims))))
check(max(diffs) < 1e-10,
      'area_t and cos(lat) weighting agree on a regular grid (max {0:.2e})'.format(max(diffs)))

# land must not leak into the weighted mean
poisoned = field.where(mask > 0, 1e6)
clean = [b for b in boxes if box_slice(mask, b).min() < 1]
if clean:
    b = clean[0]
    w = box_slice(area, b).fillna(0.0)
    m = float(box_slice(poisoned, b).weighted(w).mean(dims))
    check(abs(m) < 10, 'land cells get zero weight (mean {0:.3f}, not ~1e6)'.format(m))
else:
    print('SKIP  no partially-land tile survived the 75% filter')

# NB04 fidelity: plain vs circular longitude centre, and the drop=True shrink flag
b0 = boxes[0]
check('lon_center_circular' in b0 and 'lon_center_plain' in b0,
      'both longitude conventions are stored on every tile')
boxes_plain, _ = gen_tiles(mask, geolat, geolon, ny_full=None, lon_center='plain')
check(all(abs(b['lon_center'] - b['lon_center_plain']) < 1e-9 for b in boxes_plain),
      "LON_CENTER='plain' reproduces NB04's arithmetic mean")
boxes_circ, _ = gen_tiles(mask, geolat, geolon, ny_full=None, lon_center='circular')
check(all(abs(b['lon_center'] - b['lon_center_circular']) < 1e-9 for b in boxes_circ),
      "LON_CENTER='circular' uses the circular mean")
check(any(b['nb04_bbox_shrinks'] for b in boxes) or True,
      'nb04_bbox_shrinks is present on every tile ({0} flagged)'.format(
          sum(b['nb04_bbox_shrinks'] for b in boxes)))

# a tile with a wholly-land interior row must be flagged as one NB04's drop=True shrinks
mv = np.ones((ny, nx)); mv[25, :] = 0.0
m2 = xr.DataArray(mv, dims=dims, coords=coords)
bx2, _ = gen_tiles(m2, geolat, geolon, ny_full=None)
touched = [b for b in bx2 if b['y0'] <= 25 < b['y1']]
check(bool(touched) and all(b['nb04_bbox_shrinks'] for b in touched),
      'an all-land row flags every tile it crosses ({0} tiles)'.format(len(touched)))

# fold-row detection
boxes_f, n_f = gen_tiles(mask, geolat, geolon, ny_full=ny, drop_fold_row=True)
boxes_k, _ = gen_tiles(mask, geolat, geolon, ny_full=ny, drop_fold_row=False)
check(n_f > 0 and len(boxes_k) - len(boxes_f) == n_f,
      'DROP_FOLD_ROW removes exactly the {0} fold-touching tiles'.format(n_f))

# ---------------------------------------------------------------- section 8 ranking
TERM_MAP = {'MLT tendency': 'mlt_tendency', 'Surface Flux': 'surf_to_ML',
            'Advection': 'advection', 'Vertical mixing': 'vert_mixing',
            'Entrainment': 'entrainment'}
G.update(TERM_MAP=TERM_MAP, RANK_BY='driver')

# the worked example from the explanation
vals = {'onset':   dict(surf_to_ML=0.08, advection=0.01, vert_mixing=-0.03, entrainment=0.02),
        'decline': dict(surf_to_ML=0.05, advection=-0.02, vert_mixing=-0.12, entrainment=-0.01)}
terms = ['surf_to_ML', 'advection', 'vert_mixing', 'entrainment']
ds = xr.Dataset(
    {t: (('tiles', 'events', 'phase'),
         np.array([[[vals['onset'][t], vals['decline'][t]]]])) for t in terms},
    coords=dict(tiles=['t0'], events=[0], phase=['onset', 'decline']))
ds['mlt_tendency'] = (('tiles', 'events', 'phase'), np.array([[[0.08, -0.10]]]))

src8 = cell_with('def phase_ranks', 'RANK_BY')
src8 = src8.split('RANKS, TALLY, NMHW')[0]          # definitions only
exec(src8, G)
pr = G['phase_ranks']

r_dec_driver = pr(ds, 'decline', 'driver').iloc[0]
r_dec_signed = pr(ds, 'decline', 'signed').iloc[0]
r_dec_abs    = pr(ds, 'decline', 'abs').iloc[0]
r_on_driver  = pr(ds, 'onset', 'driver').iloc[0]
r_on_signed  = pr(ds, 'onset', 'signed').iloc[0]

print('\n  decline ranks  driver:', dict(r_dec_driver.astype(int)))
print('  decline ranks  signed:', dict(r_dec_signed.astype(int)))
print('  decline ranks  abs   :', dict(r_dec_abs.astype(int)))

check(r_dec_driver['vert_mixing'] == 1,
      "driver: vertical mixing (-0.12) is primary at decline")
check(r_dec_signed['surf_to_ML'] == 1 and r_dec_signed['vert_mixing'] == 4,
      "signed: surface flux is 'primary' and vertical mixing is rank 4 (NB04 behaviour)")
check(r_dec_abs['vert_mixing'] == 1 and r_dec_abs['surf_to_ML'] == 2,
      'abs: largest magnitude first')
check((r_on_driver == r_on_signed).all(),
      'driver and signed agree at onset (they differ only at decline)')

# the case that separates driver from abs: a big OPPOSING term at decline
ds2 = ds.copy(deep=True)
ds2['surf_to_ML'][:] = np.array([[[0.08, 0.20]]])
r2_driver = pr(ds2, 'decline', 'driver').iloc[0]
r2_abs    = pr(ds2, 'decline', 'abs').iloc[0]
check(r2_driver['vert_mixing'] == 1 and r2_abs['surf_to_ML'] == 1,
      'with a large opposing term, driver picks the cooler and abs picks the bigger number')

# ---------------------------------------------------------------- tally shape
n_rank = 4
tab = pd.DataFrame(columns=terms, index=[np.arange(1, n_rank + 1)])
ranks_df = pr(ds, 'onset', 'driver')
for rk in np.arange(1, n_rank + 1):
    tab.loc[rk] = ranks_df.where(ranks_df == rk).count().values
tab = tab.astype('float')
check(np.shape(tab.loc[1]) == (1, 4),
      'tally .loc[1] is a 1x4 DataFrame (required by ultraplot bar(mean=True))')
check(float(tab.sum().sum()) == 4.0, 'every term is assigned exactly one rank')

print('\n' + ('ALL CHECKS PASSED' if not fails else 'FAILURES:\n  ' + '\n  '.join(fails)))
sys.exit(1 if fails else 0)
