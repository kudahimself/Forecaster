from models.forecast_model import ForecastingModel
from views.forecast_view import ForecastingView


class ForecastingController:
    def __init__(self, model: ForecastingModel, view: ForecastingView):
        self.model = model
        self.view = view
        self.view.set_controller(self)
        self.view.show_app()

    def update_view(self):
        self.model.update_data()
        self.view.display_data(self.model.data)
        # self.model.update_forecast()
        # self.view.display_forecast(self.model.forecast)

    def handle_user_input(self):
        user_input = self.view.get_user_input()
        # Process user input and update model and view accordingly

    def perform_analysis(self):
        print("Performing analysis...")
        self.model.execute_data_analysis()
        analysis_data = self.model.get_analysis()
        self.view.display_analysis_results(analysis_data)
    
    def perform_impute_data(self, impute_type):
        print('Replacing Missing Values')
        self.model.execute_data_imputation(impute_type)
        imputated_data = self.model.get_data()
        print(imputated_data)