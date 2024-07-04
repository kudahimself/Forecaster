import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np



class LinearRegressionModel:
    def __init__(self, dataframe, target_column='values'):
        self.dataframe = dataframe.fillna(0).copy()
        self.target_column = target_column
        self.model = LinearRegression()
        
        # Preprocess the dataframe to handle datetime columns
        self._preprocess_dataframe()
        
        self.X = self.dataframe.drop(columns=[self.target_column])
        self.y = self.dataframe[self.target_column]
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)
        self.mse = None
        self.r2 = None

    def fit(self):
        self.model.fit(self.X_train, self.y_train)

    def predict(self, X):
        return self.model.predict(X)

    def evaluate(self):
        predictions = self.model.predict(self.X_test)
        self.mse = mean_squared_error(self.y_test, predictions)
        self.r2 = r2_score(self.y_test, predictions)

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

    def get_coefficients(self):
        return self.model.coef_

    def get_intercept(self):
        return self.model.intercept_
    
    def get_plot_data(self):
        x = self.X_train.index
        X_test = self.X_test.index
        y = self.y_train
        y_pred = self.model.predict(self.X_test)
        return [x, y, X_test, y_pred, 'Linear Regression Model', 'DateTime', 'Target']
