from models.forecasting_models.linear_regression import LinearRegressionModel
from models.forecasting_models.exponential_smoothing import ExponentialSmoothingModel

class Trainer:

    def __init__(self, data) -> None:
        self.data = data
        self.models_list = []
        self.models_list.append(LinearRegressionModel(data))
        self.models_list.append(ExponentialSmoothingModel(data))


    def train_models(self):

        for model in self.models_list:
            model.fit()
            model.evaluate()
        return self.models_list

    def show_fitting(self):
        pass
        # for model in self.models_list:
