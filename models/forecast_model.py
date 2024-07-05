from models.facade.facade import ForecastingFacade


class ForecastingModel:
    def __init__(self, facade: ForecastingFacade):
        self.facade = facade
        self.data = facade.data
        self.freq = facade.freq
        self.original_data = facade.data
        self.forecast = None
        self.analysis_results = None
        self.trained_models = None

    def update_data(self):
        self.data = self.facade.fetch_data()

    def update_forecast(self):
        self.forecast = self.facade.perform_forecast()
    
    def execute_data_analysis(self):
        # Logic to perform analysis
        self.analysis_results = self.facade.data_analysis(self.get_data())
    
    def get_analysis(self):
        return self.analysis_results
    
    def execute_data_imputation(self, impute_type):
        # Logic to impute data
        self.data = self.facade.data_imputation(self.original_data, impute_type)
    
    def execute_model_training(self):
        self.trained_models = self.facade.model_training(self.data, self.freq)

    def get_data(self):
        return self.data
    
    def get_trained_models(self):
        return self.trained_models
