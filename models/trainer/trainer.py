from models.forecasting_models.linear_regression import LinearRegressionModel
from models.forecasting_models.exponential_smoothing import ExponentialSmoothingModel

class Trainer:

    def __init__(self, data, freq) -> None:
        self.data = data
        self.freq = freq
        self.models_list = []
        self.models_list.append(LinearRegressionModel(data))
        self.models_list.append(ExponentialSmoothingModel(data, freq))
        self.models_list.append(ExponentialSmoothingModel(data, freq, seasonal='multiplicative'))

    def train_models(self):

        for model in self.models_list:
            model.fit()
            model.evaluate()
        return self.models_list

    def show_fitting(self):
        pass
        # for model in self.models_list:
