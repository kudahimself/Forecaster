from facade.facade import ForecastingFacade
from models.forecast_model import ForecastingModel
from views.forecast_view import ForecastingView
from controllers.forecast_controller import ForecastingController
import pandas as pd
import numpy as np

# Generate the date range
date_range = pd.date_range('2017-01-01 00:00', '2017-01-01 00:59', freq='1Min')
values = np.random.randint(1, 20, date_range.shape[0])
df = pd.DataFrame({'datetime': date_range, 'values': values}).replace(1,None)
df.index = date_range  # set index
df_filtered = df[~df.index.isin(df.between_time('00:12', '00:14').index)]


def main():

    facade = ForecastingFacade(df_filtered, '1min')
    model = ForecastingModel(facade)
    view = ForecastingView()
    controller = ForecastingController(model, view)

    # Run the application
    controller.update_view()
    # Handle user interactions in a loop or event-driven manner


main()