from views.view_manager import ViewManager
import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from views.abstract_page_view import AbstractPage

class DataAnalysisView(AbstractPage):

    def __init__(self, vm: ViewManager) -> None:
        self.vm = vm
        self.view_name = 'data_analysis_page'
        self.tab_name = "Data Analysis"
        self.vm.set_view(self.view_name, self)

    def create_data_analysis_page(self):
        
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

            # Add space after the label
            space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
            space_label.pack(pady=20)

            # Create a label and place it in the center of the frame
            label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
            label.pack(pady=(100, 20), anchor='n')

            # Add a button to perform analysis
            perform_analysis_button = ctk.CTkButton(frame, text='Perform Analysis', command=self.vm.controller.perform_analysis)
            perform_analysis_button.pack(side=ctk.LEFT, padx=10, pady=10)
    
    def display_analysis_results(self, results):
        # Access the 'Data Analysis' tab
        tab = self.vm.tabs['Data Analysis']

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