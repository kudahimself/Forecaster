import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from views.abstract_page_view import AbstractPage
from views.view_manager import ViewManager



class DataImputationView(AbstractPage):

    def __init__(self, vm: ViewManager):
        self.vm = vm
        self.tab_name = "Data Imputation"
        self.view_name = 'data_imputation_page'
        self.vm.set_view(self.view_name, self)
        self.label_impute_type = None

    def create_data_imputation_page(self):
        
        # Check if tab already exists to avoid duplication
        if self.tab_name not in self.vm.tabs:
            self.vm.add_tab(self.tab_name)
            tab = self.vm.get_tab(self.tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.vm.app_width, height=self.vm.app_height, fg_color="transparent")
            canvas.create_window((0, 0), window=frame, anchor='nw')

            self.display_buttons()

    def display_buttons(self):
        # Create a canvas inside the tab
        tab = self.vm.get_tab(self.tab_name)
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.vm.app_width, height=self.vm.app_height, fg_color="transparent")
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Add a label
        self.label_impute_type = ctk.CTkLabel(master=frame, text="Imputation Type: None", font=("Arial", 18), anchor='n')
        self.label_impute_type.pack(side=ctk.TOP, pady=(20, 0), padx=10, anchor=ctk.N)

        # Add a label
        label = ctk.CTkLabel(master=frame, text="Select a type of imputation", font=("Arial", 18))
        label.pack(pady=12, padx=10,  anchor="n")

        # Add buttons for each imputation type
        buttons = [
            ("Original", "original"),
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
            button = ctk.CTkButton(master=frame, text=text, command=lambda impute_type=impute_type: self.vm.controller.perform_impute_data(impute_type))
            button.pack(pady=10)
        
        

    def update_page(self, impute_type):
        self.label_impute_type.configure(text=f'Imputation Type: {impute_type}')

    
