import customtkinter as ctk
from run.run import Run

class MainPage:
    def __init__(self, pipeline: Run):
        # Create the main application window
        self.app = ctk.CTk()

        # Set the title of the window
        self.app.title("Forecaster")

        # Set the size of the window
        self.app.geometry("600x300")

        # Create a label with the text "Forecaster"
        label = ctk.CTkLabel(self.app, text="Forecaster", font=("Arial", 24))
        label.pack(pady=20)

        # Create buttons with a reusable click handler
        self.create_button("Data Analysis", pipeline.data_analysis, 'Data Analysis')
        # self.create_button("Data Imputation", pipeline.data_imputation)

        # Run the application
        self.app.mainloop()

    def on_button_click(self, callback, tab_name):
        print(f"Executing {callback.__name__}")
        callback(tab_name)

    def create_button(self, text, callback, tab_name):
        button = ctk.CTkButton(self.app, text=text, command=lambda: self.on_button_click(callback, tab_name))
        button.pack(pady=10)

    def add_tab(self, tab_name, callback):
        # Create a new tab
        tab = self.tab_view.add(tab_name)
        tab_label = ctk.CTkLabel(tab, text=f"Contents of {tab_name}")
        tab_label.pack(pady=20)
        # Call the callback function to populate the tab with data
        callback()  # Assuming the callback function handles populating the tab
