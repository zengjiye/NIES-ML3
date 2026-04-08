import tensorflow as tf
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from shared import *
import os, warnings

warnings.filterwarnings("ignore")

nn_epochs = 500
learning_rate = 0.001
batch_size = 1024
n_seed = 10

##############################################
#
def regressor_f(model, seed, ncol):

    if (model == 'nn'):
        tf.keras.utils.set_random_seed(seed)
        reg = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(ncol,)),
            tf.keras.layers.Dense(128, activation='tanh'),
            tf.keras.layers.Dense(128, activation='tanh'),
            tf.keras.layers.Dense(1)])
        reg.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate), loss='mean_absolute_error') 
    elif (model == 'rf'):
        reg = RandomForestRegressor(n_estimators=100,min_samples_leaf=50,random_state=seed,n_jobs=6)
    elif (model == 'gb'):
        reg = LGBMRegressor(n_estimators=250,num_leaves=100,random_state=seed,n_jobs=6,force_row_wise=True,verbose=0)

    return reg
    
##############################################
#
def bias_f(ml3, rate):

    Year, Y, Y_avg, Y_std, X, X_avg, X_std = ml_data(rate)

    fp = open(f"./ml_io/bias.tf_{ml3}.{rate:.4f}.csv",'w')
    fp.write(f"year, nd, bias, std, r2, std\n")

    for year in range(start_year(),end_year()+1):
    
        I = Year == year
        if I.sum() < 10: continue
        y_val = Y[I]
        x_val = X[I]
        I = Year != year
        y = Y[I]
        x = X[I]
        
        bias = np.zeros((n_seed,))
        r2 = np.zeros((n_seed,))
        
        for seed in range(n_seed):
            reg = regressor_f(ml3, seed+99, X.shape[1])
            if ml3 == "nn":
                reg.fit(x, y, epochs=nn_epochs, verbose=0, batch_size=batch_size)
                yf = reg.predict(x_val, verbose=0).reshape(y_val.shape)
            else:
                reg.fit(x, y)
                yf = reg.predict(x_val).reshape(y_val.shape) 
            r2[seed] = np.corrcoef(yf,y_val)[0,1]
            yf -= y_val
            bias[seed] = Y_std * yf.mean()
            print(year,seed,bias[seed],r2[seed])
        
        s = f"{year},{y_val.size},{bias.mean()},{bias.std()},{r2.mean()},{r2.std()}\n"
        print(ml3, s)
        fp.write(s)
        
    fp.close()
   
##############################################
#
def mapping_f(ml3, rate):

    Year, Y, Y_avg, Y_std, X, X_avg, X_std = ml_data(rate)

    models = []
    
    for seed in range(n_seed):
    
        reg = regressor_f(ml3, seed+99, X.shape[1])
        print(ml3, seed+1)
        if ml3 == 'nn':
            reg.fit(X, Y, epochs=nn_epochs, verbose=0, batch_size=batch_size)
        else:
            reg.fit(X, Y)
        bias = reg.predict(X).reshape(Y.shape) - Y
        print(ml3, seed+1, Y.std()*bias)
        models.append(reg)

    ############################
    
    path = f"./ml_io/tf_{ml3}"
    os.makedirs(path, exist_ok=True)

    lat, clon, slon = grid_mesh()

    delta = co2_delta(rate)
    
    for yy in range(start_year(), end_year() + 1):
    
        dco2 = delta[yy-start_year()]
        sst_avg = SST_avg(yy)
        
        for mm in range(1, 13):
        
            print(ml3, yy, mm)
            sst = SST_f(yy, mm)
            sss = SSS_f(yy, mm)
            chl = CHL_f(mm)
            mld = MLD_f(mm)
            dsst = sst - sst_avg
            I = np.logical_and(~chl.mask, ~mld.mask)
            I = np.logical_and(I, ~np.isnan(dsst))
            I = np.logical_and(I, sst > sst_min())
            I = np.logical_and(I, sss > sss_min())
            sst = sst[I].reshape((-1,))
            sss = sss[I].reshape((-1,))
            chl = chl[I].reshape((-1,))
            mld = mld[I].reshape((-1,))
            dsst = dsst[I].reshape((-1,))
            y = lat[I].reshape((-1,))
            cx = clon[I].reshape((-1,))
            sx = slon[I].reshape((-1,))
            
            d = {'sst':sst,'sss':sss,'chl':chl,'mld':mld,'dsst':dsst,'lat':y,'cosx':cx,'sinx':sx}
            X = pd.DataFrame(data=d)
            X -= X_avg
            X /= X_std
            X = X.to_numpy()
            
            count = 0
            
            for m in models:
                if ml3 == 'nn':
                    if count == 0:
                        co2 = m.predict(X, verbose=0)
                    else:
                        co2 += m.predict(X, verbose=0)
                else:
                    if count == 0:
                        co2 = m.predict(X)
                    else:
                        co2 += m.predict(X)
                count += 1
                
            co2 /= count
            co2 *= Y_std
            co2 += Y_avg
            co2 -= dco2
            v = np.empty(lat.shape)
            v[:] = missing_f()
            v[I] = co2.reshape((co2.size,))
            
            cdw, vaw = cdw_f(f"{path}/fco2.{yy}.{mm:02d}.nc", "fco2", "uatm")
            vaw[:] = v
            cdw.close()

