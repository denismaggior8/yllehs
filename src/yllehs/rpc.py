from typing import Any, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from yllehs.device import VirtualDevice

class RPCError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class RPCHandler:
    def __init__(self, device: "VirtualDevice"):
        self.device = device

    async def execute(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = params or {}
        
        # Dispatch table
        if method == "Shelly.GetDeviceInfo":
            return self.device.get_device_info()
        elif method == "Shelly.GetStatus":
            return self.device.get_status()
        elif method == "Shelly.GetConfig":
            return self.device.get_config()
        elif method == "Shelly.ListMethods":
            return self.list_methods()
        elif method == "Shelly.Reboot":
            return self.device.reboot()
        
        # Switch RPC
        elif method == "Switch.GetStatus":
            cid = params.get("id", 0)
            comp = self.device.get_component("switch", cid)
            if not comp:
                raise RPCError(404, f"Component switch:{cid} not found")
            return comp.get_status()
        elif method == "Switch.GetConfig":
            cid = params.get("id", 0)
            comp = self.device.get_component("switch", cid)
            if not comp:
                raise RPCError(404, f"Component switch:{cid} not found")
            return comp.get_config()
        elif method == "Switch.SetConfig":
            cid = params.get("id", 0)
            comp = self.device.get_component("switch", cid)
            if not comp:
                raise RPCError(404, f"Component switch:{cid} not found")
            config = params.get("config", {})
            return comp.set_config(config)
        elif method == "Switch.Set":
            cid = params.get("id", 0)
            on = params.get("on")
            if on is None:
                raise RPCError(400, "Missing 'on' parameter")
            comp = self.device.get_component("switch", cid)
            if not comp:
                raise RPCError(404, f"Component switch:{cid} not found")
            return comp.set_output(bool(on), source="RPC")
        elif method == "Switch.Toggle":
            cid = params.get("id", 0)
            comp = self.device.get_component("switch", cid)
            if not comp:
                raise RPCError(404, f"Component switch:{cid} not found")
            return comp.toggle(source="RPC")
            
        # Input RPC
        elif method == "Input.GetStatus":
            cid = params.get("id", 0)
            comp = self.device.get_component("input", cid)
            if not comp:
                raise RPCError(404, f"Component input:{cid} not found")
            return comp.get_status()
        elif method == "Input.GetConfig":
            cid = params.get("id", 0)
            comp = self.device.get_component("input", cid)
            if not comp:
                raise RPCError(404, f"Component input:{cid} not found")
            return comp.get_config()
        elif method == "Input.SetConfig":
            cid = params.get("id", 0)
            comp = self.device.get_component("input", cid)
            if not comp:
                raise RPCError(404, f"Component input:{cid} not found")
            config = params.get("config", {})
            return comp.set_config(config)
        elif method == "Input.Trigger":
            cid = params.get("id", 0)
            state = params.get("state")
            event = params.get("event", "btn_down")
            comp = self.device.get_component("input", cid)
            if not comp:
                raise RPCError(404, f"Component input:{cid} not found")
            return comp.trigger(state=state, event_name=event)

        # HTTP RPC (supported on Gen2)
        elif method == "HTTP.GET":
            import aiohttp
            url = params.get("url")
            if not url:
                raise RPCError(400, "Missing 'url' parameter")
            timeout = params.get("timeout", 15)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as resp:
                    body = await resp.text()
                    return {"code": resp.status, "body": body, "headers": dict(resp.headers)}
        elif method == "HTTP.POST":
            import aiohttp
            url = params.get("url")
            if not url:
                raise RPCError(400, "Missing 'url' parameter")
            body_data = params.get("body", "")
            headers = params.get("headers", {})
            timeout = params.get("timeout", 15)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=body_data, headers=headers, timeout=timeout) as resp:
                    body = await resp.text()
                    return {"code": resp.status, "body": body, "headers": dict(resp.headers)}

        raise RPCError(404, f"Method '{method}' not found")

    def list_methods(self) -> Dict[str, Any]:
        methods = ["Shelly.GetDeviceInfo", "Shelly.GetStatus", "Shelly.GetConfig", "Shelly.ListMethods", "Shelly.Reboot", "HTTP.GET", "HTTP.POST"]
        has_switch = any(c.type == "switch" for c in self.device.components.values())
        has_input = any(c.type == "input" for c in self.device.components.values())
        if has_switch:
            methods.extend(["Switch.GetStatus", "Switch.GetConfig", "Switch.SetConfig", "Switch.Set", "Switch.Toggle"])
        if has_input:
            methods.extend(["Input.GetStatus", "Input.GetConfig", "Input.SetConfig", "Input.Trigger"])
        return {"methods": methods}
