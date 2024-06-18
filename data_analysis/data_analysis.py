from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from tabulate import tabulate
from terminalplot import plot as tp


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
    
    def analyse_data(self):
        print('Starting Analyis...')
        self.missing_values()
        self.null_values()
        self.data_facts()
        self.plot_data()
        
    
    
    @staticmethod
    def answer_input(ans, prompt, answer_msg):
            answer = None
            while not answer:
                answer = input(prompt)
                if answer.lower() == 'y':
                    [print(x) for x in ans]
                elif answer.lower() == 'n':
                    answer = True
                else:
                    DataAnalysis.answer_input(ans, prompt, answer_msg)

    
    def missing_values(self):
        reference_datetime_range = self.create_comparison_index()
        checking_dataset = self.data.copy().index

        
        reference_set = set(reference_datetime_range)
        checking_set = set(checking_dataset)
        
        # Elements in reference_set but not in checking_set (difference)
        only_in_reference = reference_set - checking_set
        if only_in_reference:
            print(f'{len(only_in_reference)} missing values have been identified in this dataset\n')
            DataAnalysis.answer_input(only_in_reference,
                                      'Do you want to see the values. Type "Y" or "N": ',
                                      f'There are {len(only_in_reference)} values missing')                    
    

    def null_values(self):
        value_set = tuple(self.data['values'])
        null_values = sum(1 for item in value_set if item is None or item == 0)
        percentage = round(100*null_values/len(value_set), 2)

        table = [
            ["Null and Zero Count", null_values],
            ["Percentage of null and zero values", f'{percentage}%']]
        print(tabulate(table, headers=["Statistic", "Value"], tablefmt="grid"))
              

    def create_comparison_index(self):
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
        print(tabulate(table, headers=["Aggregation"], tablefmt="grid"))

        return datetime_range


    def data_facts(self):
        
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
        print(tabulate(table, headers=["Statistic", "Value"], tablefmt="grid"))
    

    def plot_data(self):
        df = self.data
        df['datetime'] = pd.to_datetime(df['datetime'])

        x = range(100)
        y = [i**2 for i in x]
        tp(y, x)




    