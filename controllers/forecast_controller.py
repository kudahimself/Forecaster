from models.forecast_model import ForecastingModel
from views.forecast_view import ForecastingView


class ForecastingController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def update_view(self):
        self.model.update_data()
        self.view.display_data(self.model.data)
        # self.model.update_forecast()
        # self.view.display_forecast(self.model.forecast)

    def handle_user_input(self):
        user_input = self.view.get_user_input()
        # Process user input and update model and view accordingly
