from run.run import Run
import pandas as pd
import numpy as np
from gui.app_interface import ForecasterApp

# Generate the date range
date_range = pd.date_range('2017-01-01 00:00', '2017-01-01 00:59', freq='1Min')
values = np.random.randint(1, 20, date_range.shape[0])
df = pd.DataFrame({'datetime': date_range, 'values': values}).replace(1,None)
df.index = date_range  # set index
df_filtered = df[~df.index.isin(df.between_time('00:12', '00:14').index)]


def main():
    gui = ForecasterApp(Run(df_filtered, '1min'))

    # pipeline.data_analysis()


main()