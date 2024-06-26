from data_analysis.data_analysis import DataAnalysis
from aggregator.aggregator import Aggregator
from data_imputation.data_imputation import Imputator


class ForecastingFacade:
    '''Facade'''

    def __init__(self, ts_data, freq):
        self.data = Aggregator.aggregate_dataframe(ts_data, freq)
        self.freq = freq
        # self.analysis = None
        # self.imputated_data = None

    def data_analysis(self, data):
        self.analyse = DataAnalysis(data, self.freq)
        analysis_data = self.analyse.analyse_data()
        return analysis_data

    def data_imputation(self, data, impute_type):
        self.impute = Imputator(data)
        impute_data = self.impute.impute_data(impute_type)
        return impute_data

    def fetch_data(self):
        # Simplified interface for fetching data
        return self.data

    def process_data(self):
        # Simplified interface for processing data
        pass

    def perform_forecast(self):
        # Simplified interface for performing forecast
        pass


