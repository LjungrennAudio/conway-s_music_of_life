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
    def __init__(self):
        # Initialize pyo server
        self.server = Server().boot()
        self.server.start()

        # Grid variables
        self.width = 15
        self.height = 5
        self.grid = np.random.choice([0, 1], (self.height, self.width), p=[0.9, 0.1]).astype(np.uint8)
        self.kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])

        # Speed variable for simulation delay (ms)
        self.speed = 500  # Default to 500ms delay

        # Sine wave generators for each row
        self.oscs = [Sine(freq=self.midi_to_freq(row + 60), mul=0.1).out() for row in range(self.height)]

        # Start the simulation
        self.run_simulation()

    def midi_to_freq(self, midi_note):
        """Convert MIDI note to frequency."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    def run_simulation(self):
        """Run the simulation step by step."""
        try:
            while True:
                self.grid = compute_next_generation(self.grid, self.kernel)
                self.play_sounds()
                time.sleep(self.speed / 1000.0)  # Convert milliseconds to seconds
        except KeyboardInterrupt:
            print("Simulation stopped.")
            self.server.stop()

    def play_sounds(self):
        """Map grid state to sound."""
        for y, row in enumerate(self.grid):
            # Map row to a sine wave generator
            volume = row.sum() / self.width  # Normalize volume based on live cells in the row
            self.oscs[y].mul = float(volume)  # Convert NumPy float to Python float

if __name__ == "__main__":
    LifeSoundGenerator()
