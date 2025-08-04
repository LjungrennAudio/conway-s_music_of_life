# musical Conway's Game of Life!
# pitch and volume controlled by cells!
# How to Use
# - Run the program.
# - Use the dropdown menu to select a scale (e.g., Major, Minor, Pentatonic).
# - Use the Start button to begin the simulation.
# - Adjust the speed using the slider.
# - Press Randomize to reset the grid.
# - Use the Volume slider to adjust the overall sound level.
# - listento the simulation and enjoy the melodious Game of Life!
# 
# another part of wofl's GoL module idea
# 
# What’s New
# ::Scales Dropdown:
# 
# - Added a dropdown (ttk.Combobox) to dynamically switch scales.
# - Bind the selection to the change_scale method.
# - Predefined Scales:
# 
# ::Chromatic, Major, Minor, Pentatonic, and Blues scales spanning octaves 5 to 6.
# ::Dynamic Re-Quantization:
# When a new scale is selected, the oscillators' frequencies are updated to match the new scale.
# 
# Dependencies:
# before you can run will need:
# `pip install tkinter numba pyo wxpython`
# then `$python conway's_music_of_life_-_now with_scales.py` to run :)

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
        self.root.title("Ladies 'n Gentlemen: Conway's Music of Life")

        # Initialize Pyo server
        self.server = Server().boot()
        self.server.start()

        # Grid variables
        self.width = 22
        self.height = 22
        self.grid = np.random.choice([0, 1], (self.height, self.width), p=[0.9, 0.1]).astype(np.uint8)
        self.kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        self.running = False

        # Tables for different waveforms
        self.sine = HarmTable([1])  # Pure sine tone
        self.square = SquareTable()  # Square waveform
        self.saw = SawTable()  # Sawtooth waveform
        self.triangle = LinTable([(0, 0), (8191, 1), (16383, 0)], size=16384)  # Triangle waveform
        self.noise = LinTable([(0, 0.5), (4095, 1), (8191, 0), (12287, -1), (16383, -0.5)], size=16384)  # Noise-like table

        # Predefined scales (spanning multiple octaves)
        self.scales = {
            "Chromatic": [m for o in range(5, 7) for m in range(o * 12, o * 12 + 12)],
            "Major": [m for o in range(5, 7) for m in [o * 12, o * 12 + 2, o * 12 + 4, o * 12 + 5, o * 12 + 7, o * 12 + 9, o * 12 + 11]],
            "Minor": [m for o in range(5, 7) for m in [o * 12, o * 12 + 2, o * 12 + 3, o * 12 + 5, o * 12 + 7, o * 12 + 8, o * 12 + 10]],
            "Pentatonic": [m for o in range(5, 7) for m in [o * 12, o * 12 + 2, o * 12 + 4, o * 12 + 7, o * 12 + 9]],
            "Blues": [m for o in range(5, 7) for m in [o * 12, o * 12 + 3, o * 12 + 5, o * 12 + 6, o * 12 + 7, o * 12 + 10]],
        }

        # Set the initial scale
        self.current_scale_name = "Chromatic"
        self.CHROMATIC_SCALE = self.scales[self.current_scale_name]

        # Oscillators for each row (quantized to the initial scale)
        self.oscs = [
            Osc(self.sine, freq=self.midi_to_freq(self.quantize_pitch(row + 60)), mul=0.1).out()
            for row in range(self.height)
        ]

        # Tkinter variables
        self.speed = tk.IntVar(value=500)
        self.volume = tk.DoubleVar(value=0.5)

        # Create GUI controls
        self.create_controls()

    def create_controls(self):
        """Create the GUI controls."""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(padx=10, pady=10)

        # Start button
        ttk.Button(control_frame, text="Start", command=self.start_simulation).pack(
            side=tk.LEFT, padx=5
        )

        # Stop button
        ttk.Button(control_frame, text="Stop", command=self.stop_simulation).pack(
            side=tk.LEFT, padx=5
        )

        # Randomize button
        ttk.Button(control_frame, text="Randomize", command=self.randomize_grid).pack(
            side=tk.LEFT, padx=5
        )

        # Scale dropdown
        ttk.Label(control_frame, text="Scale:").pack(side=tk.LEFT, padx=5)
        self.scale_dropdown = ttk.Combobox(control_frame, values=list(self.scales.keys()))
        self.scale_dropdown.set(self.current_scale_name)
        self.scale_dropdown.bind("<<ComboboxSelected>>", self.change_scale)
        self.scale_dropdown.pack(side=tk.LEFT, padx=5)

        # Speed slider
        ttk.Label(control_frame, text="Speed (ms):").pack(side=tk.LEFT, padx=5)
        ttk.Scale(control_frame, from_=50, to=1000, variable=self.speed, orient=tk.HORIZONTAL).pack(
            side=tk.LEFT, padx=5
        )

        # Volume slider
        ttk.Label(control_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        tk.Scale(
            control_frame,
            from_=0.0,
            to=1.0,
            variable=self.volume,
            orient=tk.HORIZONTAL,
            resolution=0.01,
        ).pack(side=tk.LEFT, padx=5)

        # Alive cells label
        self.alive_label = ttk.Label(self.root, text="Alive Cells: 0")
        self.alive_label.pack(pady=10)

    def change_scale(self, event):
        """Update the scale when a new scale is selected."""
        self.current_scale_name = self.scale_dropdown.get()
        self.CHROMATIC_SCALE = self.scales[self.current_scale_name]

        # Re-quantize the oscillators to the new scale
        for y, osc in enumerate(self.oscs):
            quantized_midi = self.quantize_pitch(y + 60)
            osc.freq = self.midi_to_freq(quantized_midi)

    def quantize_pitch(self, midi_note):
        """Quantize MIDI note to the closest note in the allowed scale."""
        closest_note = min(self.CHROMATIC_SCALE, key=lambda x: abs(x - midi_note))
        return closest_note

    def midi_to_freq(self, midi_note):
        """Convert MIDI note to frequency."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

        # Start button
        ttk.Button(control_frame, text="Start", command=self.start_simulation).pack(
            side=tk.LEFT, padx=5
        )

        # Stop button
        ttk.Button(control_frame, text="Stop", command=self.stop_simulation).pack(
            side=tk.LEFT, padx=5
        )

        # Randomize button
        ttk.Button(control_frame, text="Randomize", command=self.randomize_grid).pack(
            side=tk.LEFT, padx=5
        )

        # Speed slider
        ttk.Label(control_frame, text="Speed (ms):").pack(side=tk.LEFT, padx=5)
        ttk.Scale(control_frame, from_=50, to=1000, variable=self.speed, orient=tk.HORIZONTAL).pack(
            side=tk.LEFT, padx=5
        )

        # Volume slider
        ttk.Label(control_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        tk.Scale(
            control_frame,
            from_=0.0,
            to=1.0,
            variable=self.volume,
            orient=tk.HORIZONTAL,
            resolution=0.01,
            ).pack(side=tk.LEFT, padx=5)

        # Alive cells label
        self.alive_label = ttk.Label(self.root, text="Alive Cells: 0")
        self.alive_label.pack(pady=10)

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
            neighbors = int(row.sum())
            alive_cells += neighbors

            # Select waveform based on number of neighbors
            if neighbors == 0:
                waveform = self.noise
            elif neighbors == 1:
                waveform = self.square
            elif 2 <= neighbors <= 3:
                waveform = self.sine
            elif 4 <= neighbors <= 5:
                waveform = self.saw
            else:
                waveform = self.triangle

            # Update oscillator
            self.oscs[y].setTable(waveform)
            self.oscs[y].mul = float(neighbors / self.width * self.volume.get())  # Scale by volume

        # Update alive cells label
        self.alive_label.config(text=f"Alive Cells: {alive_cells}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LifeSoundGenerator(root)
    root.mainloop()
