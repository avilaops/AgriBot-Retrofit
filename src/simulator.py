"""
AgriBot Retrofit - Telemetry Simulator
Generates realistic mock telemetry data for testing

Supports:
- MQTT publishing (mosquitto broker)
- HTTP POST to REST endpoint
- Console output for debugging
"""

import time
import json
import random
from datetime import datetime, timezone
from typing import Optional, Protocol
from pathlib import Path
import sys

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️  paho-mqtt not installed. MQTT publishing disabled.")

try:
    import requests
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    print("⚠️  requests not installed. HTTP publishing disabled.")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from telemetry_spec import (
    TelemetryMessage,
    GPSPosition,
    OperationType,
    DeviceStatus,
    OperationData,
    DeviceHealth
)


class TelemetryPublisher(Protocol):
    """Protocol for telemetry publishers"""
    def publish(self, message: TelemetryMessage) -> bool:
        """Publish telemetry message. Returns True on success."""
        ...


class ConsolePublisher:
    """Prints telemetry to console"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.count = 0
    
    def publish(self, message: TelemetryMessage) -> bool:
        self.count += 1
        
        if self.verbose:
            print(f"\n📡 Telemetry #{self.count} - {message.device_id}")
            print(f"   📍 GPS: ({message.gps.lat:.6f}, {message.gps.lon:.6f}) ±{message.gps.precision}m")
            print(f"   🚜 Operation: {message.operation.value}")
            print(f"   ⚡ Speed: {message.speed_kmh:.1f} km/h | Heading: {message.heading_deg}°")
            print(f"   📊 Status: {message.status.value}")
            
            if message.operation_data:
                print(f"   💊 Dose: {message.operation_data.applied_dose:.1f}/{message.operation_data.prescribed_dose:.1f} (Zone: {message.operation_data.zone_id})")
            
            if message.device_health:
                print(f"   🔋 Tank: {message.device_health.tank_level_pct:.0f}% | Battery: {message.device_health.battery_pct:.0f}%")
        else:
            print(f"📡 {self.count:03d} | {message.device_id} | {message.operation.value[:10]:<10} | "
                  f"({message.gps.lat:.4f}, {message.gps.lon:.4f}) | {message.speed_kmh:4.1f} km/h")
        
        return True


class MQTTPublisher:
    """Publishes telemetry via MQTT"""
    
    def __init__(self, broker: str = "localhost", port: int = 1883, 
                 topic: str = "agribot/telemetry", qos: int = 1):
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt is required for MQTT publishing")
        
        self.broker = broker
        self.port = port
        self.topic = topic
        self.qos = qos
        self.client = mqtt.Client()
        self.connected = False
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Connect
        try:
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            time.sleep(0.5)  # Wait for connection
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT connected to {self.broker}:{self.port}")
        else:
            print(f"❌ MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"⚠️  MQTT disconnected")
    
    def publish(self, message: TelemetryMessage) -> bool:
        if not self.connected:
            print(f"⚠️  MQTT not connected, skipping message")
            return False
        
        payload = message.model_dump_json()
        result = self.client.publish(self.topic, payload, qos=self.qos)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return True
        else:
            print(f"❌ MQTT publish failed: {result.rc}")
            return False
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


class HTTPPublisher:
    """Publishes telemetry via HTTP POST"""
    
    def __init__(self, endpoint: str, headers: Optional[dict] = None):
        if not HTTP_AVAILABLE:
            raise ImportError("requests is required for HTTP publishing")
        
        self.endpoint = endpoint
        self.headers = headers or {"Content-Type": "application/json"}
        self.session = requests.Session()
    
    def publish(self, message: TelemetryMessage) -> bool:
        try:
            payload = message.model_dump_json()
            response = self.session.post(
                self.endpoint,
                data=payload,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code in [200, 201, 202]:
                return True
            else:
                print(f"⚠️  HTTP {response.status_code}: {response.text[:100]}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP publish failed: {e}")
            return False


class TelemetrySimulator:
    """
    Simulates AgriBot telemetry data generation
    
    Features:
    - Realistic GPS path simulation (field traversal)
    - Variable rate operation tracking
    - Device health monitoring
    - Configurable operation types
    """
    
    def __init__(self, 
                 device_id: str = "agribot_001",
                 start_lat: float = -21.1234,
                 start_lon: float = -47.5678,
                 operation: OperationType = OperationType.FERTILIZER_APPLICATION):
        
        self.device_id = device_id
        self.lat = start_lat
        self.lon = start_lon
        self.operation = operation
        self.heading = 90.0  # East
        self.speed = 8.0  # km/h
        self.tank_level = 100.0
        self.battery = 100.0
        self.fuel = 100.0
        
        # Field traversal parameters
        self.row_width = 0.0001  # ~11m in degrees
        self.row_length = 0.005  # ~550m
        self.direction = 1  # 1 = forward, -1 = backward
        self.rows_completed = 0
    
    def _update_position(self, dt: float = 1.0):
        """Update GPS position based on speed and heading"""
        # Speed in degrees/second (approximate)
        speed_deg_per_sec = (self.speed / 3600) / 111  # 111 km per degree
        
        # Move along current heading
        if self.direction == 1:
            self.lon += speed_deg_per_sec * dt
        else:
            self.lon -= speed_deg_per_sec * dt
        
        # Check if reached end of row
        if abs(self.lon - (-47.5678)) > self.row_length:
            self._turn_around()
    
    def _turn_around(self):
        """Turn around at end of row"""
        self.direction *= -1
        self.lat += self.row_width  # Move to next row
        self.rows_completed += 1
        self.heading = 90.0 if self.direction == 1 else 270.0
    
    def _update_resources(self, dt: float = 1.0):
        """Update tank level, battery, fuel"""
        if self.operation in [OperationType.FERTILIZER_APPLICATION, OperationType.PESTICIDE_APPLICATION]:
            self.tank_level -= 0.05 * dt  # 5%/min consumption
        
        self.battery -= 0.01 * dt  # 1%/min drain
        self.fuel -= 0.02 * dt  # 2%/min consumption
        
        # Clamp to 0
        self.tank_level = max(0, self.tank_level)
        self.battery = max(0, self.battery)
        self.fuel = max(0, self.fuel)
    
    def generate_message(self) -> TelemetryMessage:
        """Generate one telemetry message"""
        
        # Determine zone based on position (mock)
        zone_id = f"Z{(int(self.lat * 10000) % 5) + 1:03d}"
        
        # Generate operation data
        operation_data = None
        if self.operation in [OperationType.FERTILIZER_APPLICATION, OperationType.PESTICIDE_APPLICATION]:
            prescribed = 100.0 + (hash(zone_id) % 50)  # 100-150 kg/ha
            actual = prescribed + random.uniform(-5, 5)  # ±5 kg/ha variation
            
            operation_data = OperationData(
                zone_id=zone_id,
                prescribed_dose=prescribed,
                applied_dose=actual,
                application_width_m=12.0
            )
        
        # Device health
        device_health = DeviceHealth(
            tank_level_pct=self.tank_level,
            battery_pct=self.battery,
            fuel_level_pct=self.fuel,
            engine_temp_c=85.0 + random.uniform(-5, 10),
            hydraulic_pressure_bar=180.0 + random.uniform(-10, 10)
        )
        
        # GPS noise
        gps = GPSPosition(
            lat=self.lat + random.uniform(-0.00001, 0.00001),
            lon=self.lon + random.uniform(-0.00001, 0.00001),
            precision=random.uniform(0.02, 0.08),
            altitude=850.0 + random.uniform(-2, 2)
        )
        
        # Determine status
        status = DeviceStatus.OPERATIONAL
        if self.tank_level < 10 or self.battery < 15 or self.fuel < 10:
            status = DeviceStatus.WARNING
        
        message = TelemetryMessage(
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc),
            gps=gps,
            speed_kmh=self.speed + random.uniform(-0.5, 0.5),
            heading_deg=self.heading,
            operation=self.operation,
            status=status,
            operation_data=operation_data,
            device_health=device_health,
            firmware_version="v2.3.1",
            operator_id="OP_042"
        )
        
        return message
    
    def run(self, 
            publisher: TelemetryPublisher,
            duration_sec: int = 60,
            interval_sec: float = 1.0):
        """
        Run simulation for specified duration
        
        Args:
            publisher: Telemetry publisher instance
            duration_sec: Simulation duration in seconds
            interval_sec: Telemetry interval in seconds
        """
        print(f"\n🚜 Starting AgriBot Telemetry Simulator")
        print(f"   Device: {self.device_id}")
        print(f"   Operation: {self.operation.value}")
        print(f"   Duration: {duration_sec}s | Interval: {interval_sec}s")
        print(f"   Start position: ({self.lat:.6f}, {self.lon:.6f})")
        print("=" * 70)
        
        start_time = time.time()
        message_count = 0
        success_count = 0
        
        try:
            while (time.time() - start_time) < duration_sec:
                # Generate and publish message
                message = self.generate_message()
                
                if publisher.publish(message):
                    success_count += 1
                
                message_count += 1
                
                # Update state
                self._update_position(interval_sec)
                self._update_resources(interval_sec / 60)  # Convert to minutes
                
                # Sleep until next interval
                time.sleep(interval_sec)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Simulation interrupted by user")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print(f"✅ Simulation Complete")
        print(f"   Duration: {elapsed:.1f}s")
        print(f"   Messages: {message_count} ({success_count} successful)")
        print(f"   Rows completed: {self.rows_completed}")
        print(f"   Final position: ({self.lat:.6f}, {self.lon:.6f})")
        print(f"   Tank: {self.tank_level:.1f}% | Battery: {self.battery:.1f}%")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AgriBot Telemetry Simulator")
    parser.add_argument("--device-id", default="agribot_001", help="Device identifier")
    parser.add_argument("--duration", type=int, default=30, help="Simulation duration (seconds)")
    parser.add_argument("--interval", type=float, default=1.0, help="Telemetry interval (seconds)")
    
    parser.add_argument("--mqtt", action="store_true", help="Enable MQTT publishing")
    parser.add_argument("--mqtt-broker", default="localhost", help="MQTT broker address")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--mqtt-topic", default="agribot/telemetry", help="MQTT topic")
    
    parser.add_argument("--http", type=str, help="HTTP endpoint URL")
    
    parser.add_argument("--operation", default="fertilizer_application",
                       choices=[op.value for op in OperationType],
                       help="Operation type")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = TelemetrySimulator(
        device_id=args.device_id,
        operation=OperationType(args.operation)
    )
    
    # Setup publishers
    publishers = [ConsolePublisher(verbose=True)]
    
    if args.mqtt and MQTT_AVAILABLE:
        mqtt_pub = MQTTPublisher(
            broker=args.mqtt_broker,
            port=args.mqtt_port,
            topic=args.mqtt_topic
        )
        publishers.append(mqtt_pub)
    
    if args.http and HTTP_AVAILABLE:
        http_pub = HTTPPublisher(endpoint=args.http)
        publishers.append(http_pub)
    
    # Composite publisher
    class MultiPublisher:
        def __init__(self, publishers):
            self.publishers = publishers
        
        def publish(self, message):
            results = [pub.publish(message) for pub in self.publishers]
            return any(results)
    
    # Run simulation
    multi_pub = MultiPublisher(publishers)
    simulator.run(multi_pub, duration_sec=args.duration, interval_sec=args.interval)
