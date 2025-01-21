# musical Conway's Game of Life!
# pitch and volume controlled by cells!
# How to Use
# - Run the program.
# - Use the Start button to begin the simulation.
# - Adjust the speed using the slider.
# - Press Randomize to reset the grid.
# - Use the Volume slider to adjust the overall sound level.
# 
# another part of wofl's GoL module idea
# 
# Dependencies:
# before you can run will need:
# `pip install tkinter numba pyo wxpython `


import tkinter as tk
from tkinter import ttk
import numpy as np
from numba import jit
from pyo import *

@jit(nopython=True, parallel=True)
def compute_next_generation(grid, kernel):
    """Numba-accelerated grid computation."""
    height, width = grid.shape
    neighbor_count = np.zeros_like(grid)

    # Compute neighbors for each cell
    for y in range(height):
        for x in range(width):
            neighbors = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    neighbors += grid[(y + dy) % height, (x + dx) % width]
            neighbor_count[y, x] = neighbors

    # Apply Conway's rules
    next_grid = (neighbor_count == 3) | ((grid == 1) & (neighbor_count == 2))
    return next_grid.astype(np.uint8)

class LifeSoundGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Musical Conway's Game of Life")

        # Initialize pyo server
        self.server = Server().boot()
        self.server.start()

        # Grid variables
        self.width = 20
        self.height = 20
        self.grid = np.random.choice([0, 1], (self.height, self.width), p=[0.9, 0.1]).astype(np.uint8)
        self.kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        self.running = False

        # Sine wave generators for each row
        self.oscs = [Sine(freq=self.midi_to_freq(row + 60), mul=0.1).out() for row in range(self.height)]

        # Tkinter variables
        self.speed = tk.IntVar(value=500)  # Speed slider value (ms delay)
        self.volume = tk.DoubleVar(value=0.5)  # Volume slider value (0.0 to 1.0)

        # Create GUI controls
        self.create_controls()

    def midi_to_freq(self, midi_note):
        """Convert MIDI note to frequency."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    # Remaining methods (randomize_grid, run_simulation, etc.) are unchanged


    def create_controls(self):
        """Create the GUI controls."""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(padx=10, pady=10)

        # Start button
        ttk.Button(
            control_frame, text="Start", command=self.start_simulation
        ).pack(side=tk.LEFT, padx=5)

        # Stop button
        ttk.Button(
            control_frame, text="Stop", command=self.stop_simulation
        ).pack(side=tk.LEFT, padx=5)

        # Randomize button
        ttk.Button(
            control_frame, text="Randomize", command=self.randomize_grid
        ).pack(side=tk.LEFT, padx=5)

        # Speed slider
        ttk.Label(control_frame, text="Speed (ms):").pack(side=tk.LEFT, padx=5)
        ttk.Scale(
            control_frame, from_=50, to=1000, variable=self.speed, orient=tk.HORIZONTAL
        ).pack(side=tk.LEFT, padx=5)

        # Volume slider (use tk.Scale instead of ttk.Scale)
        tk.Label(control_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        tk.Scale(
            control_frame,
            from_=0.0, to=1.0,
            variable=self.volume,
            orient=tk.HORIZONTAL,
            resolution=0.01
        ).pack(side=tk.LEFT, padx=5)

        # Alive cells label
        self.alive_label = ttk.Label(self.root, text="Alive Cells: 0")
        self.alive_label.pack(pady=10)


    def midi_to_freq(self, midi_note):
        """Convert MIDI note to frequency."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    def randomize_grid(self):
        """Randomize the initial grid."""
        self.grid = np.random.choice([0, 1], (self.height, self.width), p=[0.9, 0.1]).astype(np.uint8)
        self.update_sounds()

    def start_simulation(self):
        """Start the simulation."""
        self.running = True
        self.run_simulation()

    def stop_simulation(self):
        """Stop the simulation."""
        self.running = False

    def run_simulation(self):
        """Run the simulation step by step."""
        if not self.running:
            return

        self.grid = compute_next_generation(self.grid, self.kernel)
        self.update_sounds()

        # Schedule the next step based on the speed slider value
        self.root.after(self.speed.get(), self.run_simulation)

    def update_sounds(self):
        """Update the sounds based on the grid state."""
        alive_cells = 0
        for y, row in enumerate(self.grid):
            volume = float(row.sum() / self.width)  # Normalize volume for the row
            self.oscs[y].mul = float(volume * self.volume.get())  # Scale by master volume
            alive_cells += row.sum()

        # Update alive cells label
        self.alive_label.config(text=f"Alive Cells: {alive_cells}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LifeSoundGenerator(root)
    root.mainloop()
