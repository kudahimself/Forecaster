from facade.facade import ForecastingFacade


class ForecastingModel:
    def __init__(self, facade: ForecastingFacade):
        self.facade = facade
        self.data = facade.data
        self.forecast = None

    def update_data(self):
        self.data = self.facade.fetch_data()

    def update_forecast(self):
        self.forecast = self.facade.perform_forecast()
