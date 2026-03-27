from cftime import num2date
from shared import *

#souce: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels-monthly-means?tab=overview

def regrid(path, vname):

    os.makedirs(f"./ml_io/netcdf/{vname}/", exist_ok=True)

    def grid_f(fname):

        cdr = netCDF4.Dataset(fname)
        lat = cdr.variables["latitude"][:]
        assert(lat[0] == 90)
        assert(lat.size == 721)
        lon = cdr.variables["longitude"][:]
        assert(lon[0] == 0)
        assert(lon.size == 1440)
        var = cdr.variables["valid_time"]
        time = netCDF4.num2date(var[:],var.units)
        var = cdr.variables[vname]
        k = 0
    
        for t in time:
            print(t.year, t.month, vname)
            v = var[k]
            k += 1
            assert(v.mask.sum() == 0)
            
            #pack values at 0 degree to the end
            c = v[:,0].reshape((v.shape[0],1))
            v = np.hstack((v,c))

            #interpolate to grid center
            v = 0.5 * (v[:,0:-1] + v[:,1:])
            v = 0.5 * (v[0:-1,:] + v[1:,:])
            
            #4x4 grid mean
            v = np.add.reduceat(
                np.add.reduceat(v, np.arange(0, 720, 4), axis=0),
                np.arange(0, 1440, 4), axis=1
            )
            v /= 16.0
            
            cdw, vaw = cdw_f(f"./ml_io/netcdf/{vname}/{vname}.{t.year}.{t.month:02d}.nc", vname, var.units)
            vaw[:] = np.flipud(v)       #(90,-90) to (-90,90)
            cdw.close()
        
    for root, dirs, files in os.walk(path):
        for file in files:
            grid_f(root + "/" + file)

##################################

regrid("F:/ERA5/10m_wind_speed", "si10")
regrid("F:/ERA5/surface_pressure", "sp")