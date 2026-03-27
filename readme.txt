This is a brief summary for using the NIES-ML3 package. It is based on
the code we used to produced the dataset for GCB-2025 with minor revisions. 

Please contact <zeng@nies.go.jp> for any questions.

1. SOCAT CO2
	Python: "socat-co2.py"
	Use the script to extract ocean CO2 data. The results will be save 
in "./ml_io/netcdf/socat"
	
2. Sea surface temperature and ice cover data
	URL: ftp.cdc.noaa.gov/Datasets/noaa.oisst.v2.highres
	Use "noaa-oisst.py" to process the data. The monthly 1x1 degree means
of "sst" and "icec" will be saved in "./ml_io/netcdf/sst" and 
"./ml_io/netcdf/ices" respectively.

3. Sea surface salinity and mixing layer depth climatology
	URL: https://www.ncei.noaa.gov/access/world-ocean-atlas-2023/
	Use "woa-sss.py" and "woa-mld.py" to process the data. The monthly
1x1 degree means of "sss" and "mld" will be saved as 
"./ml_io/netcdf/sss.##.nc" and "./ml_io/netcdf/mld.##.nc" respectively.

4. Chl-a climatology 	
	URL: https://oceancolor.gsfc.nasa.gov/l3/
	Download "AQUA", "JPSS1", and "SNPP" and use "modis-chla-regrid.py"
to process the data first and then use "modis-chla-fill.py" to fill gaps.
The monthly 1x1 degree means will be saved as "./ml_io/netcdf/chl.##.nc" 

5. Surface air CO2 data
	URL: https://gml.noaa.gov/ccgg/mbl/data.php
	Download the surface CO2 data and use "noaa-xco2.py" to interpolate
CO2 to 1x1 degree mesh. The results will be saved in "./ml_io/netcdf/xco2".

6. Wind speed and pressure data
	URL: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels-monthly-means?tab=overview
	Download the monthly wind speed and surface data from the URL
and use "era5-regrid.py to process the data. The monthly 1x1 degree means
of "si10" and "sp" will be saved in "./ml_io/netcdf/si10" and 
"./ml_io/netcdf/sp" respectively.


7. Annual rate of air CO2
	URL: https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt
	Download the globally averaged marine surface annual mean growth rates
and used the template "trend.correction.xlsx" to calculate the fitted 
decadal trend. Save the results as "./ml_io/trend.txt".

8. Trend correction
	Python: "ml3-tf.py"
	Use the fitted trend as the first estimate of the ocean CO2 trend and then
use the leave-one-year-out (LOYO) validation method iteratively to obtain 
the ocean CO2 trend not accounted for by the fitted trend. We suggest using 
the gradient boot (GB) machine method (implemented by LightGBM) first as it 
is very fast; then use the random forest (RF) and neural network (NN) methods
starting with the converged trend. The RF and NN are much slower than GB, 
especially the NN method. If you use them starting from the fitted rate, 
you may not be able to get a converged trend within a reasonable time. 

8. CO2 mapping and flux calculation
	Python: "ml3-tf.py"
	Use the fitted and corrected trends for CO2 mapping. 

	

  

 