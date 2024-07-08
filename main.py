from models.facade.facade import ForecastingFacade
from models.forecast_model import ForecastingModel
from views.view_manager import ViewManager
from controllers.forecast_controller import ForecastingController
import pandas as pd
import numpy as np
from views.main_page_view import MainPageView
from views.data_analysis_view import DataAnalysisView
from views.data_imputation_view import DataImputationView
from views.model_training_view import ModelTrainingView

#############
# # Generate the date range
# date_range = pd.date_range('2017-01-01 00:00', '2017-01-01 02:59', freq='1Min')
# values = np.random.randint(1, 20, date_range.shape[0])
# df = pd.DataFrame({'datetime': date_range, 'values': values}).replace(1,None)
# df.index = date_range  # set index
# df_filtered = df[~df.index.isin(df.between_time('00:12', '00:14').index)]

#####################
# Generate the date range
date_range = pd.date_range('2017-01-01 00:00', '2017-01-01 1:59', freq='1Min')
sine_values = np.sin(np.linspace(0, 30 * np.pi, date_range.shape[0]))
random_ints = np.random.normal(loc=0, scale=1, size=date_range.shape[0])
# Clip the random values to be within the range [-0.05, 0.05]
random_ints = np.clip(random_ints, -0.01, 0.01)
values = sine_values + random_ints

# Create DataFrame
df = pd.DataFrame({'datetime': date_range, 'values': values})

# Set index
df.index = date_range

# # Filter out specific time intervals
# df_filtered = df[~df.index.isin(df.between_time('00:12', '00:14').index)]

def main():

    facade = ForecastingFacade(df, '1min')
    model = ForecastingModel(facade)
    view = ViewManager()
    controller = ForecastingController(model, view)

    # Initiliasing App UI
    main_page = MainPageView(view)
    data_analysis_page = DataAnalysisView(view)
    data_imputation_page = DataImputationView(view)
    model_training_page = ModelTrainingView(view)


    controller.view.show_app()

if __name__ == "__main__":
    main()