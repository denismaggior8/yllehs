import time
from typing import Any, Dict, Optional, Callable, List

class Component:
    def __init__(self, comp_type: str, comp_id: int, config: Dict[str, Any], initial_status: Dict[str, Any]):
        self.type = comp_type
        self.id = comp_id
        self.key = f"{comp_type}:{comp_id}"
        self.config = dict(config)
        self.status = dict(initial_status)
        self.status["id"] = comp_id
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    def add_listener(self, listener: Callable[[str, Dict[str, Any]], None]):
        self.listeners.append(listener)

    def notify(self, event_type: str, data: Dict[str, Any]):
        for l in self.listeners:
            l(event_type, data)

    def get_status(self) -> Dict[str, Any]:
        return dict(self.status)

    def get_config(self) -> Dict[str, Any]:
        return dict(self.config)

    def set_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        self.config.update(new_config)
        return {"restart_required": False}


class SwitchComponent(Component):
    def __init__(self, comp_id: int, config: Dict[str, Any], initial_status: Dict[str, Any]):
        super().__init__("switch", comp_id, config, initial_status)
        if "output" not in self.status:
            self.status["output"] = False
        if "source" not in self.status:
            self.status["source"] = "init"

    def set_output(self, on: bool, source: str = "RPC") -> Dict[str, Any]:
        was_on = self.status.get("output", False)
        self.status["output"] = bool(on)
        self.status["source"] = source
        if "apower" in self.status:
            self.status["apower"] = 50.0 if on else 0.0
            self.status["current"] = 0.22 if on else 0.0

        if was_on != on:
            self.notify("status_change", {"component": self.key, "delta": {"output": on, "source": source}, "status": self.get_status()})
            self.notify("event", {"component": self.key, "event": "toggle", "ts": time.time(), "id": self.id})
        return {"was_on": was_on}

    def toggle(self, source: str = "RPC") -> Dict[str, Any]:
        cur = self.status.get("output", False)
        return self.set_output(not cur, source=source)


class RelayComponent(Component):
    def __init__(self, comp_id: int, config: Dict[str, Any], initial_status: Dict[str, Any]):
        super().__init__("relay", comp_id, config, initial_status)
        if "ison" not in self.status:
            self.status["ison"] = False
        if "has_timer" not in self.status:
            self.status["has_timer"] = False
        if "timer_remaining" not in self.status:
            self.status["timer_remaining"] = 0

    def set_state(self, turn: str) -> Dict[str, Any]:
        if turn == "on":
            self.status["ison"] = True
        elif turn == "off":
            self.status["ison"] = False
        elif turn == "toggle":
            self.status["ison"] = not self.status["ison"]
        self.notify("status_change", {"component": self.key, "status": self.get_status()})
        return self.get_status()


class InputComponent(Component):
    def __init__(self, comp_id: int, config: Dict[str, Any], initial_status: Dict[str, Any]):
        super().__init__("input", comp_id, config, initial_status)
        if "state" not in self.status and "input" not in self.status:
            self.status["state"] = False

    def trigger(self, state: Optional[bool] = None, event_name: str = "btn_down") -> Dict[str, Any]:
        if state is not None:
            if "state" in self.status:
                self.status["state"] = bool(state)
            if "input" in self.status:
                self.status["input"] = 1 if state else 0
        if "event" in self.status:
            self.status["event"] = event_name
            self.status["event_cnt"] = self.status.get("event_cnt", 0) + 1

        self.notify("event", {"component": self.key, "event": event_name, "ts": time.time(), "id": self.id})
        self.notify("status_change", {"component": self.key, "delta": {"state": self.status.get("state")}, "status": self.get_status()})
        return self.get_status()


def create_component(spec) -> Component:
    if spec.type == "switch":
        return SwitchComponent(spec.id, spec.config, spec.initial_status)
    elif spec.type == "relay":
        return RelayComponent(spec.id, spec.config, spec.initial_status)
    elif spec.type == "input":
        return InputComponent(spec.id, spec.config, spec.initial_status)
    else:
        return Component(spec.type, spec.id, spec.config, spec.initial_status)
