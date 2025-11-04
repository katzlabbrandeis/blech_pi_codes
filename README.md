# Raspberry Pi Laboratory Control System

This repository contains a collection of Python scripts designed for laboratory automation and control systems running on Raspberry Pi. The scripts primarily focus on controlling valves, managing experimental setups, and interfacing with various hardware components.

## Core Functionality

### Valve Control and Fluid Delivery

Several scripts in this repository provide functionality for controlling valves and fluid delivery systems:

- **shake_valves.py**: Provides utilities for valve control including:
  - `open_repeats()`: Opens valves repeatedly for a specified duration and number of repetitions
  - `clearout()`: Clears fluid lines by opening valves for a set duration
  - `clearout_menu()`: Interactive menu for clearing specific fluid lines

- **dan_taste_delivery.py**: Specialized script for taste delivery systems with functions like:
  - `clearout()`: Clears fluid lines using ports 31, 33, 35, 37
  - `open_repeats()`: Opens valves repeatedly with customizable timing parameters

- **pi_rig.py**: Core functionality for controlling experimental rigs with:
  - `clearout()`: Clears fluid lines using default ports 31, 33, 35, 37

### Experimental Control

- **pi_emg_laser_passive.py**: Controls EMG and laser equipment with:
  - `clearout()`: Specialized clearout function for ports 16, 18, 21, 22, 23, 24

- **pi_licking.py**: Monitors and records licking behavior in experimental subjects

- **seq_poke.py**, **seq_poke2.py**, **seq_poke3.py**: Series of scripts for sequential nose poke experiments with increasing complexity

- **nose_poke_testing.py**: Testing utilities for nose poke experimental setups

### Imaging and Monitoring

- **multi_camera.py**: Handles multiple camera inputs for experimental monitoring and recording

## Hardware Requirements

- Raspberry Pi (3 or newer recommended)
- GPIO connections to valves, sensors, and other experimental equipment
- Appropriate power supplies for connected hardware

## Installation

1. Clone this repository to your Raspberry Pi:
   ```
   git clone https://github.com/yourusername/pi-lab-control.git
   ```

2. Install required dependencies:
   ```
   pip install RPi.GPIO numpy pandas matplotlib
   ```

## Usage Examples

### Clearing Fluid Lines

```python
# Import the appropriate module for your setup
import pi_rig

# Clear all default fluid lines
pi_rig.clearout()

# Clear specific ports for 10 seconds
pi_rig.clearout(outports=[31, 33], dur=10)
```

### Running Valve Tests

```python
# Import valve control module
import shake_valves

# Open valves repeatedly
shake_valves.open_repeats(outports=[31, 33], opentime=0.05, repeats=20)
```

### Running Experimental Protocols

```python
# Import the appropriate experimental module
import seq_poke3

# Run the experiment with default parameters
seq_poke3.run_experiment()
```

## Contributing

Contributions to improve these scripts or add new functionality are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Specify your license here]

## Contact

[Your contact information]
