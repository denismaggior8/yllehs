import os
import json
from typing import Dict, Optional, Any
from yllehs.profiles import DEVICE_PROFILES, DeviceModelProfile
from yllehs.components import Component, create_component
from yllehs.rpc import RPCHandler
from yllehs.runtime import ScriptRuntime

class VirtualDevice:
    def __init__(self, name: str, model: str, port: int, firmware: Optional[str] = None, script_path: Optional[str] = None):
        self.name = name
        self.model = model
        self.port = port
        self.script_path = script_path
        
        if model not in DEVICE_PROFILES:
            raise ValueError(f"Unsupported Shelly model: {model}")
        
        self.profile: DeviceModelProfile = DEVICE_PROFILES[model]
        self.gen = self.profile.gen
        self.firmware = firmware or ("1.14.0" if self.gen == 1 else "1.4.0")
        
        self.components: Dict[str, Component] = {}
        self._init_components()
        
        self.rpc_handler = RPCHandler(self)
        self.runtime = ScriptRuntime(self) if self.gen >= 2 else None

        # Hook component notifications into runtime if Gen2+
        if self.runtime:
            for comp in self.components.values():
                comp.add_listener(self._handle_component_notification)

            if self.script_path and os.path.isfile(self.script_path):
                with open(self.script_path, "r") as f:
                    self.runtime.load_script(f.read())

    def _init_components(self):
        for spec in self.profile.components:
            comp = create_component(spec)
            self.components[comp.key] = comp

    def _handle_component_notification(self, event_type: str, data: Dict[str, Any]):
        if self.runtime:
            if event_type == "event":
                self.runtime.on_event(data)
            elif event_type == "status_change":
                self.runtime.on_status_change(data)

    def get_component(self, comp_type: str, comp_id: int) -> Optional[Component]:
        return self.components.get(f"{comp_type}:{comp_id}")

    def get_device_info(self) -> Dict[str, Any]:
        mac = self.components.get("sys:0", Component("sys", 0, {}, {})).config.get("device", {}).get("mac", "AABBCCDDEE00")
        if self.gen == 1:
            return {
                "type": self.profile.type_name,
                "mac": mac,
                "auth": False,
                "fw": self.firmware,
                "discoverable": True,
                "num_outputs": len([c for c in self.components.values() if c.type == "relay"]),
                "num_meters": len([c for c in self.components.values() if c.type == "pm"])
            }
        else:
            return {
                "id": f"yllehs-{self.name}",
                "mac": mac,
                "model": self.profile.model,
                "gen": self.profile.gen,
                "fw_id": self.firmware,
                "ver": self.firmware,
                "app": self.profile.app,
                "auth_en": False,
                "auth_domain": None
            }

    def get_status(self) -> Dict[str, Any]:
        if self.gen == 1:
            res = {
                "wifi_sta": self.components.get("wifi:0", Component("wifi", 0, {}, {})).get_status(),
                "relays": [c.get_status() for c in self.components.values() if c.type == "relay"],
                "inputs": [c.get_status() for c in self.components.values() if c.type == "input"],
                "meters": [c.get_status() for c in self.components.values() if c.type == "pm"],
                "mac": self.components.get("sys:0", Component("sys", 0, {}, {})).config.get("device", {}).get("mac", "AABBCCDDEE00"),
            }
            return res
        else:
            res = {
                "sys": self.components.get("sys:0", Component("sys", 0, {}, {})).get_status(),
                "wifi": self.components.get("wifi:0", Component("wifi", 0, {}, {})).get_status(),
            }
            for k, comp in self.components.items():
                if comp.type in ["switch", "input"]:
                    res[f"{comp.type}:{comp.id}"] = comp.get_status()
            return res

    def get_config(self) -> Dict[str, Any]:
        if self.gen == 1:
            return {
                "device": {"type": self.profile.type_name, "mac": "AABBCCDDEE00"},
                "wifi_sta": self.components.get("wifi:0", Component("wifi", 0, {}, {})).get_config(),
                "relays": [c.get_config() for c in self.components.values() if c.type == "relay"],
            }
        else:
            res = {
                "sys": self.components.get("sys:0", Component("sys", 0, {}, {})).get_config(),
                "wifi": self.components.get("wifi:0", Component("wifi", 0, {}, {})).get_config(),
            }
            for k, comp in self.components.items():
                if comp.type in ["switch", "input"]:
                    res[f"{comp.type}:{comp.id}"] = comp.get_config()
            return res

    def reboot(self) -> Dict[str, Any]:
        if self.runtime:
            self.runtime.stop()
            self.runtime = ScriptRuntime(self)
            if self.script_path and os.path.isfile(self.script_path):
                with open(self.script_path, "r") as f:
                    self.runtime.load_script(f.read())
        return {"restart_required": False}

    def stop(self):
        if self.runtime:
            self.runtime.stop()
