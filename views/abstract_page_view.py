from abc import ABC, abstractmethod
import customtkinter as ctk
from CTkTable import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import statsmodels.api as sm


class AbstractPage(ABC):

    def __init__(self):
        self.app_background = '#161B25'
        self.app_button_colour = '#2E3C4F'


    def display_table(self, frame, table, button_colour='#2E3C4F',
                      colors=["#4C6382","#3A4C63"],
                      text_colour='white'):
        plot_frame = ctk.CTkFrame(frame, fg_color='transparent')
        plot_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        table = CTkTable(master=plot_frame, values=table,
                         header_color=button_colour, colors=colors,
                         text_color=text_colour)
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
    
    def display_line_graph(self, frame, plot_data, logarithmic=False):
        if logarithmic:
            shift_constant = abs(plot_data[1].min()) + 1
            y = (plot_data[1] + shift_constant).apply(lambda x: np.log(x))
            title= 'Logarithmic ' + plot_data[2]
        else:
            y = plot_data[1]
            title= plot_data[2]

        x = plot_data[0]
        m = y.rolling(window=10).mean()
        xlabel= plot_data[3]
        ylabel = plot_data[4]
        plot_frame = ctk.CTkFrame(frame)
        plot_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111)

        # Plot original data
        ax.plot(x, y, color='#736AC9', label='Original Data')
        # Plot moving average
        ax.plot(x, m, color='yellow', label='Moving Average')

        fig.set_facecolor("#2E3C4F")
        ax.set_facecolor('#2E3C4F')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        axis_color = '#FFFFFF'
        ax.xaxis.label.set_color(axis_color)
        ax.yaxis.label.set_color(axis_color)
        ax.tick_params(axis='x', colors=axis_color)
        ax.tick_params(axis='y', colors=axis_color)
        ax.title.set_color(axis_color)
        
        # Display only the first and last value on the x-axis
        ax.set_xticks([x.iloc[0], x.iloc[-1]])
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
    
    def display_histogram(self, frame, plot_data):
        x = plot_data[0]
        y = plot_data[1]
        title= plot_data[2]
        xlabel= plot_data[3]
        ylabel = plot_data[4]
        plot_frame = ctk.CTkFrame(frame)
        plot_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111)
        ax.hist(y, density=True, orientation='horizontal', color='#736AC9')
        fig.set_facecolor("#2E3C4F")
        ax.set_facecolor('#2E3C4F')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        axis_color = '#FFFFFF'
        ax.xaxis.label.set_color(axis_color)
        ax.yaxis.label.set_color(axis_color)
        ax.tick_params(axis='x', colors=axis_color)
        ax.tick_params(axis='y', colors=axis_color)
        ax.title.set_color(axis_color)
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
    
    def display_autocovariance(self, frame, plot_data):

        y = plot_data[5]
        title= plot_data[2]
        xlabel= plot_data[3]
        ylabel = plot_data[4]
        plot_frame = ctk.CTkFrame(frame)
        plot_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111)

        sm.graphics.tsa.plot_acf(y, lags=29, ax = ax, color='#736AC9')

        fig.set_facecolor("#2E3C4F")
        ax.set_facecolor('#2E3C4F')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        axis_color = '#FFFFFF'
        ax.xaxis.label.set_color(axis_color)
        ax.yaxis.label.set_color(axis_color)
        ax.tick_params(axis='x', colors=axis_color)
        ax.tick_params(axis='y', colors=axis_color)
        ax.title.set_color(axis_color)
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
    

    def display_model(self, frame, plot_data):

        y = plot_data[1]
        x = plot_data[0]
        X_test = plot_data[2]
        y_pred = plot_data[3]
        title= plot_data[4]
        xlabel= plot_data[5]
        ylabel = plot_data[6]
        plot_frame = ctk.CTkFrame(frame)
        plot_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111)

        # Plot original data
        ax.scatter(x, y, color='#736AC9', label='Original Data')
        # Plot Model
        ax.plot(X_test, y_pred, color='yellow', label='Model Data')

        fig.set_facecolor("#2E3C4F")
        ax.set_facecolor('#2E3C4F')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        axis_color = '#FFFFFF'
        ax.xaxis.label.set_color(axis_color)
        ax.yaxis.label.set_color(axis_color)
        ax.tick_params(axis='x', colors=axis_color)
        ax.tick_params(axis='y', colors=axis_color)
        ax.title.set_color(axis_color)
        
        # Display only the first and last value on the x-axis
        # ax.set_xticks([x.iloc[0], x.iloc[-1]])
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)