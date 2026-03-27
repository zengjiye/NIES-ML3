from shared import *

#https://www.ncei.noaa.gov/access/world-ocean-atlas-2018/

for mm in range(1, 13):
    print(mm)
    lat, lon = grid_f()
    cdr = netCDF4.Dataset(f"F:/woa/woa18_A5B7_M02{mm:02d}_01.nc")
    v = cdr.variables["lat"][:]
    assert(v[0] == lat[0])
    assert(v[-1] == lat[-1])
    v = np.roll(cdr.variables["lon"][:],180)
    I = v < 0
    v[I] += 360
    assert(v[0] == lon[0])
    assert(v[-1] == lon[-1])
    v = cdr.variables["M_an"][0,0]
    v[v.mask] = missing_f()
    v = np.roll(v,180,axis=1)
    cdw, vaw =  cdw_f(f"./ml_io/netcdf/mld.{mm:02d}.nc", "mld", "m")
    vaw[:] = v
    cdw.close()



