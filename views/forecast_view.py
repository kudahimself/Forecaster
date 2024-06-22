import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



class ForecastingView:

    def __init__(self):
        self.controller = None
        self.main_page = None
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
        self.main_page = MainPageView(self)
        self.main_page.create_main_page()
    
    def create_data_analysis_page(self):
        self.data_analysis_page = DataAnalysisView(self)
        self.data_analysis_page.create_data_analysis_page()
    
    def display_analysis_results(self, results):
        self.data_analysis_page.display_analysis_results(results)
    

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



class MainPageView:

    def __init__(self, fv: ForecastingView) -> None:
        self.fv = fv
 
    def create_main_page(self):
        tab_name = "Main"
        tab = self.fv.tab_view.add(tab_name)
        # Store the tab in the dictionary
        self.fv.tabs[tab_name] = tab

        # Create a canvas inside the tab
        canvas = ctk.CTkCanvas(tab)
        canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        

        # Create a frame inside the canvas with the same size as the main window
        frame = ctk.CTkFrame(canvas, width=self.fv.app_width, height=self.fv.app_height, fg_color="transparent")
        frame.pack(expand=True)

        # Create a label and place it in the center of the frame
        label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
        label.pack(pady=(100, 20), anchor='n')

        # Add space after the label
        space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
        space_label.pack(pady=20)

        button = ctk.CTkButton(frame, text='Data Analysis', command=lambda: self.fv.create_data_analysis_page())
        button.pack(side=ctk.LEFT, padx=10, pady=10)


class DataAnalysisView:

    def __init__(self, fv: ForecastingView):
        self.fv = fv
        self.tab_name = "Data Analysis"

    def create_data_analysis_page(self):
        
        # Check if tab already exists to avoid duplication
        if self.tab_name not in self.fv.tabs:
            self.fv.add_tab(self.tab_name)
            tab = self.fv.get_tab(self.tab_name)

            # Create a canvas inside the tab
            canvas = ctk.CTkCanvas(tab)
            canvas.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # Create a frame inside the canvas with the same size as the main window
            frame = ctk.CTkFrame(canvas, width=self.fv.app_width, height=self.fv.app_height, fg_color="transparent")
            canvas.create_window((0, 0), window=frame, anchor='nw')

            # Add space after the label
            space_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
            space_label.pack(pady=20)

            # Create a label and place it in the center of the frame
            label = ctk.CTkLabel(frame, text="Welcome To Forecasting", font=("Arial", 24))
            label.pack(pady=(100, 20), anchor='n')

            # Add a button to perform analysis
            perform_analysis_button = ctk.CTkButton(frame, text='Perform Analysis', command=self.fv.controller.perform_analysis)
            perform_analysis_button.pack(side=ctk.LEFT, padx=10, pady=10)
    

    def display_analysis_results(self, results):
        # Access the 'Data Analysis' tab
        tab = self.fv.tabs['Data Analysis']

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


    def display_table(self, frame, table):
        table = CTkTable(master=frame, values=table, header_color="#52AA91", colors=["#FFFFFF", "#DBEEEA"])
        table.pack(expand=True, fill="both", padx=20, pady=20)
    
    def display_text(self, frame, text):
        # Calculate number of lines in text
        num_lines = text.count('\n') + 1
        # Calculate height based on number of lines
        text_height = num_lines * 20  # Adjust multiplier as needed
        # Create CTkTextbox directly on the canvas, not in scrollable_frame
        text_display = ctk.CTkTextbox(frame, wrap='word', height=text_height, activate_scrollbars=False)
        text_display.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        text_display.insert(ctk.END, text + '\n')
    
    def display_graph(self, frame, plot_data):
        x = plot_data[0]
        y = plot_data[1]
        title= plot_data[2]
        xlabel= plot_data[3]
        ylabel = plot_data[4]
        plot_frame = ctk.CTkFrame(frame)
        plot_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(x, y)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Display only the first and last value on the x-axis
        ax.set_xticks([x.iloc[0], x.iloc[-1]])
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
