from data_analysis.data_analysis import DataAnalysis
from aggregator.aggregator import Aggregator
from data_imputation.data_imputation import Imputator


class ForecastingFacade:
    '''Facade'''

    def __init__(self, ts_data, freq):
        self.data = Aggregator.aggregate_dataframe(ts_data, freq)
        self.freq = freq
        self.analysis = None
        # self.imputate_data
    
    def get_analysis_data(self):
        return self.analysis

    def data_analysis(self):
        self.analyse = DataAnalysis(self.data, self.freq)
        self.analyse.analyse_data()
        self.analysis = self.analyse.get_results()

    def imputate_data(self, tab, app_geometry):
        self.impute_data = Imputator(self.data, tab, app_geometry)
        self.impute_data.render(tab)
        self.data = self.impute_data.data

    def fetch_data(self):
        # Simplified interface for fetching data
        return self.data

    def process_data(self):
        # Simplified interface for processing data
        pass

    def perform_forecast(self):
        # Simplified interface for performing forecast
        pass


