import customtkinter as ctk
from run.run import Run
from graphical_user_interface.module_notes import Notes


class MainPage:
    def __init__(self, pipeline: Run):
        # Create the main application window
        self.app = ctk.CTk()

        # Set the title of the window
        self.app.title("Forecaster")

        # Set the size of the window
        self.app.geometry("800x600")

        # Create a Tab View
        self.tab_view = ctk.CTkTabview(self.app)
        self.tab_view.pack(fill="both", expand=True, pady=20)

        # Add the initial tab
        self.add_initial_tab()

        # Create buttons with a reusable click handler
        self.create_button("Data Analysis", pipeline.data_analysis, "Data Analysis Tab")
        # self.create_button("Data Imputation", pipeline.data_imputation, "Data Imputation Tab")

        # Run the application
        self.app.mainloop()

    def add_initial_tab(self):
        tab_name = "Main"
        tab = self.tab_view.add(tab_name)
        notes = Notes(tab, tab_name)
        notes.add_text("Welcome to the Forecaster application!")
        notes.render()

    def on_button_click(self, callback, tab_name):
        print(f"Executing {callback.__name__}")
        self.add_tab(tab_name, callback)

    def create_button(self, text, callback, tab_name):
        button = ctk.CTkButton(self.app, text=text, command=lambda: self.on_button_click(callback, tab_name))
        button.pack(pady=10)

    def add_tab(self, tab_name, callback):
        tab = self.tab_view.add(tab_name)
        notes = Notes(tab, tab_name)
        callback(notes)
        notes.render()
