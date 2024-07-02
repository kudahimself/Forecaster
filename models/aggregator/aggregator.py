import pandas as pd





class Aggregator:

    """
    D - calendar day frequency
    W - weekly frequency
    M - monthly frequency
    Q - quarterly frequency
    Y -yearly frequency
    h - hourly frequency
    min - minutely frequency
    s - secondly frequency
    ms - milliseconds
    us - microseconds
    ns - nanoseconds
    """

    def __init__(self, ts_data, freq):
        self.data = self.aggregate_dataframe(ts_data, freq, 'sum')


    @classmethod
    def aggregate_dataframe(cls, ts_data, time_period='M'):
        """
        Aggregates a dataframe with columns 'datetime' and 'values'.

        Parameters:
        df (pd.DataFrame): The input dataframe with 'datetime' and 'values' columns.
        time_period (str): The time period to group by. (e.g., 'D' for daily, 'M' for monthly)
        agg_func (str): The aggregation function to apply. (e.g., 'sum')

        Returns:
        pd.DataFrame: The aggregated dataframe.
        """
        # Ensure that the 'datetime' column is in datetime format
        ts_data.loc[:, 'datetime'] = pd.to_datetime(ts_data['datetime'])

        # Set the 'datetime' column as the index
        ts_data.set_index('datetime', inplace=True)

        # Aggregate the 'values' column by the specified time period and aggregation function
        aggregated_df = ts_data.resample(time_period).agg({'values': 'sum'})

        # Reset the index to have 'datetime' as a column again
        aggregated_df.reset_index(inplace=True)
        aggregated_df['index'] = aggregated_df['datetime']
        aggregated_df.set_index('index', inplace=True)

        return aggregated_df