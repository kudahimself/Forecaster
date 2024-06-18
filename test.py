import matplotlib.pyplot as plt

# Use the terminal backend
plt.switch_backend('module://matplotlib_terminal.backend')

# Sample data
x = [1, 2, 3, 4, 5]
y = [10, 20, 30, 40, 50]

# Create a plot
plt.plot(x, y)
plt.title('Sample Plot')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')

# Show the plot in the terminal
plt.show()
