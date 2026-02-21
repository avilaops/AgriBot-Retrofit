"""
Example: Basic telemetry simulation
Demonstrates AgriBot telemetry generation and publishing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telemetry_spec import OperationType
from simulator import TelemetrySimulator, ConsolePublisher


def run_basic_example():
    """Run basic telemetry simulation"""
    
    print("=" * 70)
    print("AGRIBOT TELEMETRY SYSTEM - BASIC EXAMPLE")
    print("=" * 70)
    print()
    print("This example demonstrates:")
    print("  1. Creating a telemetry simulator")
    print("  2. Generating realistic GPS trajectories")
    print("  3. Simulating variable rate application")
    print("  4. Publishing to console")
    print()
    print("Press Ctrl+C to stop the simulation")
    print()
    
    # Create simulator
    simulator = TelemetrySimulator(
        device_id="agribot_demo",
        start_lat=-21.1234,
        start_lon=-47.5678,
        operation=OperationType.FERTILIZER_APPLICATION
    )
    
    # Create console publisher
    publisher = ConsolePublisher(verbose=True)
    
    # Run simulation for 20 seconds at 1 Hz
    try:
        simulator.run(
            publisher=publisher,
            duration_sec=20,
            interval_sec=1.0
        )
    except KeyboardInterrupt:
        print("\n\n✅ Simulation stopped by user")
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print()
    print("Next steps:")
    print("  - Try different operation types: --operation seeding")
    print("  - Enable MQTT: --mqtt --mqtt-broker localhost")
    print("  - Enable HTTP: --http http://localhost:8000/telemetry")
    print()
    print("For full options: python src/simulator.py --help")
    print("=" * 70)


if __name__ == "__main__":
    run_basic_example()
