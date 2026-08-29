import socket
from typing import List
from zeroconf import IPVersion, ServiceInfo, Zeroconf
from yllehs.device import VirtualDevice

class MDNSAdvertiser:
    def __init__(self):
        self.zeroconf: Zeroconf | None = None
        self.services: List[ServiceInfo] = []

    def start(self, devices: List[VirtualDevice]):
        try:
            self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            local_ip = self._get_local_ip()

            for dev in devices:
                dev_info = dev.get_device_info()
                mac = dev_info.get("mac", "AABBCCDDEE00").lower()
                clean_name = dev.name.lower().replace(" ", "-")
                service_name = f"yllehs-{clean_name}-{mac}"

                properties = {
                    "gen": str(dev.gen),
                    "model": dev.model,
                    "app": dev_info.get("app", "Plus1"),
                    "ver": str(dev.firmware),
                    "id": dev_info.get("id", f"yllehs-{clean_name}"),
                    "mac": mac,
                    "discoverable": "true",
                }

                info = ServiceInfo(
                    type_="_shelly._tcp.local.",
                    name=f"{service_name}._shelly._tcp.local.",
                    addresses=[socket.inet_aton(local_ip)],
                    port=dev.port,
                    properties=properties,
                    server=f"{service_name}.local."
                )

                self.zeroconf.register_service(info)
                self.services.append(info)
        except Exception as e:
            print(f"[mDNS] Warning: Failed to initialize ZeroConf advertiser ({e})", flush=True)

    def stop(self):
        if self.zeroconf:
            for info in self.services:
                try:
                    self.zeroconf.unregister_service(info)
                except Exception:
                    pass
            self.zeroconf.close()
            self.services.clear()

    def _get_local_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
