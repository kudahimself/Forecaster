from models.forecast_model import ForecastingModel
from views.view_manager import ViewManager



class ForecastingController:
    def __init__(self, model: ForecastingModel, view: ViewManager):
        self.model = model
        self.view = view
        self.view.set_controller(self)

    def handle_user_input(self):
        user_input = self.view.get_user_input()
        # Process user input and update model and view accordingly

    def perform_analysis(self):
        # print("Performing analysis...")
        self.model.execute_data_analysis()
        analysis_data = self.model.get_analysis()
        self.view.display_analysis_results(analysis_data)
    
    def perform_impute_data(self, impute_type):
        # print('Replacing Missing Values')
        self.model.execute_data_imputation(impute_type)
        self.view.display_impute_type(impute_type)
        imputated_data = self.model.get_data()
    
    def perform_model_training(self):
        # print('Training Models')
        self.model.execute_model_training()
        trained_models = self.model.get_trained_models()
        self.view.display_model_results(trained_models)
        
    