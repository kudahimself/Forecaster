import customtkinter as ctk


class ForecastingView:

    def __init__(self):
        self.controller = None
        self.tabs = {}
        self.create_app_structure()
        self.create_main_page()
        # self.app.mainloop()
    
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
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.app_width, height=self.app_height, fg_color="transparent")
        frame.pack(expand=True)

        # Create a label and place it in the center of the frame
        label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
        label.pack(pady=(100, 20), anchor='n')

        # Add space after the label
        space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
        space_label.pack(pady=20)

        button = ctk.CTkButton(frame, text='Data Analysis', command=lambda: self.create_data_analysis_page())
        button.pack(side=ctk.LEFT, padx=10, pady=10)
    

    def create_data_analysis_page(self):
        tab_name = "Data Analysis"
        
        # Check if tab already exists to avoid duplication
        if tab_name not in self.tabs:
            self.add_tab(tab_name)
            tab = self.get_tab(tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.app_width, height=self.app_height, fg_color="transparent")
            canvas.create_window((0, 0), window=frame, anchor='nw')

            # Add space after the label
            space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
            space_label.pack(pady=20)

            # Create a label and place it in the center of the frame
            label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
            label.pack(pady=(100, 20), anchor='n')

            # Add a button to perform analysis
            perform_analysis_button = ctk.CTkButton(frame, text='Perform Analysis', command=self.controller.perform_analysis)
            perform_analysis_button.pack(side=ctk.LEFT, padx=10, pady=10)

    def display_analysis_results(self, results):
        # Access the 'Data Analysis' tab
        tab = self.tabs['Data Analysis']

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
        x = results['missing_values']
        text = f'There are {len(x)} values missing'

        # Calculate number of lines in text
        num_lines = text.count('\n') + 1
        # Calculate height based on number of lines
        text_height = num_lines * 20  # Adjust multiplier as needed

        # Create CTkTextbox inside the scrollable frame
        text_display = ctk.CTkTextbox(scrollable_frame, wrap='word', height=text_height, activate_scrollbars=False)
        text_display.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        text_display.insert(ctk.END, text + '\n')

        # Print to verify display of analysis results
        print("Displayed analysis results.")


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

    