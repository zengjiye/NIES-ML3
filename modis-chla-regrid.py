from shared import *

###################################

def process_file(root, file, sname):

    global iy, jx

    a = file.split("_")
    if a[0] != sname: return
    mm = a[2][4:6]
    print(sname, mm)

    cdr = netCDF4.Dataset(root+"/"+file)
    chl = cdr.variables["chlor_a"]
    units = chl.units
    chl = chl[:]
    vname = "chl"
    
    if iy is None:
        lat = cdr.variables["lat"][:]
        assert(lat[0] > 0)
        lon = cdr.variables["lon"][:]
        assert(lon[0] < 0)
        
        y = np.linspace(89, -89, 179)
        iy = np.zeros((y.size,), dtype="i")
        for i in range(y.size):
            iy[i] = np.where(lat < y[i])[0][0]
        iy = np.insert(iy, 0, 0)
        iy = np.append(iy, lat.size)
        assert(iy.size == 181)

        x = np.linspace(-179, 179, 359)
        jx = np.zeros((x.size,), dtype="i")
        for j in range(x.size):
            jx[j] = np.where(lon > x[j])[0][0]
        jx = np.insert(jx, 0, 0)
        jx = np.append(jx, lon.size)
        assert(jx.size == 361)
        
    avg = np.empty((180,360))
    avg[:] = np.nan
        
    for i in range(180):
        i1 = iy[i]
        i2 = iy[i+1]
        for j in range(360):
            j1 = jx[j]
            j2 = jx[j+1]
            v = chl[i1:i2,j1:j2]
            avg[i,j] = v.mean()

    os.makedirs(f"./ml_io/netcdf/{sname}", exist_ok=True)
    cdw, vaw = cdw_f(f"./ml_io/netcdf/{sname}/{vname}.{mm}.nc", vname, units)
    avg = np.flipud(avg)
    avg = np.roll(avg, 180, axis=1)
    vaw[:] = avg
    cdw.close()

###################################
# https://oceancolor.gsfc.nasa.gov/l3/

for sname in ("AQUA", "JPSS1", "SNPP"):
    iy = None
    jx = None
    for root, dirs, files in os.walk("F:/MODIS/CHLA_2025/data"):
        for file in files:
            if len(file) < 30: continue
            if file.endswith(".nc"):
                process_file(root, file, sname)
