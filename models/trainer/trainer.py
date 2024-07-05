from models.forecasting_models.linear_regression import LinearRegressionModel
from models.forecasting_models.exponential_smoothing import ExponentialSmoothingModel
from models.trainer.model_selector import ModelSelector



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

        self.best_models()
        return self.models_list

    def best_models(self):
        ms = ModelSelector(self.models_list)
        return ms.get_best_model()
    
