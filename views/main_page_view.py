from views.view_manager import ViewManager
import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from views.abstract_page_view import AbstractPage



class MainPageView(AbstractPage):

    def __init__(self, vm: ViewManager) -> None:
        self.tab_name = 'Main'
        self.view_name = 'main_page'
        self.vm = vm
        self.set_main_page()


    def set_main_page(self):
        self.vm.set_view(self.tab_name, self)
        self.create_main_page()
 
    def create_main_page(self):

        tab = self.vm.tab_view.add(self.tab_name)
        # Store the tab in the dictionary
        self.vm.tabs[self.tab_name] = tab

        # Create a canvas inside the tab
        canvas = ctk.CTkCanvas(tab, bg=self.vm.app_background)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        
        # Create a label and place it in the center of the frame
        label = ctk.CTkLabel(canvas, text="Welcome To Forecasting", font=("Arial", 24), text_color="white")
        label.pack(pady=100, anchor='n')

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.vm.app_width, height=self.vm.app_height-300, fg_color="transparent")
        frame.pack(expand=True, anchor='n')

        button = ctk.CTkButton(frame,
                               text='Data Analysis',
                               command=lambda: self.vm.data_analysis_page.create_data_analysis_page(),
                               fg_color=self.vm.app_button_colour)
        button.pack(side=ctk.LEFT, padx=10, pady=10, anchor='n')

        button = ctk.CTkButton(frame, text='Data Imputation',
                               command=lambda: self.vm.data_imputation_page.create_data_imputation_page(),
                               fg_color=self.vm.app_button_colour)
        button.pack(side=ctk.LEFT, padx=10, pady=10, anchor='n')

