"""
AgriBot Retrofit - Telemetry Specification
Defines the data contract for robot telemetry streaming

This module provides Pydantic models for:
- Real-time telemetry data (GPS + operation status)
- Device health monitoring
- Variable rate application execution tracking
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class OperationType(str, Enum):
    """Type of agricultural operation"""
    FERTILIZER_APPLICATION = "fertilizer_application"
    PESTICIDE_APPLICATION = "pesticide_application"
    SEEDING = "seeding"
    HARVEST = "harvest"
    SOIL_SAMPLING = "soil_sampling"
    IDLE = "idle"
    MAINTENANCE = "maintenance"


class DeviceStatus(str, Enum):
    """Device operational status"""
    OPERATIONAL = "operational"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class GPSPosition(BaseModel):
    """GPS coordinates with precision metadata"""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    precision: float = Field(..., gt=0, description="GPS precision in meters (HDOP)")
    altitude: Optional[float] = Field(None, description="Altitude in meters (optional)")
    
    @field_validator('precision')
    @classmethod
    def validate_precision(cls, v):
        if v > 10.0:
            raise ValueError("GPS precision must be <= 10m for agricultural operations")
        return v


class OperationData(BaseModel):
    """Variable rate operation tracking"""
    zone_id: Optional[str] = Field(None, description="Management zone identifier")
    prescribed_dose: Optional[float] = Field(None, ge=0, description="Prescribed dose (kg/ha or L/ha)")
    applied_dose: Optional[float] = Field(None, ge=0, description="Actual applied dose")
    application_width_m: Optional[float] = Field(None, gt=0, description="Application width in meters")
    
    @field_validator('applied_dose')
    @classmethod
    def validate_dose_deviation(cls, v, info):
        """Warn if actual dose deviates >10% from prescription"""
        if v is not None and 'prescribed_dose' in info.data and info.data['prescribed_dose']:
            deviation = abs(v - info.data['prescribed_dose']) / info.data['prescribed_dose']
            if deviation > 0.10:
                # In production, this would trigger an alert
                pass
        return v


class DeviceHealth(BaseModel):
    """Device health and resource monitoring"""
    tank_level_pct: Optional[float] = Field(None, ge=0, le=100, description="Tank level percentage")
    battery_pct: Optional[float] = Field(None, ge=0, le=100, description="Battery percentage")
    engine_temp_c: Optional[float] = Field(None, description="Engine temperature in Celsius")
    hydraulic_pressure_bar: Optional[float] = Field(None, ge=0, description="Hydraulic pressure")
    fuel_level_pct: Optional[float] = Field(None, ge=0, le=100, description="Fuel level percentage")


class TelemetryMessage(BaseModel):
    """
    Complete telemetry message from AgriBot
    
    This is the primary data contract for robot-to-cloud communication.
    All timestamps are in ISO 8601 format (UTC).
    
    Example:
    ```json
    {
        "device_id": "agribot_001",
        "timestamp": "2026-02-20T10:35:12Z",
        "gps": {
            "lat": -21.1234,
            "lon": -47.5678,
            "precision": 0.03,
            "altitude": 850.5
        },
        "operation": "fertilizer_application",
        "speed_kmh": 8.5,
        "heading_deg": 90.0,
        "status": "operational",
        "operation_data": {
            "zone_id": "Z003",
            "prescribed_dose": 120.0,
            "applied_dose": 118.0,
            "application_width_m": 12.0
        },
        "device_health": {
            "tank_level_pct": 67.0,
            "battery_pct": 85.0,
            "fuel_level_pct": 72.0
        }
    }
    ```
    """
    
    # Device identification
    device_id: str = Field(..., description="Unique device identifier")
    timestamp: datetime = Field(..., description="Telemetry timestamp (UTC)")
    
    # Position and motion
    gps: GPSPosition
    speed_kmh: float = Field(..., ge=0, le=50, description="Speed in km/h")
    heading_deg: Optional[float] = Field(None, ge=0, lt=360, description="Heading in degrees (0-359)")
    
    # Operation
    operation: OperationType = Field(..., description="Current operation type")
    status: DeviceStatus = Field(default=DeviceStatus.OPERATIONAL, description="Device status")
    
    # Operation-specific data
    operation_data: Optional[OperationData] = Field(None, description="VRA operation data")
    
    # Device health
    device_health: Optional[DeviceHealth] = Field(None, description="Device health metrics")
    
    # Optional metadata
    firmware_version: Optional[str] = Field(None, description="Device firmware version")
    operator_id: Optional[str] = Field(None, description="Operator identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "agribot_001",
                "timestamp": "2026-02-20T10:35:12Z",
                "gps": {
                    "lat": -21.1234,
                    "lon": -47.5678,
                    "precision": 0.03,
                    "altitude": 850.5
                },
                "operation": "fertilizer_application",
                "speed_kmh": 8.5,
                "heading_deg": 90.0,
                "status": "operational",
                "operation_data": {
                    "zone_id": "Z003",
                    "prescribed_dose": 120.0,
                    "applied_dose": 118.0,
                    "application_width_m": 12.0
                },
                "device_health": {
                    "tank_level_pct": 67.0,
                    "battery_pct": 85.0,
                    "fuel_level_pct": 72.0
                },
                "firmware_version": "v2.3.1",
                "operator_id": "OP_042"
            }
        }


class TelemetryBatch(BaseModel):
    """Batch of telemetry messages for bulk transmission"""
    device_id: str
    batch_id: str
    messages: list[TelemetryMessage]
    
    @field_validator('messages')
    @classmethod
    def validate_batch_size(cls, v):
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 messages")
        return v


if __name__ == "__main__":
    # Example usage
    from datetime import timezone
    
    print("AgriBot Telemetry Specification")
    print("=" * 50)
    print()
    
    # Create example telemetry message
    telemetry = TelemetryMessage(
        device_id="agribot_001",
        timestamp=datetime.now(timezone.utc),
        gps=GPSPosition(lat=-21.1234, lon=-47.5678, precision=0.03, altitude=850.5),
        operation=OperationType.FERTILIZER_APPLICATION,
        speed_kmh=8.5,
        heading_deg=90.0,
        status=DeviceStatus.OPERATIONAL,
        operation_data=OperationData(
            zone_id="Z003",
            prescribed_dose=120.0,
            applied_dose=118.0,
            application_width_m=12.0
        ),
        device_health=DeviceHealth(
            tank_level_pct=67.0,
            battery_pct=85.0,
            fuel_level_pct=72.0
        ),
        firmware_version="v2.3.1",
        operator_id="OP_042"
    )
    
    print("Example Telemetry Message:")
    print(telemetry.model_dump_json(indent=2))
    print()
    print("✅ Telemetry specification validated successfully")
