from models.facade.facade import ForecastingFacade
from models.forecast_model import ForecastingModel
from views.view_manager import ViewManager
from controllers.forecast_controller import ForecastingController
import pandas as pd
import numpy as np
from views.main_page_view import MainPageView
from views.data_analysis_view import DataAnalysisView
from views.data_imputation_view import DataImputationView


# Generate the date range
date_range = pd.date_range('2017-01-01 00:00', '2017-01-01 00:59', freq='1Min')
values = np.random.randint(1, 20, date_range.shape[0])
df = pd.DataFrame({'datetime': date_range, 'values': values}).replace(1,None)
df.index = date_range  # set index
df_filtered = df[~df.index.isin(df.between_time('00:12', '00:14').index)]


def main():

    facade = ForecastingFacade(df_filtered, '1min')
    model = ForecastingModel(facade)
    view = ViewManager()
    controller = ForecastingController(model, view)

    main_page = MainPageView(view)
    data_analysis_page = DataAnalysisView(view)
    data_imputation_page = DataImputationView(view)
    view.show_app()
    
    
    
    

    # Run the application
    controller.update_view()
    # Handle user interactions in a loop or event-driven manner


main()