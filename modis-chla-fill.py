from shared import *

chl_all = np.empty((12, 180, 360))
chl_min = np.empty((180 ,360))
chl_min[:] = 1e32

#####################

for mm in range(12):
        
    fname = f"./ml_io/netcdf/XXX/chl.{mm+1:02d}.nc"
    chl = netCDF4.Dataset(fname.replace("XXX","SNPP")).variables["chl"][:]
    
    ch2 = netCDF4.Dataset(fname.replace("XXX","JPSS1")).variables["chl"][:]
    I = np.logical_and(chl.mask==True, ch2.mask==False)
    chl[I] = ch2[I]
    chl.mask[I] = False
    
    ch2 = netCDF4.Dataset(fname.replace("XXX","AQUA")).variables["chl"][:]
    I = np.logical_and(chl.mask==True, ch2.mask==False)
    chl[I] = ch2[I]
    chl.mask[I] = False
    
    chl[chl.mask] = np.nan
    chl_all[mm,:] = chl
        
    I = chl < chl_min
    chl_min[I] = chl[I]

#####################
        
chl_min[chl_min > 1e31] = np.nan

for mm in range(12):
    chl = chl_all[mm,:]
    I = np.logical_and(np.isnan(chl), ~np.isnan(chl_min))
    chl[I] = chl_min[I]
    cdw, vaw = cdw_f(f"./ml_io/netcdf/chl.{mm+1:02d}.nc", "chl", "log(1+chl)")
    vaw[:] = np.log(1 + chl)
    cdw.close()
