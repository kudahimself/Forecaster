import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from CTkTable import *
from tkinter import Button, Entry


class CustomPrompt(ctk.CTkFrame):
    def __init__(self, master=None, message="", prompt=""):
        super().__init__(master)
        
        # Create widgets for the prompt
        self.message_label = ctk.CTkLabel(self, text=message)
        self.message_label.pack(side=ctk.TOP, padx=10, pady=5)
        
        self.entry = Entry(self)
        self.entry.pack(side=ctk.TOP, padx=10, pady=5)
        
        self.submit_button = Button(self, text="Submit", command=self.submit_prompt)
        self.submit_button.pack(side=ctk.TOP, padx=10, pady=5)
        
        # Store prompt message for future reference if needed
        self.prompt_message = prompt

    def submit_prompt(self):
        # Example function to handle submission of prompt
        user_input = self.entry.get()
        # You can process the user input as needed
        print(f"User entered: {user_input}")


class Notes:
    def __init__(self, root, title):
        self.root = root
        # self.root.geometry("856x645")
        # self.root.title(title)

        self.root._set_appearance_mode("dark")

        # Create a canvas to add a scrollbar
        self.canvas = ctk.CTkCanvas(self.root)
        self.canvas.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=1)

        # Create a scrollbar
        self.scrollbar = ctk.CTkScrollbar(self.root, command=self.canvas.yview)
        self.scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)

        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # # Create a frame inside the canvas
        self.scrollable_frame = ctk.CTkFrame(self.canvas)
        self.scrollable_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Elements to be rendered later
        self.elements = []
    


    def add_text(self, text):
        self.elements.append(('text', text))


    def plot_graph(self, x, y, title='Sample Plot', xlabel='x', ylabel='y'):
        self.elements.append(('plot', (x, y, title, xlabel, ylabel)))


    def prompt_user(self, message, prompt):
        self.elements.append(('prompt', (message, prompt)))
    

    def add_table(self, data, headers: list):
        self.elements.append(('table', (data, headers)))


    def render(self):
        for element in self.elements:
            if element[0] == 'text':
                text = element[1]
                # Calculate number of lines in text
                num_lines = text.count('\n') + 1
                # Calculate height based on number of lines
                text_height = num_lines * 20  # Adjust multiplier as needed
                # Create CTkTextbox directly on the canvas, not in scrollable_frame
                text_display = ctk.CTkTextbox(self.scrollable_frame, wrap='word', height=text_height, activate_scrollbars=False)
                text_display.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
                text_display.insert(ctk.END, text + '\n')
                
            elif element[0] == 'plot':
                x, y, title, xlabel, ylabel = element[1]
                plot_frame = ctk.CTkFrame(self.scrollable_frame)
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
            
            elif element[0] == 'table':
                data, headers = element[1]
                values = data.insert(0, headers)
                table = CTkTable(master=self.scrollable_frame, values=data, header_color="#52AA91", colors=["#FFFFFF", "#DBEEEA"])
                table.pack(expand=True, fill="both", padx=20, pady=20)


        def render_main_page():
            pass
        