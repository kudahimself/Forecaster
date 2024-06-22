import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from views.abstract_page_view import AbstractPage



class ForecastingView:

    def __init__(self):
        self.controller = None
        self.main_page = None
        self.tabs = {}
        self.create_app_structure()
        self.create_main_page()
        # self.app.mainloop()
    
    def show_app(self):
        self.app.mainloop()

    def set_controller(self, controller):
        self.controller = controller
    
    def add_tab(self, tab_name):
        if tab_name not in self.tabs:
            self.tabs[tab_name] = self.tab_view.add(tab_name)
    
    def get_tab(self, tab_name):
        return self.tabs.get(tab_name)
        
    def create_app_structure(self):
        self.app_width = 800
        self.app_height = 600
        # Create the main application window
        self.app = ctk.CTk()
        self.app.title("Forecaster")
        self.app.geometry(f"{self.app_width}x{self.app_height}")
        self.app._set_appearance_mode('dark')
        self.app.update_idletasks() # Force the window to update and render

        # Create a Tab View
        self.tab_view = ctk.CTkTabview(self.app)
        self.tab_view.pack(fill="both", expand=True, pady=20)

    
    def create_main_page(self):
        self.main_page = MainPageView(self)
        self.main_page.create_main_page()
    
    def create_data_analysis_page(self):
        self.data_analysis_page = DataAnalysisView(self)
        self.data_analysis_page.create_data_analysis_page()
    
    def display_analysis_results(self, results):
        self.data_analysis_page.display_analysis_results(results)
    
    def create_data_imputation_page(self):
        self.data_imputation_page = DataImputationView(self)
        self.data_imputation_page.create_data_imputation_page()
    

    def display_main_page():
        pass   

    def display_data(self, data):
        # Display the data in the UI
        pass

    def display_forecast(self, forecast):
        # Display the forecast in the UI
        pass

    def get_user_input(self):
        # Get user input from the UI
        pass



class MainPageView(AbstractPage):

    def __init__(self, fv: ForecastingView) -> None:
        self.fv = fv
 
    def create_main_page(self):
        tab_name = "Main"
        tab = self.fv.tab_view.add(tab_name)
        # Store the tab in the dictionary
        self.fv.tabs[tab_name] = tab

        # Create a canvas inside the tab
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.fv.app_width, height=self.fv.app_height, fg_color="transparent")
        frame.pack(expand=True)

        # Create a label and place it in the center of the frame
        label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
        label.pack(pady=(100, 20), anchor='n')

        # Add space after the label
        space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
        space_label.pack(pady=20)

        button = ctk.CTkButton(frame, text='Data Analysis', command=lambda: self.fv.create_data_analysis_page())
        button.pack(side=ctk.LEFT, padx=10, pady=10)

        button = ctk.CTkButton(frame, text='Data Imputation', command=lambda: self.fv.create_data_imputation_page())
        button.pack(side=ctk.LEFT, padx=10, pady=10)



class DataAnalysisView(AbstractPage):

    def __init__(self, fv: ForecastingView):
        self.fv = fv
        self.tab_name = "Data Analysis"

    def create_data_analysis_page(self):
        
        # Check if tab already exists to avoid duplication
        if self.tab_name not in self.fv.tabs:
            self.fv.add_tab(self.tab_name)
            tab = self.fv.get_tab(self.tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.fv.app_width, height=self.fv.app_height, fg_color="transparent")
            canvas.create_window((0, 0), window=frame, anchor='nw')

            # Add space after the label
            space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
            space_label.pack(pady=20)

            # Create a label and place it in the center of the frame
            label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
            label.pack(pady=(100, 20), anchor='n')

            # Add a button to perform analysis
            perform_analysis_button = ctk.CTkButton(frame, text='Perform Analysis', command=self.fv.controller.perform_analysis)
            perform_analysis_button.pack(side=ctk.LEFT, padx=10, pady=10)
    

    def display_analysis_results(self, results):
        # Access the 'Data Analysis' tab
        tab = self.fv.tabs['Data Analysis']

        # Clear existing widgets from the tab
        for widget in tab.winfo_children():
            widget.destroy()

        # Create a canvas to add a scrollbar
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=1)

        # Create a scrollbar
        scrollbar = ctk.CTkScrollbar(tab, command=canvas.yview)
        scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create a frame inside the canvas
        scrollable_frame = ctk.CTkFrame(canvas)
        scrollable_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Display results
        aggregation_table = results['missing_values'][0]
        missing_values = results['missing_values'][1]
        null_values = results['null_values']
        data_facts = results['data_facts']
        plot_data = results['plot_data']

        self.display_table(scrollable_frame, aggregation_table)
        self.display_table(scrollable_frame, missing_values)
        self.display_table(scrollable_frame, null_values)
        self.display_table(scrollable_frame, data_facts)
        self.display_graph(scrollable_frame, plot_data)



class DataImputationView(AbstractPage):

    def __init__(self, fv: ForecastingView):
        self.fv = fv
        self.tab_name = "Data Imputation"

    def create_data_imputation_page(self):
        
        # Check if tab already exists to avoid duplication
        if self.tab_name not in self.fv.tabs:
            self.fv.add_tab(self.tab_name)
            tab = self.fv.get_tab(self.tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.fv.app_width, height=self.fv.app_height, fg_color="transparent")
            canvas.create_window((0, 0), window=frame, anchor='nw')

            self.display_buttons()

    def display_buttons(self):
        # Create a canvas inside the tab
        tab = self.fv.get_tab(self.tab_name)
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.fv.app_width, height=self.fv.app_height, fg_color="transparent")
        frame.pack(expand=True)
        frame.pack(pady=20, padx=60, fill="both", expand=True)

        # Add a label
        label = ctk.CTkLabel(master=frame, text="Select a type of imputation", font=("Arial", 18))
        label.pack(pady=12, padx=10)

        # Add buttons for each imputation type
        buttons = [
            ("Next", 'next'),
            ("Previous", 'previous'),
            ("Mode", 'mode'),
            ("Mean", 'mean'),
            ("Min", 'min'),
            ("Max", 'max'),
            ("Moving Average", 'moving_avg'),
            ("Fixed Value", 'fixed_value')
        ]

        for text, impute_type in buttons:
            button = ctk.CTkButton(master=frame, text=text, command=lambda impute_type=impute_type: self.fv.controller.perform_impute_data(impute_type))
            button.pack(pady=10)

