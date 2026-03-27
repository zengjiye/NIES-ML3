import os
import numpy as np
import netCDF4
import pandas as pd

##############################################

def start_year(): return 1982

def end_year(): return 2024

def ref_year(): return int(start_year() + (end_year() - start_year()) / 2)

def sst_min(): return -5.0

def sss_min(): return 15.0

def co2_min(): return 50.0

def co2_max(): return 1000.0

def missing_f(): return np.nan

##############################################

def grid_f():

    lat = np.linspace(-89.5,89.5,180)
    lon = np.linspace(0.5,359.5,360)
    
    return lat, lon

##############################################

def grid_map():

    lat, lon = grid_f()
    lon, lat = np.meshgrid(lon, lat)
    
    return lat, lon

##############################################

def grid_mesh():

    lat, lon = grid_f()
    lon, lat = np.meshgrid(lon, lat)
    lon *= np.pi/180
    
    return lat, np.cos(lon), np.sin(lon)

##############################################

def cdw_f(fname, vname, units):

    lat, lon = grid_f()
    missing = missing_f()
    cdw = netCDF4.Dataset(fname, "w")
    cdw.createDimension("lat", lat.size)
    var = cdw.createVariable("lat", lat.dtype, ("lat",))
    var[:] = lat
    cdw.createDimension("lon", lon.size)
    var = cdw.createVariable("lon", lon.dtype, ("lon",))
    var[:] = lon
    var = cdw.createVariable(vname, "f4", ("lat","lon"), fill_value=missing)
    var.units = units
    var[:] = missing
    
    return cdw, var

##############################################

def co2_delta(rate):

    D = np.loadtxt(f"./ml_io/trend.txt", skiprows=1)
    Yr = D[:,0].astype('i4')
    R = D[:,1] - rate
    assert(Yr[0] == start_year())
    assert(Yr[-1] == end_year())
    
    nr = Yr.size
    for i in range(nr):
        if Yr[i] == ref_year(): break
    
    R1 = R[0:i].copy()
    R1 = np.flip(np.cumsum(np.flip(R1)))
    R2 = R[i:nr].copy()
    R2[0] = 0
    R2 = -np.cumsum(R2)
    R = np.hstack((R1,R2))
    
    return R

##############################################
#
def input_f():

    lat, lon = grid_map()

    fname = f"./ml_io/input.csv"
    f = open(fname, "w")
    f.write("#year,month,lat,lon,co2,sst,sss,chl,mld,dsst\n")
    k = 0
    count = 0

    for yy in range(start_year(), end_year()+1):
    
        k += 1
        avg = SST_avg(yy)
        
        for mm in range(1, 13):
        
            co2 = socat_f(yy, mm)
            sst = SST_f(yy, mm)
            sss = SSS_f(yy, mm)
            chl = CHL_f(mm)
            mld = MLD_f(mm)
            dsst = sst - avg
            I = np.logical_and(~chl.mask, ~mld.mask)
            I = np.logical_and(I, ~np.isnan(dsst))
            I = np.logical_and(I, sst>sst_min())
            I = np.logical_and(I, sss>sss_min())
            I = np.logical_and(I, co2>co2_min())
            I = np.logical_and(I, co2<co2_max())
            if I.sum() < 2: continue
            vy = lat[I]
            vx = lon[I]
            vco2 = co2[I]
            vsst = sst[I]
            vsss = sss[I]
            vchl = chl[I]
            vmld = mld[I]
            dsst = dsst[I]
            
            for i in range(vy.size):
                s  = f"{yy},{mm},{vy[i]},{vx[i]},{vco2[i]:.2f},"
                s += f"{vsst[i]:.2f},{vsss[i]:.2f},{vchl[i]:.5f},{vmld[i]:.0f},"
                s += f"{dsst[i]:.2f}"
                if count % 1000 == 0: print(s)
                count += 1
                f.write(s+"\n")

    f.close()
    
    return fname
    
##############################################
#
def ml_data(rate):

    delta = co2_delta(rate)

    DF = pd.read_csv(f"./ml_io/input.csv",sep=',',header=0)
    Year = DF['#year']
    Y =  DF['co2']
    k = 0
    for year in range(start_year(), end_year()+1):
        I = Year == year
        Y[I] +=delta[k]
        k += 1
    Y_avg = Y.mean(axis=0)
    Y_std = Y.std(axis=0)
    Y -= Y_avg
    Y /= Y_std

    X = DF[['sst','sss','chl','mld','dsst','lat']]
    v = DF['lon']
    v *= np.pi/180.0;
    d = {'cosx': np.cos(v), 'sinx': np.sin(v)}
    v = pd.DataFrame(data=d)
    X = pd.concat([X,v],axis=1)
    X_avg = X.mean(axis=0)
    X_std = X.std(axis=0)
    X -= X_avg
    X /= X_std

    return Year, Y.to_numpy(), Y_avg, Y_std, X.to_numpy(), X_avg, X_std
   
##############################################
#
def flux_f(ml3, coef):

    f = open(f"./ml_io/flux.{ml3}.csv", "w")
    f.write("year,flux\n")

    Area = Area_f()
    Area[Area.mask] = 0
    
    for yy in range(start_year(), end_year()+1):
        sum = 0
        for mm in range(1, 13):
            print(ml3, yy, mm)
            CO2w = fCO2_f(ml3, yy, mm)
            SST = SST_f(yy, mm)
            SSS = SSS_f(yy, mm)
            CO2a = xCO2_f(yy, mm)
            WND = WIND_f(yy, mm)
            PS = PS_f(yy, mm)
    
            PS *= 9.86923e-6            #Pa to atm
            CO2a = xco2_pco2(CO2a, SST, SSS, PS)
            CO2w = fco2_pco2(CO2w, SST, PS)
            dCO2 = CO2a - CO2w          #positive downward
            Kw = kw_f(SST, WND, coef)   #m/s
            K0 = k0_f(SST, SSS, PS)     #mol/m3/uatm
            Flux = dCO2 * Kw * K0       #mol/m2/s
            
            cdw, vaw = cdw_f(f"./ml_io/tf_{ml3}/flux.{yy}.{mm:02d}.nc", "flux", "mol m-2 s-1")
            vaw[:] = Flux
            cdw.close()
            
            Flux *= Area                #mol/s
            sum += Flux.sum()*(365*24*60*60*12e-15) #pg yr-1
        
        f.write(f"{yy},{sum/12}\n")
        
    f.close()

##############################################

def fCO2_f(ml3, year, mm):
    return netCDF4.Dataset(f"./ml_io/tf_{ml3}/fco2.{year}.{mm:02d}.nc").variables["fco2"][:]

##############################################

def CHL_f(mm):

    return netCDF4.Dataset(f"./ml_io/netcdf/chl.{mm:02d}.nc").variables["chl"][:]

##############################################

def MLD_f(mm):

    return netCDF4.Dataset(f"./ml_io/netcdf/mld.{mm:02d}.nc").variables["mld"][:]

##############################################

def SSS_f(yy, mm):

#    return netCDF4.Dataset(f"./ml_io/netcdf/sss/sss.{yy}.{mm:02d}.nc").variables["sss"][:]
    return netCDF4.Dataset(f"./ml_io/netcdf/sss.{mm:02d}.nc").variables["sss"][:]

##############################################

def SST_f(yy, mm):

    return netCDF4.Dataset(f"./ml_io/netcdf/sst/sst.{yy}.{mm:02d}.nc").variables["sst"][:]

##############################################

def SST_avg(yy):

    for mm in range(1, 13):
        sst = SST_f(yy, mm)
        if mm == 1:
            avg = np.zeros(sst.shape)
            cnt = np.zeros(sst.shape)
        avg += sst
        I = sst > sst_min()
        cnt[I] += 1

    I = cnt == 12
    avg[I] /= 12
    avg[~I] = np.nan
    
    return avg

##############################################

def ICE_f(yy, mm):
    return netCDF4.Dataset(f"./ml_io/netcdf/icec/icec.{yy}.{mm:02d}.nc").variables["icec"][:]

##############################################

def xCO2_f(yy, mm):

    return netCDF4.Dataset(f"./ml_io/netcdf/xco2/xco2.{yy}.{mm:02d}.nc").variables["xco2"][:]

##############################################

def socat_f(year, mm):
    return netCDF4.Dataset(f"./ml_io/netcdf/socat/fco2.{year}.{mm:02d}.nc").variables["fco2"][:]

##############################################

def fordetal_f(year, mm):
    return netCDF4.Dataset(f"./ml_io/netcdf/fordetal/fco2.{year}.{mm:02d}.nc").variables["fco2"][:]

##############################################

def WIND_f(yy, mm):

    return netCDF4.Dataset(f"./ml_io/netcdf/si10/si10.{yy}.{mm:02d}.nc").variables["si10"][:]

##############################################

def PS_f(yy, mm):

    return netCDF4.Dataset(f"./ml_io/netcdf/sp/sp.{yy}.{mm:02d}.nc").variables["sp"][:]

##############################################

def Area_f():

    return netCDF4.Dataset("./ml_io/netcdf/area.nc").variables["area"][:]

##############################################

def Seafrac_f():

    return netCDF4.Dataset("./ml_io/netcdf/seafrac.nc").variables["seafrac"][:]

##############################################
#
def alpha_coef():

    count = 0
    alpha = 0.0
    
    Area = Area_f()
    
    for yy in range(1990, 2020):
    
        print(yy)
        for mm in range(1, 13):
        
            ICE = ICE_f(yy, mm)
            ICE[ICE.mask] = 0
            SST = SST_f(yy, mm)
            WND = WIND_f(yy, mm)
            I = np.logical_and(ICE==0, Area>0)
            I = np.logical_and(I, ~SST.mask)
            SST = SST[I]
            WND = WND[I]
            A = Area[I]
            Sc = 2116.8 - 136.25*SST + 4.7353*np.power(SST,2) - 0.092307*np.power(SST,3) + 0.0007555*np.power(SST,4)
            #Fay et al. (2021)
            kw = np.power(WND,2)/np.sqrt(Sc/660.0)
            #area weighted kw mean()
            kw *= A / A.sum()
            avg = kw.sum()
            alpha += 16.5/avg
            count += 1
            
    alpha /= count
    
    print(alpha)
    
    return alpha

##############################################
#
def kw_f(TC, Wnd, coef):

    #Schmidt number (Table 1)
    I = TC<-2
    TC[I] = -2
    I = TC>40
    TC[I] = 40
    Sc = 2116.8-136.25*TC+4.7353*TC*TC-0.092307*np.power(TC,3)+0.0007555*np.power(TC,4)
    #Gas exchange coefficient (cm/hr)
    Kw = coef*Wnd*Wnd/np.sqrt(Sc/660.0)
    Kw /= 100.0*3600.0               #cm/hr to m/s
    
    return Kw
    
##############################################
#
def vapor_f(TK, SSS):

    #Eq.10 of Weiss & Price (1980) (atm)
    pH2O = np.exp(24.4543-67.4509*(100/TK)-4.8489*np.log(TK/100.0)-0.000544*SSS)
    
    return pH2O
    
##############################################
#
def solibolity_f(TC, SSS):

    #Wanninkhof (2014)
    TK = TC + 273.15
    #Solubility (mol/L/atm) (Table 2)
    T100 = TK/100.0
    K0 = -58.0931+90.5069*(100.0/TK)+22.2940*np.log(T100)+SSS*(0.027766-0.025888*(T100)+0.0050578*np.power(T100,2))
    K0 = np.exp(K0)
    K0 *= 1.e3*1.e-6        # mol/L/atm to mol/m3/uatm
    
    return K0
    
##############################################
#
def k0_f(TC, SSS, PS):

    #Wanninkhof (2014)
    TK = TC + 273.15
    #Solubility (mol/L/atm) (Table 2)
    T100 = TK/100.0
    K0 = -58.0931+90.5069*(100.0/TK)+22.2940*np.log(T100)+SSS*(0.027766-0.025888*(T100)+0.0050578*np.power(T100,2))
    K0 = np.exp(K0)
    K0 *= 1.e3*1.e-6        # mol/L/atm to mol/m3/uatm
    #correction for vapor pressure
    K0 /= PS - vapor_f(TK, SSS)
    
    return K0

##############################################

def xco2_pco2(xCO2, SST, SSS, Ps):

    TK = SST+273.15
    pCO2 = xCO2*(Ps - vapor_f(TK, SSS))
    
    return pCO2
    
##############################################

def pco2_fco2(pCO2, SST, Ps):

    return pCO2 * virial_coeff(SST, Ps)
    
##############################################
#
def fco2_pco2(fCO2, SST, Ps):

    return fCO2 / virial_coeff(SST, Ps)

##############################################
#
def kw_f(TC, Wnd, coef):
    #Schmidt number (Table 1)
    I = TC<-2
    TC[I] = -2
    I = TC>40
    TC[I] = 40
    Sc = 2116.8-136.25*TC+4.7353*TC*TC-0.092307*np.power(TC,3)+0.0007555*np.power(TC,4)
    #Gas exchange coefficient (cm/hr)
    Kw = coef*Wnd*Wnd/np.sqrt(Sc/660.0)
    Kw /= 100.0*3600.0                          #cm/hr to m/s
    return Kw
    
##############################################
#
def vapor_f(TK, SSS):
    #Eq.10 of Weiss & Price (1980) (atm)
    pH2O = np.exp(24.4543-67.4509*(100/TK)-4.8489*np.log(TK/100.0)-0.000544*SSS)
    return pH2O
    
##############################################
#
def solibolity_f(TC, SSS):
    #Wanninkhof (2014)
    TK = TC + 273.15
    #Solubility (mol/L/atm) (Table 2)
    T100 = TK/100.0
    K0 = -58.0931+90.5069*(100.0/TK)+22.2940*np.log(T100)+SSS*(0.027766-0.025888*(T100)+0.0050578*np.power(T100,2))
    K0 = np.exp(K0)
    K0 *= 1.e3*1.e-6        # mol/L/atm to mol/m3/uatm
    return K0
    
##############################################
#
def k0_f(TC, SSS, PS):
    #Wanninkhof (2014)
    TK = TC + 273.15
    #Solubility (mol/L/atm) (Table 2)
    T100 = TK/100.0
    K0 = -58.0931+90.5069*(100.0/TK)+22.2940*np.log(T100)+SSS*(0.027766-0.025888*(T100)+0.0050578*np.power(T100,2))
    K0 = np.exp(K0)
    K0 *= 1.e3*1.e-6        # mol/L/atm to mol/m3/uatm
    #correction for vapor pressure
    K0 /= PS - vapor_f(TK, SSS)
    return K0

##############################################

def xco2_pco2(xCO2, SST, SSS, Ps):
    TK = SST+273.15
    pCO2 = xCO2*(Ps - vapor_f(TK, SSS))
    return pCO2
    
##############################################

def pco2_fco2(pCO2, SST, Ps):
    return pCO2 * virial_coeff(SST, Ps)
    
##############################################
#
def fco2_pco2(fCO2, SST, Ps):
    return fCO2 / virial_coeff(SST, Ps)

##############################################
#
def virial_coeff(SST, Ps):

    #Weiss (1974); Eq.11 (cm3 mol-1)
    TK = SST+273.15
    I = TK<273.0
    TK[I] = 273.0
    I = TK>313.0
    TK[I] = 313.0
    a=57.7-0.118*TK
    #Eq.6  (cm3 mol-1)
    TK = SST+273.15
    b = -1636.75+12.0408*TK-3.27975e-2*TK*TK+3.16528e-5*np.power(TK,3)
    #Eq.9; R=82.05746 cm3 atm K-1 mol-1
    return np.exp((b+2.0*a)*Ps/(82.05746*TK))
    