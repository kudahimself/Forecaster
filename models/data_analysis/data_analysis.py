from abc import ABC, abstractmethod
import pandas as pd
from models.data_analysis.autocorrelation import AutoCorrelation



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
        missing_values = self.missing_values()
        null_values = self.null_values()
        data_facts = self.data_facts()
        plot_data = self.plot_data()
        return {'missing_values': missing_values,
                'null_values': null_values,
                'data_facts': data_facts,
                'plot_data': plot_data}

    def missing_values(self):
        reference_datetime_range, aggregation_table = self.create_comparison_index()
        checking_dataset = self.data.copy().index

        
        reference_set = set(reference_datetime_range)
        checking_set = set(checking_dataset)
        
        # Elements in reference_set but not in checking_set (difference)
        only_in_reference = reference_set - checking_set
        if only_in_reference:
            missing_values = [['Missing Values'], len(only_in_reference)]
        else:
            missing_values = [['Missing Values'], ['None']]                    
        return [aggregation_table, missing_values]

    def null_values(self):
        value_set = tuple(self.data['values'])
        null_values = sum(1 for item in value_set if item is None or item == 0)
        percentage = round(100*null_values/len(value_set), 2)

        table = [
            ["Null and Zero Count", null_values],
            ["Percentage of null and zero values", f'{percentage}%']]
        # app_i.add_table(table, headers=["Statistic", "Value"])
              
        return table

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
        table = [['Aggregation'], [self.freq]]
    
        return datetime_range, table


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
            ["Min Value", round(min_value, 2)],
            ["Max Value", round(max_value, 2)],
            ["Mean Value", round(mean_value, 2)],
            ["Count", count],
            ["Standard Deviation", std_dev],
            ["Standard Deviation over Mean", round(std_dev / mean_value, 2) if mean_value != 0 else 0]
        ]
        
        return table
    
    
    def plot_data(self):
        df = self.data
        x = df['datetime']
        y = df['values']
        title = f'Aggregated Time Series Data to {self.freq}'
        x_label = 'Time'
        y_label = 'Values'
        z = AutoCorrelation.calculate_ac(df['values'])
        return [x, y, title, x_label, y_label, z]
