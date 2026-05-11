from shared import *

#https://gml.noaa.gov/ccgg/mbl/data.php

def ext_co2(yy1, yy2, rate):
    for mm in range(1, 13):
        xco2 = xCO2_f(yy1, mm)
        xco2 += rate
        cdw, vaw = cdw_f(f"./ml_io/netcdf/xco2/xco2.{yy2}.{mm:02d}.nc", "xco2", "ppm")
        vaw[:] = xco2
        cdw.close()

##############################

def surf_co2():
    os.makedirs(f"./ml_io/netcdf/xco2", exist_ok=True)

    dat = np.loadtxt("F:/noaa/co2_GHGreference.1581313063_surface.txt")
    yr = dat[:, 0].astype("i4")
    dat = dat[:,range(1,dat.shape[1],2)]
    
    yp = np.linspace(-1.0, 1.0, dat.shape[1])
    lat, lon = grid_f()
    lat = np.sin(np.pi*lat/180.0)

    for yy in range(start_year(), end_year()+1):
        k = yr == yy
        if k.sum() != 48: continue
        vyr = dat[k]
        for mm in range(0, 12):
            print(yy, mm+1)
            i = mm * 4
            vmm = np.mean(vyr[i:i+4], axis=0)
            v = np.interp(lat, yp, vmm)
            cdw, vaw = cdw_f(f"./ml_io/netcdf/xco2/xco2.{yy}.{mm+1:02d}.nc", "xco2", "ppm")
            for j in range(lon.size): vaw[:,j] = v
            cdw.close()

##############################

#surf_co2()
#ext_co2(2023, 2024, 3.33)
