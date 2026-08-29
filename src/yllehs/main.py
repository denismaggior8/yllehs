import os
import sys
import yaml
import asyncio
from aiohttp import web
from typing import List
from yllehs.device import VirtualDevice
from yllehs.server import create_device_app
from yllehs.mdns import MDNSAdvertiser

async def run_server(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    devices_cfg = config.get("devices", [])
    if not devices_cfg:
        print("No devices configured.", flush=True)
        return

    runners: List[web.AppRunner] = []
    devices: List[VirtualDevice] = []

    for d_cfg in devices_cfg:
        name = d_cfg.get("name", "shelly")
        model = d_cfg.get("model", "plus-1")
        port = d_cfg.get("port", 8080)
        firmware = d_cfg.get("firmware", None)
        script = d_cfg.get("script", None)

        device = VirtualDevice(name=name, model=model, port=port, firmware=firmware, script_path=script)
        devices.append(device)
        
        app = create_device_app(device)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        runners.append(runner)
        print(f"Started virtual Shelly device '{name}' (model: {model}) on http://0.0.0.0:{port}", flush=True)

    # Start mDNS ZeroConf discovery for Home Assistant
    mdns = MDNSAdvertiser()
    mdns.start(devices)

    # Start scripts after event loop and HTTP servers are active
    for device in devices:
        device.start_script()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        mdns.stop()
        for d in devices:
            d.stop()
        for r in runners:
            await r.cleanup()

def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "yllehs.yaml"
    if not os.path.isfile(cfg_path):
        print(f"Config file '{cfg_path}' not found.", flush=True)
        sys.exit(1)
    asyncio.run(run_server(cfg_path))

if __name__ == "__main__":
    main()
