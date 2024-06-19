from data_analysis.data_analysis import DataAnalysis
from aggregator.aggregator import Aggregator

class Run():
    '''Facade'''

    def __init__(self, ts_data, freq):
        self.data = Aggregator.aggregate_dataframe(ts_data, freq)
        self.analyse = DataAnalysis(self.data, freq)


    def set_tab_name(self, tab, tab_name):
        setattr(self, tab, tab_name)

    def data_analysis(self, tab):
        self.analyse.analyse_data(tab)