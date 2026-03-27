from shared import *

year = start_year()
cdr = netCDF4.Dataset("F:/SOCAT/SOCATv2025_tracks_gridded_monthly.nc")

lat = cdr.variables["ylat"][:]
assert(lat[0]==-89.5)
assert(lat[-1]==89.5)
assert(lat.size==180)

lon = cdr.variables["xlon"][:]
assert(lon[0]==-179.5)
assert(lon[-1]==179.5)
assert(lon.size==360)

var = cdr.variables["tmnth"]
time = netCDF4.num2date(var[:], var.units)
var = cdr.variables["fco2_ave_unwtd"]
os.makedirs(f"./ml_io/netcdf/socat/", exist_ok=True)

for k in range(time.size):
    t = time[k]
    if t.year < start_year()-2: continue
    print(t.year, t.month)
    cdw, vaw = cdw_f(f"./ml_io/netcdf/socat/fco2.{t.year}.{t.month:02d}.nc", "fco2", var.units)
    v = var[k - 1]
    v[v.mask] = missing_f()
    vaw[:] = np.roll(v, 180, axis=1)
    cdw.close()
