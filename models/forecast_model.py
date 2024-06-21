from facade.facade import ForecastingFacade


class ForecastingModel:
    def __init__(self, facade: ForecastingFacade):
        self.facade = facade
        self.data = facade.data
        self.forecast = None
        self.analysis_results = None

    def update_data(self):
        self.data = self.facade.fetch_data()

    def update_forecast(self):
        self.forecast = self.facade.perform_forecast()
    
    def execute_data_analysis(self):
        # Logic to perform analysis
        self.facade.data_analysis()
        self.analysis_results = self.facade.get_analysis_data()
    
    def get_analysis(self):
        return self.analysis_results

