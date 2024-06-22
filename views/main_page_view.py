import customtkinter as ctk
from forecast_view import ForecastingView


class MainPageView():
    
    def create_main_page(self, app: ForecastingView):
        tab_name = "Main"
        tab = app.tab_view.add(tab_name)
        # Store the tab in the dictionary
        app.tabs[tab_name] = tab

        # Create a canvas inside the tab
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.app_width, height=self.app_height, fg_color="transparent")
        frame.pack(expand=True)

        # Create a label and place it in the center of the frame
        label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
        label.pack(pady=(100, 20), anchor='n')

        # Add space after the label
        space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
        space_label.pack(pady=20)

        button = ctk.CTkButton(frame, text='Data Analysis', command=lambda: self.create_data_analysis_page())
        button.pack(side=ctk.LEFT, padx=10, pady=10)