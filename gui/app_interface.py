import customtkinter as ctk
from run.run import Run
from gui.page_notes import Notes


class ForecasterApp:
    def __init__(self, pipeline: Run):
        self.app_width = 800
        self.app_height = 600
        # Create the main application window
        self.app = ctk.CTk()

        # Set the title of the window
        self.app.title("Forecaster")

        # Set the size of the window
        self.app.geometry(f"{self.app_width}x{self.app_height}") 

        # Force the window to update and render
        self.app.update_idletasks()

        # Create a Tab View
        self.tab_view = ctk.CTkTabview(self.app)
        self.tab_view.pack(fill="both", expand=True, pady=20)

        #Initial tabs
        self.tabs = {}

        # Add the initial tab
        self.add_main_tab(pipeline)


        
        # Run the application
        self.app.mainloop()

    def add_main_tab(self, pipeline: Run):
        tab_name = "Main"
        tab = self.tab_view.add(tab_name)
        # Store the tab in the dictionary
        self.tabs[tab_name] = tab

        # Create a canvas inside the tab
        self.canvas = ctk.CTkCanvas(tab)
        self.canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        # Create a frame inside the canvas with the same size as the main window
        self.frame = ctk.CTkFrame(self.canvas, width=self.app_width, height=self.app_height, fg_color="transparent")
        self.frame.pack(expand=True)

        # Create a label and place it in the center of the frame
        self.label = ctk.CTkLabel(self.frame, text="Welcome to forecasting", font=("Arial", 24))
        self.label.pack(pady=(100, 20), anchor='n')

        # Add space after the label
        space_label = ctk.CTkLabel(self.frame, text="", font=("Arial", 12))
        space_label.pack(pady=20)

        # Create buttons with a reusable click handler
        self.create_button("Data Analysis", pipeline.data_analysis, "Data Analysis")
        self.create_button("Data Imputation", pipeline.imputate_data, "Data Imputation")


    def on_button_click(self, callback, tab_name):
        print(f"Executing {callback.__name__}")
        self.add_tab(tab_name, callback)

    def create_button(self, text, callback, tab_name):
        tab = self.get_tab('Main')
        if tab:
            # Add button to the frame inside the "Main" tab
            button = ctk.CTkButton(self.frame, text=text, command=lambda: self.on_button_click(callback, tab_name))
            button.pack(side=ctk.LEFT, padx=10, pady=10)
        else:
            print(f"Tab 'Main' not found")

    def add_tab(self, tab_name, callback):
        if tab_name not in self.tabs:
            self.tabs[tab_name] = self.tab_view.add(tab_name)
            notes = Notes(self.tabs[tab_name], tab_name)
            callback(notes)
            notes.render()

    def get_tab(self, tab_name):
        return self.tabs.get(tab_name)

