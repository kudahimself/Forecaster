import pandas as pd

class Imputator:

    """
    next
    previous
    mode
    mean
    min
    max
    moving_avg
    fixed_value
    """

    @classmethod
    def impute(cls, ts_data, imp_type, fixed_value=None):

        match imp_type:

            case 'next':
                result = cls.impute_next(ts_data)

            case 'previous':
                result = cls.impute_previous(ts_data)

            case 'mode':
                result = cls.impute_mode(ts_data)

            case 'mean':
                result = cls.impute_mean(ts_data)

            case 'min':
                result = cls.impute_min(ts_data)
            
            case 'max':
                result = cls.impute_max(ts_data)

            case 'moving_avg':
                result = cls.impute_mva(ts_data)

            case 'fixed_value':
                result = cls.impute_fv(ts_data)

        return result
    
    @classmethod
    def impute_next(cls, ts_data):
        ts_data['values'].replace(0, pd.NA, inplace=True)
        ts_data['values'] = ts_data['values'].fillna(method='bfill')
        return ts_data 
