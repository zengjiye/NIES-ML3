import calendar
from shared import *

#ftp.cdc.noaa.gov/Datasets/noaa.oisst.v2.highres

def data_f(fname, vname):

    os.makedirs(f"./ml_io/netcdf/{vname}/", exist_ok=True)

    cdr = netCDF4.Dataset(fname)
    var = cdr.variables["lat"][:]
    assert(var[0] == -89.875)
    assert(var.size == 720)
    var = cdr.variables["lon"][:]
    assert(var[0] == 0.125)
    assert(var.size == 1440)
    var = cdr.variables["time"]
    time = netCDF4.num2date(var[:],var.units)
    var = cdr.variables[vname]
    k = 0
    
    for t in time:
    
        print(t.year, t.month, vname)
        v = var[k]
        k += 1
    
        I = v.mask == 0
        dat = np.zeros(v.shape)
        cnt = np.zeros(v.shape)
        dat[I] = v[I]
        cnt[I] = 1
    
        #4x4 grid mean
        dat = np.add.reduceat(
            np.add.reduceat(dat, np.arange(0, 720, 4), axis=0),
            np.arange(0, 1440, 4), axis=1
        )
        cnt = np.add.reduceat(
            np.add.reduceat(cnt, np.arange(0, 720, 4), axis=0),
            np.arange(0, 1440, 4), axis=1
        )
        I = cnt > 0
        dat[I] = dat[I] / cnt[I]
        
        I = cnt == 0
        if vname == "ice":
            dat[I] = 0
        else:
            dat[I] = missing_f()
        
        cdw, vaw = cdw_f(f"./ml_io/netcdf/{vname}/{vname}.{t.year}.{t.month:02d}.nc", vname, var.units)
        vaw[:] = dat
        cdw.close()
        
####################################

data_f("F:/NOAA/sst.mon.mean.nc", "sst")
data_f("F:/NOAA/icec.mon.mean.nc", "icec")
