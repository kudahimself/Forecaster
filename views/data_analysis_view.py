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

    def create_data_analysis_page(self, reset=False):
        
        # Check if tab already exists to avoid duplication
        if self.tab_name not in self.vm.tabs or reset:
            if self.tab_name not in self.vm.tabs:
                self.vm.add_tab(self.tab_name)
            tab = self.vm.get_tab(self.tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
            

            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.vm.app_width, height=self.vm.app_height, fg_color="transparent")
            frame.pack(expand=True)
            label = ctk.CTkLabel(frame, text="Data Analysis", font=("Arial", 24))
            label.pack(pady=10, side=ctk.TOP)

            # Add a button to perform analysis
            perform_analysis_button = ctk.CTkButton(frame, text='Perform Analysis', command=self.vm.controller.perform_analysis)
            perform_analysis_button.pack(padx=10, pady=10, anchor='n')
    
    def display_analysis_results(self, results):
        # Access the 'Data Analysis' tab
        tab = self.vm.tabs[self.tab_name]

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

        reset_button = ctk.CTkButton(master=scrollable_frame, text='Reset Analysis',
                                     command=self.reset_page)
        reset_button.pack(pady=10, padx=10, anchor='n')

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
        self.display_line_graph(scrollable_frame, plot_data)
        self.display_histogram(scrollable_frame, plot_data)
        label2 = ctk.CTkLabel(scrollable_frame, text="", font=("Arial", 24))
        label2.pack(pady=100, side=ctk.TOP)
    
    def reset_page(self):
        tab = self.vm.tabs[self.tab_name]

        for widget in tab.winfo_children():
            widget.destroy()
        
        self.create_data_analysis_page(True)