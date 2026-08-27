from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComponentSpec(BaseModel):
    type: str  # "sys", "wifi", "relay", "switch", "input", "pm"
    id: int = 0
    name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    initial_status: Dict[str, Any] = Field(default_factory=dict)


class DeviceModelProfile(BaseModel):
    model: str
    name: str
    gen: int = 2  # 1, 2, 3
    app: str = "Plus1"
    type_name: str = "SHSW-1"  # Gen1 identifier
    components: List[ComponentSpec] = Field(default_factory=list)


DEVICE_PROFILES: Dict[str, DeviceModelProfile] = {
    # --- Gen 1 Models ---
    "shelly1": DeviceModelProfile(
        model="shelly1",
        name="Shelly 1",
        gen=1,
        app="Shelly1",
        type_name="SHSW-1",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"type": "SHSW-1", "mac": "AABBCCDDEE00"}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enabled": True}}, initial_status={"ip": "192.168.1.100", "has_ip": True, "rssi": -60}),
            ComponentSpec(type="relay", id=0, config={"name": "Relay 0", "appliance_type": "General"}, initial_status={"ison": False, "has_timer": False, "timer_remaining": 0, "source": "init"}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0"}, initial_status={"input": 0, "event": "", "event_cnt": 0}),
        ]
    ),
    "shelly1pm": DeviceModelProfile(
        model="shelly1pm",
        name="Shelly 1PM",
        gen=1,
        app="Shelly1PM",
        type_name="SHSW-PM",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"type": "SHSW-PM", "mac": "AABBCCDDEE0A"}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enabled": True}}, initial_status={"ip": "192.168.1.10A", "has_ip": True, "rssi": -55}),
            ComponentSpec(type="relay", id=0, config={"name": "Relay 0", "appliance_type": "General"}, initial_status={"ison": False, "has_timer": False, "timer_remaining": 0, "overpower": False, "source": "init"}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0"}, initial_status={"input": 0, "event": "", "event_cnt": 0}),
            ComponentSpec(type="pm", id=0, config={}, initial_status={"power": 0.0, "is_valid": True, "counters": [0.0, 0.0, 0.0], "total": 0}),
        ]
    ),
    "shelly25": DeviceModelProfile(
        model="shelly25",
        name="Shelly 2.5",
        gen=1,
        app="Shelly25",
        type_name="SHSW-25",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"type": "SHSW-25", "mac": "AABBCCDDEE0B"}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enabled": True}}, initial_status={"ip": "192.168.1.10B", "has_ip": True, "rssi": -52}),
            ComponentSpec(type="relay", id=0, config={"name": "Relay 0"}, initial_status={"ison": False, "has_timer": False, "timer_remaining": 0, "source": "init"}),
            ComponentSpec(type="relay", id=1, config={"name": "Relay 1"}, initial_status={"ison": False, "has_timer": False, "timer_remaining": 0, "source": "init"}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0"}, initial_status={"input": 0, "event": "", "event_cnt": 0}),
            ComponentSpec(type="input", id=1, config={"name": "Input 1"}, initial_status={"input": 0, "event": "", "event_cnt": 0}),
            ComponentSpec(type="pm", id=0, config={}, initial_status={"power": 0.0, "is_valid": True, "counters": [0.0, 0.0, 0.0], "total": 0}),
            ComponentSpec(type="pm", id=1, config={}, initial_status={"power": 0.0, "is_valid": True, "counters": [0.0, 0.0, 0.0], "total": 0}),
        ]
    ),

    # --- Gen 2 Models ---
    "plus-1": DeviceModelProfile(
        model="plus-1",
        name="Shelly Plus 1",
        gen=2,
        app="Plus1",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly Plus 1", "mac": "AABBCCDDEE01", "eco_mode": True}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.101", "status": "got ip", "rssi": -55}),
            ComponentSpec(type="switch", id=0, config={"name": "Switch 0", "in_mode": "follow", "initial_state": "off", "auto_on": False, "auto_off": False}, initial_status={"output": False, "source": "init", "temperature": {"tC": 42.5, "tF": 108.5}}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0", "type": "button", "invert": False}, initial_status={"state": False}),
        ]
    ),
    "plus-1pm": DeviceModelProfile(
        model="plus-1pm",
        name="Shelly Plus 1PM",
        gen=2,
        app="Plus1PM",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly Plus 1PM", "mac": "AABBCCDDEE02", "eco_mode": True}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.102", "status": "got ip", "rssi": -50}),
            ComponentSpec(type="switch", id=0, config={"name": "Switch 0", "in_mode": "follow", "initial_state": "off", "auto_on": False, "auto_off": False}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}, "temperature": {"tC": 44.0, "tF": 111.2}}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0", "type": "button", "invert": False}, initial_status={"state": False}),
        ]
    ),
    "plus-2pm": DeviceModelProfile(
        model="plus-2pm",
        name="Shelly Plus 2PM",
        gen=2,
        app="Plus2PM",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly Plus 2PM", "mac": "AABBCCDDEE03", "eco_mode": True}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.103", "status": "got ip", "rssi": -48}),
            ComponentSpec(type="switch", id=0, config={"name": "Switch 0", "in_mode": "follow", "initial_state": "off", "auto_on": False, "auto_off": False}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}, "temperature": {"tC": 45.0, "tF": 113.0}}),
            ComponentSpec(type="switch", id=1, config={"name": "Switch 1", "in_mode": "follow", "initial_state": "off", "auto_on": False, "auto_off": False}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}, "temperature": {"tC": 45.0, "tF": 113.0}}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0", "type": "button", "invert": False}, initial_status={"state": False}),
            ComponentSpec(type="input", id=1, config={"name": "Input 1", "type": "button", "invert": False}, initial_status={"state": False}),
        ]
    ),
    "plus-4pm": DeviceModelProfile(
        model="plus-4pm",
        name="Shelly Plus 4PM",
        gen=2,
        app="Plus4PM",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly Plus 4PM", "mac": "AABBCCDDEE04", "eco_mode": False}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.104", "status": "got ip", "rssi": -52}),
            ComponentSpec(type="switch", id=0, config={"name": "Switch 0"}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}}),
            ComponentSpec(type="switch", id=1, config={"name": "Switch 1"}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}}),
            ComponentSpec(type="switch", id=2, config={"name": "Switch 2"}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}}),
            ComponentSpec(type="switch", id=3, config={"name": "Switch 3"}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0"}, initial_status={"state": False}),
            ComponentSpec(type="input", id=1, config={"name": "Input 1"}, initial_status={"state": False}),
            ComponentSpec(type="input", id=2, config={"name": "Input 2"}, initial_status={"state": False}),
            ComponentSpec(type="input", id=3, config={"name": "Input 3"}, initial_status={"state": False}),
        ]
    ),
    "plus-i4": DeviceModelProfile(
        model="plus-i4",
        name="Shelly Plus i4",
        gen=2,
        app="Plusi4",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly Plus i4", "mac": "AABBCCDDEE05", "eco_mode": True}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.105", "status": "got ip", "rssi": -51}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0", "type": "button"}, initial_status={"state": False}),
            ComponentSpec(type="input", id=1, config={"name": "Input 1", "type": "button"}, initial_status={"state": False}),
            ComponentSpec(type="input", id=2, config={"name": "Input 2", "type": "button"}, initial_status={"state": False}),
            ComponentSpec(type="input", id=3, config={"name": "Input 3", "type": "button"}, initial_status={"state": False}),
        ]
    ),

    # --- Gen 3 Models ---
    "1-gen3": DeviceModelProfile(
        model="1-gen3",
        name="Shelly 1 Gen3",
        gen=3,
        app="1Gen3",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly 1 Gen3", "mac": "AABBCCDDEE31", "eco_mode": True}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.131", "status": "got ip", "rssi": -45}),
            ComponentSpec(type="switch", id=0, config={"name": "Switch 0", "in_mode": "follow", "initial_state": "off"}, initial_status={"output": False, "source": "init", "temperature": {"tC": 40.0, "tF": 104.0}}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0", "type": "button"}, initial_status={"state": False}),
        ]
    ),
    "1pm-gen3": DeviceModelProfile(
        model="1pm-gen3",
        name="Shelly 1PM Gen3",
        gen=3,
        app="1PMGen3",
        components=[
            ComponentSpec(type="sys", id=0, config={"device": {"name": "Shelly 1PM Gen3", "mac": "AABBCCDDEE32", "eco_mode": True}}),
            ComponentSpec(type="wifi", id=0, config={"sta": {"ssid": "YllehsWiFi", "enable": True}}, initial_status={"sta_ip": "192.168.1.132", "status": "got ip", "rssi": -45}),
            ComponentSpec(type="switch", id=0, config={"name": "Switch 0", "in_mode": "follow", "initial_state": "off"}, initial_status={"output": False, "source": "init", "apower": 0.0, "voltage": 230.0, "current": 0.0, "aenergy": {"total": 0.0, "minute_ts": 0}, "temperature": {"tC": 41.0, "tF": 105.8}}),
            ComponentSpec(type="input", id=0, config={"name": "Input 0", "type": "button"}, initial_status={"state": False}),
        ]
    )
}
