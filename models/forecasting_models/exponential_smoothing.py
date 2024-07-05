import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_squared_error

class ExponentialSmoothingModel:
    def __init__(self, dataframe, freq, target_column='values', trend=None, seasonal='add'):
        self.dataframe = dataframe.fillna(0).copy()
        self.freq = freq

        # Ensure all values are positive by adding a constant
        self.shift_constant = abs(dataframe['values'].min()) + 1
        self.dataframe['values'] =self.dataframe['values'] + self.shift_constant
        self.target_column = target_column
        self.seasonal_periods = None
        self.trend = trend
        self.seasonal = seasonal
        
        # Preprocess the dataframe to handle datetime columns
        self._preprocess_dataframe()

        self.y = self.dataframe[self.target_column]
        self.train_size = int(len(self.y) * 0.8)
        self.y_train = self.y.iloc[:self.train_size]
        self.y_test = self.y.iloc[self.train_size:]
        self.model = None
        self.fitted_model = None
        self.mse = None
        if self.seasonal_periods is None:
            self.seasonal_periods = self._find_best_seasonal_period()
    
    def _find_best_seasonal_period(self):
        best_mse = float('inf')
        best_period = 1  # Start with a reasonable default period

        for period in range(2, 31):  # Checking periods from 2 to 30
            try:
                model = ExponentialSmoothing(
                    self.y_train, 
                    seasonal_periods=period,
                    trend=self.trend, 
                    seasonal=self.seasonal,
                    initialization_method='estimated',
                    freq=self.freq
                )
                fitted_model = model.fit()
                predictions = fitted_model.predict(start=0, end=len(self.y_train) - 1)
                mse = mean_squared_error(self.y_train, predictions)
                if mse < best_mse:
                    best_mse = mse
                    best_period = period
            except Exception as e:
                print(f"Could not fit model for period {period}: {e}")
                continue
        return best_period

    def fit(self):
        self.model = ExponentialSmoothing(
            self.y_train, 
            seasonal_periods=self.seasonal_periods,
            trend=self.trend, 
            seasonal=self.seasonal,
            initialization_method='estimated',
            freq=self.freq
        )
        self.fitted_model = self.model.fit()

    def predict(self):
        if self.fitted_model is None:
            raise ValueError("Model has not been fitted yet.")
        return self.fitted_model.predict(start=0, end=len(self.y) - 1)

    def evaluate(self):
        predictions = self.predict()
        # self.mse = mean_squared_error(self.y_test, predictions)
        
    def _preprocess_dataframe(self):
        for col in self.dataframe.columns:
            if np.issubdtype(self.dataframe[col].dtype, np.datetime64):
                self.dataframe[col + '_year'] = self.dataframe[col].dt.year
                self.dataframe[col + '_month'] = self.dataframe[col].dt.month
                self.dataframe[col + '_day'] = self.dataframe[col].dt.day
                self.dataframe[col + '_hour'] = self.dataframe[col].dt.hour
                self.dataframe[col + '_minute'] = self.dataframe[col].dt.minute
                self.dataframe[col + '_second'] = self.dataframe[col].dt.second
                self.dataframe.drop(columns=[col], inplace=True)
    
    def get_params(self):
        if self.fitted_model is None:
            raise ValueError("Model has not been fitted yet.")
        return self.fitted_model.params
    
    def get_plot_data(self):
        x = self.y_train.index
        X_test = self.y.index
        y = self.y_train - self.shift_constant
        y_pred = self.predict() - self.shift_constant
        return [x, y, X_test, y_pred, f'{self.seasonal.capitalize()} Exponential Smoothing Model', 'DateTime', 'Target']
    

