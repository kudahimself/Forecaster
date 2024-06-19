import customtkinter as ctk

# Create the main application window
app = ctk.CTk()

# Set the title of the window
app.title("Forecaster")

# Set the size of the window
app.geometry("856x645")

# Create a label with the text "Forecaster"
label = ctk.CTkLabel(app, text="Forecaster", font=("Arial", 24))
label.pack(pady=20)

# Create a button that asks "Do you want to see the data analysis?"
def on_button_click():
    # Add functionality for the button click here
    print("Button clicked! Show data analysis.")

button = ctk.CTkButton(app, text="Do you want to see the data analysis?", command=on_button_click)
button.pack(pady=20)

# Run the application
app.mainloop()
