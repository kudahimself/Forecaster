import customtkinter as ctk


class ForecastingView:

    def __init__(self):
        self.tabs = {}
        self.create_app_structure()
        self.create_main_page()
        self.app.mainloop()
        # self.display_main_page()
        

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
        self.label = ctk.CTkLabel(self.frame, text="Welcome To Forecasting", font=("Arial", 24))
        self.label.pack(pady=(100, 20), anchor='n')

        # Add space after the label
        space_label = ctk.CTkLabel(self.frame, text="", font=("Arial", 12))
        space_label.pack(pady=20)

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
    