"""
AgriBot Retrofit - Telemetry System
Autonomous agricultural robot telemetry streaming
"""

__version__ = "0.1.0"
__author__ = "CanaSwarm Ecosystem"

from .telemetry_spec import (
    TelemetryMessage,
    GPSPosition,
    OperationType,
    DeviceStatus
)

from .simulator import (
    TelemetrySimulator,
    MQTTPublisher,
    HTTPPublisher
)

__all__ = [
    'TelemetryMessage',
    'GPSPosition',
    'OperationType',
    'DeviceStatus',
    'TelemetrySimulator',
    'MQTTPublisher',
    'HTTPPublisher',
]
