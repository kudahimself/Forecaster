from abc import ABC, abstractmethod
import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AbstractPage(ABC):

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
