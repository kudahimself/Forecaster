from data_analysis.data_analysis import DataAnalysis
from aggregator.aggregator import Aggregator
from data_imputation.data_imputation import Imputator


class Run():
    '''Facade'''

    def __init__(self, ts_data, freq):
        self.data = Aggregator.aggregate_dataframe(ts_data, freq)
        self.analyse = DataAnalysis(self.data, freq)
        self.impute_data = Imputator(self.data)

    def data_analysis(self, tab):
        self.analyse.analyse_data(tab)

    def imputate_data(self, imp_type, tab):
        self.impute_data.impute(self.data, imp_type, tab)