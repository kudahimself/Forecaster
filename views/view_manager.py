import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from views.abstract_page_view import AbstractPage



class ViewManager:

    def __init__(self):
        self.app_width = 800
        self.app_height = 600
        self.app_background = '#161B25'
        self.app_button_colour = '#2E3C4F'
        self.controller = None
        self.main_page = None
        self.data_analysis_page = None
        self.data_imputation_page = None
        self.app = None
        self.tabs = {}
        self.create_app_structure()


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
        # Create the main application window
        self.app = ctk.CTk()
        self.app.title("Forecaster")
        self.app.geometry(f"{self.app_width}x{self.app_height}")
        self.app._set_appearance_mode('dark')
        self.app.update_idletasks() # Force the window to update and render
        self.app_background = '#161B25'

        # Create a Tab View
        self.tab_view = ctk.CTkTabview(self.app)
        self.tab_view.pack(fill="both", expand=True, pady=20)

    def set_view(self, name, view):
        setattr(self, name, view)
    
    def display_analysis_results(self, results):
        self.data_analysis_page.display_analysis_results(results)
    
    def display_impute_type(self, impute_type):
        self.data_imputation_page.update_page(impute_type)

