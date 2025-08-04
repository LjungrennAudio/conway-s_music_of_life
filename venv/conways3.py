# musical Conway's Game of Life!
# pitch and volume controlled by cells!
#
# How to Use
# - Run the program.
# - Use the dropdown menu to select a scale (e.g., Major, Minor, Pentatonic).
# - Use the Start button to begin the simulation.
# - Adjust the speed using the slider.
# - Press Randomize to reset the grid.
# - Use the Volume slider to adjust the overall sound level.
# - Listen to the simulation and enjoy the melodious Game of Life!
#
# a new version using pygame.mixer for sound
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
# `pip install pygame numba`
# then `$python conways.py` to run :)

import tkinter as tk
from tkinter import ttk
import numpy as np
from numba import jit
import pygame.mixer
import math

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

        # Initialize Pygame mixer
        pygame.mixer.init(44100, -16, 2, 2048)
        pygame.mixer.set_num_channels(22)
        self.channels = [pygame.mixer.Channel(i) for i in range(22)]

        # Grid variables
        self.width = 22
        self.height = 22
        self.grid = np.random.choice([0, 1], (self.height, self.width), p=[0.9, 0.1]).astype(np.uint8)
        self.kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        self.running = False
        self.current_row = 0
        self.full_next_grid = np.zeros_like(self.grid)

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
        self.current_scale = self.scales[self.current_scale_name]
        
        self.sound_library = {}
        self.generate_sound_library()

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
    
    def generate_sound_library(self):
        """Generates a library of plucked notes for each possible pitch and waveform."""
        self.sound_library = {}
        waveforms = ["sine", "square", "saw", "triangle", "noise"]
        for midi_note in self.current_scale:
            for waveform_type in waveforms:
                freq = self.midi_to_freq(midi_note)
                key = (midi_note, waveform_type)
                self.sound_library[key] = self.generate_plucked_sound(freq, waveform_type)

    def change_scale(self, event):
        """Update the scale and regenerate the sound library when a new scale is selected."""
        self.current_scale_name = self.scale_dropdown.get()
        self.current_scale = self.scales[self.current_scale_name]
        self.generate_sound_library()

    def quantize_pitch(self, midi_note):
        """Quantize MIDI note to the closest note in the allowed scale."""
        closest_note = min(self.current_scale, key=lambda x: abs(x - midi_note))
        return closest_note

    def midi_to_freq(self, midi_note):
        """Convert MIDI note to frequency."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
        
    def generate_plucked_sound(self, frequency, waveform_type="sine", duration=0.25, decay_time=0.2):
        """Generate a short, plucked sound with an exponential decay envelope."""
        sample_rate = 44100
        n_samples = int(round(duration * sample_rate))
        buf = np.zeros((n_samples,), dtype=np.int16)
        
        amplitude = 32767  # Max amplitude for 16-bit audio
        
        decay_samples = int(round(decay_time * sample_rate))
        decay_envelope = np.exp(-5 * np.arange(decay_samples) / decay_samples)
        
        for s in range(n_samples):
            t = float(s) / sample_rate
            
            # Apply the waveform
            if waveform_type == "sine":
                wave_value = math.sin(2 * math.pi * frequency * t)
            elif waveform_type == "square":
                wave_value = math.copysign(1, math.sin(2 * math.pi * frequency * t))
            elif waveform_type == "saw":
                wave_value = (2 * ((frequency * t) - math.floor(frequency * t + 0.5)))
            elif waveform_type == "triangle":
                v = 2 * ((frequency * t) - math.floor(frequency * t + 0.5))
                wave_value = (2 * abs(v) - 1)
            else: # "noise"
                wave_value = (2 * np.random.rand() - 1)
            
            # Apply the decay envelope
            if s < decay_samples:
                envelope_value = decay_envelope[s]
            else:
                envelope_value = 0
            
            buf[s] = int(amplitude * wave_value * envelope_value)
            
        return pygame.mixer.Sound(buffer=buf)

    def get_waveform_name(self, neighbors):
        """Determine waveform based on number of neighbors for a single cell."""
        if neighbors == 0:
            return "noise"
        elif neighbors == 1:
            return "square"
        elif 2 <= neighbors <= 3:
            return "sine"
        elif 4 <= neighbors <= 5:
            return "saw"
        else:
            return "triangle"

    def randomize_grid(self):
        """Randomize the initial grid."""
        self.grid = np.random.choice([0, 1], (self.height, self.width), p=[0.9, 0.1]).astype(np.uint8)
        pygame.mixer.stop()

    def start_simulation(self):
        """Start the simulation."""
        self.running = True
        # First, compute the entire next grid to get all updates
        self.full_next_grid = compute_next_generation(self.grid, self.kernel)
        self.current_row = 0
        self.scan_grid_line_by_line()

    def stop_simulation(self):
        """Stop the simulation."""
        self.running = False

    def scan_grid_line_by_line(self):
        """
        Updates the grid one row at a time, like a TV scan, and plays sounds
        for newly occupied cells in that row.
        """
        if not self.running:
            return

        # Check for new live cells in the current row
        for x in range(self.width):
            if self.full_next_grid[self.current_row, x] == 1 and self.grid[self.current_row, x] == 0:
                # Play a sound for this newly live cell
                midi_note = self.quantize_pitch(self.current_row + 60)
                
                # We need the neighbors of this new cell to determine waveform
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        neighbors += self.full_next_grid[(self.current_row + dy) % self.height, (x + dx) % self.width]
                
                waveform_name = self.get_waveform_name(neighbors - 1) # Subtract 1 because the cell itself is not its own neighbor
                
                sound = self.sound_library.get((midi_note, waveform_name))
                if sound:
                    channel = pygame.mixer.find_channel(True)
                    if channel:
                        channel.set_volume(self.volume.get())
                        channel.play(sound)

        # Update the current row of the grid with the new state
        self.grid[self.current_row, :] = self.full_next_grid[self.current_row, :]

        # Increment row counter
        self.current_row += 1

        # Check if the scan is complete
        if self.current_row >= self.height:
            # If so, a full generation has passed, so we prepare for the next scan
            self.full_next_grid = compute_next_generation(self.grid, self.kernel)
            self.current_row = 0
            
            # Update alive cells label at the end of a full generation scan
            alive_cells = np.sum(self.grid)
            self.alive_label.config(text=f"Alive Cells: {alive_cells}")

        # Schedule the next row's update with a shorter delay
        row_delay = int(self.speed.get() / self.height)
        self.root.after(max(row_delay, 1), self.scan_grid_line_by_line)


if __name__ == "__main__":
    root = tk.Tk()
    app = LifeSoundGenerator(root)
    root.mainloop()
    pygame.mixer.quit()