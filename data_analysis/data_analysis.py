from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from tabulate import tabulate
from graphical_user_interface.module_notes import Notes
import customtkinter as ctk
import tkinter as tk


class DataAnalysisInterface(ABC):


    @abstractmethod
    def analyse_data(self):
        """
        This method runs the data analysis and returns information about the time series data
        """
        pass


class DataAnalysis(DataAnalysisInterface):

    @staticmethod
    def initialise_ts_data(ts_data):
        # ts_data['date'] = pd.to_datetime(ts_data['date'])
        # ts_data.index = ts_data['date']  # set index 
        # ts_data.sort_values(by=['date'], inplace=True, ascending=True)
        return ts_data


    def __init__(self, ts_data: pd.DataFrame, freq: str):
        """
        This method initialises the DataAnalysis object instance
        """

        self.data = DataAnalysis.initialise_ts_data(ts_data)
        self.freq = freq
    
    def analyse_data(self, tab):
        self.missing_values(tab)
        self.null_values(tab)
        self.data_facts(tab)
        self.plot_data(tab)


    def missing_values(self, app_i: Notes):
        reference_datetime_range = self.create_comparison_index(app_i)
        checking_dataset = self.data.copy().index

        
        reference_set = set(reference_datetime_range)
        checking_set = set(checking_dataset)
        
        # Elements in reference_set but not in checking_set (difference)
        only_in_reference = reference_set - checking_set
        if only_in_reference:
            app_i.add_text(f'There are {len(only_in_reference)} values missing')                    
    

    def null_values(self, app_i: Notes):
        value_set = tuple(self.data['values'])
        null_values = sum(1 for item in value_set if item is None or item == 0)
        percentage = round(100*null_values/len(value_set), 2)

        table = [
            ["Null and Zero Count", null_values],
            ["Percentage of null and zero values", f'{percentage}%']]
        app_i.add_table(table, headers=["Statistic", "Value"])
              

    def create_comparison_index(self, app_i: Notes):

        """
        This function creates a DatetimeIndex based on provided min and max dates,
        and a desired frequency.

        Args:
            min_date (str): String representation of the minimum date in YYYY-MM-DD format.
            max_date (str): String representation of the maximum date in YYYY-MM-DD format.
            freq (str): The desired frequency for the DatetimeIndex (e.g., 'D' for daily, 'H' for hourly).

        Returns:
            pd.DatetimeIndex: The created DatetimeIndex.
        """

        min_date = self.data['datetime'].min()  # Ensure proper date format
        max_date = self.data['datetime'].max()

        # Create the DatetimeIndex with the specified frequency
        datetime_range = pd.date_range(start=min_date, end=max_date, freq=self.freq)
        table = [
            [self.freq]]
        
        app_i.add_table(table, headers=["Aggregation"])

        return datetime_range


    def data_facts(self, app_i: Notes):
        
        min_date = self.data['datetime'].min()  # Ensure proper date format
        max_date = self.data['datetime'].max()

        min_value = self.data['values'].min()  
        max_value = self.data['values'].max()
        mean_value = round(self.data['values'].mean(), 2)

        count = self.data.shape[0]
        
        std_dev = round(self.data['values'].std(), 2)

        # Create a table
        table = [
            ["Min Date", min_date],
            ["Max Date", max_date],
            ["Min Value", min_value],
            ["Max Value", max_value],
            ["Mean Value", mean_value],
            ["Count", count],
            ["Standard Deviation", std_dev],
            ["Standard Deviation over Mean", round(std_dev/mean_value, 2)]
        ]
        
        # Print the table
        app_i.add_table(table, headers=["Statistics", "Value"])
    
    
    def plot_data(self, app_i: Notes):
        df = self.data
        x = df['datetime']
        y = df['values']
        title = f'Aggregated Time Series Data to {self.freq}'
        x_label = 'Time'
        y_label = 'Values'
        app_i.plot_graph(x, y, title, x_label, y_label)
