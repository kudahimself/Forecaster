import pandas as pd
from statistics import mode

class Imputator:

    def __init__(self, ts_data) -> None:
        self.data = ts_data

    def impute(self, ts_data, imp_type, tab, fixed_value=None):

        match imp_type:

            case 'next':
                result = self.impute_next(ts_data)

            case 'previous':
                result = self.impute_previous(ts_data)

            case 'mode':
                result = self.impute_mode(ts_data)

            case 'mean':
                result = self.impute_mean(ts_data)

            case 'min':
                result = self.impute_min(ts_data)
            
            case 'max':
                result = self.impute_max(ts_data)

            case 'moving_avg':
                result = self.impute_mva(ts_data)

            case 'fixed_value':
                result = self.impute_fv(ts_data, fixed_value)

        return result
    

    def impute_next(self, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_data['values'] = ts_data['values'].fillna(method='bfill')
        return ts_data
    
    def impute_previous(self, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_data['values'] = ts_data['values'].fillna(method='ffill')
        return ts_data

    def impute_mode(self, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_mode = mode(ts_data['values'].dropna())
        ts_data['values'] = ts_data['values'].fillna(ts_mode)
        return ts_data

    def impute_mean(self, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_mean = ts_data['values'].mean()
        ts_data['values'] = ts_data['values'].fillna(ts_mean)
        return ts_data

    def impute_min(self, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_min = ts_data['values'].min()
        ts_data['values'] = ts_data['values'].fillna(ts_min)
        return ts_data

    def impute_max(self, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_max = ts_data['values'].max()
        ts_data['values'] = ts_data['values'].fillna(ts_max)
        return ts_data

    def impute_mva(self, ts_data, window=3):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_data['values'] = ts_data['values'].fillna(ts_data['values'].rolling(window, min_periods=1).mean())
        return ts_data

    def impute_fv(self, ts_data, fixed_value):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_data['values'] = ts_data['values'].fillna(fixed_value)
        return ts_data
