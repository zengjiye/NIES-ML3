from shared import *

# https://www.ncei.noaa.gov/access/world-ocean-atlas-2023/

for mm in range(1, 13):

    lat, lon = grid_f()
    cdr = netCDF4.Dataset(f"F:/woa/woa23_decav91C0_s{mm:02d}_01.nc")
    v = cdr.variables["time"][0]
    print(mm, v)
    
    v = cdr.variables["lat"][:]
    assert(v[0] == lat[0])
    assert(v[-1] == lat[-1])
    v = np.roll(cdr.variables["lon"][:],180)
    I = v < 0
    v[I] += 360
    assert(v[0] == lon[0])
    assert(v[-1] == lon[-1])
    v = cdr.variables["s_an"][0,0]
    v[v.mask] = missing_f()
    v = np.roll(v,180,axis=1)
    cdw, vaw =  cdw_f(f"./ml_io/netcdf/sss.{mm:02d}.nc", "sss", "1e-3")
    vaw[:] = v
    cdw.close()




