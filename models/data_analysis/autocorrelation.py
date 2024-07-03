import pandas as pd
import statsmodels.tsa.api as smt


class AutoCorrelation():

    @classmethod
    def calculate_ac(cls, data, lags=30):
        return smt.acovf(data)[:lags]
