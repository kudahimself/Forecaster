import pandas as pd
from statistics import mode
import customtkinter as ctk
import numpy as np


class Imputator:

    def __init__(self, ts_data) -> None:
        self.data = ts_data.copy()
        self.original = ts_data.copy()

    def impute_data(self, imp_type, fixed_value=None):
        ts_data = self.original
        match imp_type:
            case 'original':
                result = self.impute_original(ts_data)
            
            case 'interpolate':
                result = self.impute_interpolate(ts_data)

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
    
    def impute_original(self, ts_data):
        return self.original
    
    def impute_next(self, ts_data):
        ts_data['values'] = ts_data['values'].replace(0, np.nan).bfill()
        return ts_data

    def impute_previous(self, ts_data):
        ts_data['values'] = ts_data['values'].replace(0, np.nan).ffill()
        return ts_data

    def impute_mode(self, ts_data):
        mode_value = ts_data['values'].mode()[0]
        ts_data['values'] = ts_data['values'].replace(0, np.nan).fillna(mode_value)
        return ts_data

    def impute_mean(self, ts_data):
        mean_value = ts_data['values'].mean()
        ts_data['values'] = ts_data['values'].replace(0, np.nan).fillna(mean_value)
        return ts_data

    def impute_min(self, ts_data):
        min_value = ts_data['values'].min()
        ts_data['values'] = ts_data['values'].replace(0, np.nan).fillna(min_value)
        return ts_data

    def impute_max(self, ts_data):
        max_value = ts_data['values'].max()
        ts_data['values'] = ts_data['values'].replace(0, np.nan).fillna(max_value)
        return ts_data

    def impute_mva(self, ts_data, window=3):
        rolling_mean = ts_data['values'].rolling(window, min_periods=1).mean()
        ts_data['values'] = ts_data['values'].replace(0, np.nan).fillna(rolling_mean)
        return ts_data

    def impute_fv(self, ts_data, fixed_value):
        ts_data['values'] = ts_data['values'].replace(0, np.nan).fillna(fixed_value)
        return ts_data
    
    def impute_interpolate(self, ts_data):
        ts_data = ts_data.copy()  # Avoid modifying the original DataFrame
        ts_data['values'] = ts_data['values'].replace(0, np.nan)
        ts_data['values'] = ts_data['values'].interpolate(method='linear', limit_direction='forward', axis=0)
        return ts_data
    
    def get_results(self):
        return self.data.bfill()
    
    def render(self, tab):
        # Create a canvas inside the tab
        self.canvas = ctk.CTkCanvas(tab)
        self.canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        # Create a frame inside the canvas with the same size as the main window
        self.frame = ctk.CTkFrame(self.canvas, width=self.app_width, height=self.app_height, fg_color="transparent")
        self.frame.pack(expand=True)
        self.frame.pack(pady=20, padx=60, fill="both", expand=True)

        # Add a label
        label = ctk.CTkLabel(master=self.frame, text="Select a type of imputation", font=("Arial", 18))
        label.pack(pady=12, padx=10)

        # Add buttons for each imputation type
        buttons = [
            ("Next", 'next'),
            ("Previous", 'previous'),
            ("Mode", 'mode'),
            ("Mean", 'mean'),
            ("Min", 'min'),
            ("Max", 'max'),
            ("Moving Average", 'moving_avg'),
            ("Fixed Value", 'fixed_value')
        ]

        for text, impute_type in buttons:
            button = ctk.CTkButton(master=self.frame, text=text, command=lambda impute_type=impute_type: self.impute(impute_type))
            button.pack(pady=10)

