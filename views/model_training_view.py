from views.view_manager import ViewManager
import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from views.abstract_page_view import AbstractPage

class ModelTrainingView(AbstractPage):

    def __init__(self, vm: ViewManager) -> None:
        self.vm = vm
        self.view_name = 'model_training_page'
        self.tab_name = "Model Trainer"
        self.vm.set_view(self.view_name, self)

    def create_model_training_page(self, reset=False):
        
        # Check if tab already exists to avoid duplication
        if self.tab_name not in self.vm.tabs or reset:
            if self.tab_name not in self.vm.tabs:
                self.vm.add_tab(self.tab_name)
            tab = self.vm.get_tab(self.tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab, bg=self.vm.app_background)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
            
            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.vm.app_width, height=self.vm.app_height, fg_color="transparent")
            frame.pack(expand=True)
            label = ctk.CTkLabel(frame, text="Model Trainer", font=("Arial", 24), text_color='white')
            label.pack(pady=10, side=ctk.TOP)

            # Add a button to perform analysis
            perform_analysis_button = ctk.CTkButton(frame, text='Train Models',
                                                    command=self.vm.controller.perform_model_training,
                                                    fg_color=self.vm.app_button_colour)
            perform_analysis_button.pack(padx=10, pady=10, anchor='n')
    
    def display_model_results(self, trained_models, best_model):
        # Access the 'Data Analysis' tab
        tab = self.vm.tabs[self.tab_name]

        # Clear existing widgets from the tab
        for widget in tab.winfo_children():
            widget.destroy()

        # Create a canvas to add a scrollbar
        canvas = ctk.CTkCanvas(tab, bg=self.vm.app_background)
        canvas.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=1)

        # Create a frame inside the canvas
        scrollable_frame = ctk.CTkScrollableFrame(canvas, fg_color=self.vm.app_background)
        scrollable_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)

        reset_button = ctk.CTkButton(master=scrollable_frame, text='Reset Models',
                                     command=self.reset_page,
                                     fg_color=self.vm.app_button_colour)
        reset_button.pack(pady=10, padx=10, anchor='n')

        self.display_table(scrollable_frame, best_model)
        for model in trained_models:
            self.display_model(scrollable_frame, model.get_plot_data())
    
    def reset_page(self):
        tab = self.vm.tabs[self.tab_name]

        for widget in tab.winfo_children():
            widget.destroy()
        
        self.create_model_training_page(True)
    
