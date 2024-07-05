import numpy as np

class ModelSelector:

    def __init__(self, trained_models):
        self.trained_models = trained_models
        self.best_model = None
        self.mse = np.inf
    
    def get_best_model(self):
        for model in self.trained_models:
            
            if  self.mse > model.get_model_score().get('mse'):
                self.best_model = model.get_model_score().get('model_name')
                self.mse = model.get_model_score().get('mse')
        return [['Best model'], [f'Model Name: {self.best_model}'], [f'mse: {self.mse}']]

        

