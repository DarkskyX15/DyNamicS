
import os
import sys
import time
import json
import subprocess
from queue import Queue, Empty
from typing import Any, TypedDict

from pysudo import sudo_check

from ._suda import SudaLoginClient
from ._wifi import scan_and_deduplicate_wifi, connect_to_wifi


class InterfaceRebootFlags(TypedDict):
    enabled: bool
    wait_duration: bool
    interface: str
    enable_cmd: str
    disable_cmd: str

class AdvancedFlags(TypedDict):
    full_admin_mode: bool
    interface_reboot: InterfaceRebootFlags

class ServiceConfig:
    api_url: str
    api_token: str
    use_wifi: bool
    target_ssid: str
    wifi_password: str
    suda_config_path: str
    scan_interval: float
    start_on_boot: bool
    isp: str
    account: str
    password: str

    advanced_flags: AdvancedFlags


    def __init__(self, path: str | None = None) -> None:
        if path is None:
            path = "service.json"
            if not os.path.exists(path):
                self.generate_default(path)
        self._path = path
        self.update_from_file(path)


    def generate_default(self, path: str) -> None:
        c = {
            "api_url": "http://127.0.0.1/",
            "api_token": "dns-xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "use_wifi": False,
            "target_ssid": "SUDA_WIFI",
            "wifi_password": "your_wifi_password",
            "suda_config_path": "suda.json",
            "scan_interval": 60.0,
            "start_on_boot": True,
            "isp": "中国移动",
            "account": "your_account",
            "password": "your_password",
            "advanced_flags": {
                "full_admin_mode": False,
                "interface_reboot": {
                    "enabled": False,
                    "interface": "EitherNet",
                    "wait_duration": 10.0,
                    "disable_cmd": "netsh interface set interface \"%s\" admin=disable",
                    "enable_cmd": "netsh interface set interface \"%s\" admin=enable"
                }
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=4)

    def update_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            config: dict[str, Any] = json.load(f)
        for key, value in config.items():
            setattr(self, key, value)

    def update_from_dict(self, kwargs: dict[str, Any]):
        self.__dict__.update(kwargs)

    def save_config(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self.dump_dict(), f, indent=4, ensure_ascii=False)

    def dump_dict(self) -> dict[str, Any]:
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }


class ServiceMessage(TypedDict):
    type: str
    args: dict[str, Any]



class Service:

    _tunnel: Queue[ServiceMessage | None]
    _config: ServiceConfig
    _client: SudaLoginClient
    _timestamp: float

    def __init__(self) -> None:
        self._tunnel = Queue()
        self._config = ServiceConfig()
        self._client = SudaLoginClient()
        self._client.update_config(self._config.suda_config_path)
    

    def _reload_config(self, kwargs: dict[str, Any]) -> None:
        self._config.update_from_dict(kwargs)

    def _save_config(self) -> None:
        self._config.save_config()


    # Advanced Modes functions

    def advanced_interface_reboot(self, cfg: InterfaceRebootFlags) -> bool:
        if not sudo_check():
            print(
                "This feature requires admin privilege, consider setting"
                " advanced flag 'full_admin_mode' to true."
            )
            return False
    
        interface = cfg["interface"]
        enable_cmd = cfg["enable_cmd"] % (interface, )
        disable_cmd = cfg["disable_cmd"] % (interface, )

        try_count = 0

        while try_count < 3 and not self._client.inet_available:
            print(f"Disabling interface {interface}...")
            subprocess.run(disable_cmd, shell=True)
            time.sleep(cfg["wait_duration"])

            print(f"Enabling interface {interface}...")
            subprocess.run(enable_cmd, shell=True)
            time.sleep(cfg["wait_duration"])

            self._client.update_status()
            try_count += 1

        return self._client.inet_available
    

    def _scan_once(self) -> None:
        self._client.update_status()

        if not self._client.inet_available:

            if not self._config.use_wifi:
                print("Connection error with non-WiFi mode, service won't work properly.")

                if self._config.advanced_flags["interface_reboot"]["enabled"]:
                    print("Try rebooting network interface...")
                    self.advanced_interface_reboot(self._config.advanced_flags["interface_reboot"])
                return

            wifi_infos = scan_and_deduplicate_wifi(5)
            found = False
            for wifi in wifi_infos:
                if wifi["ssid"] == self._config.target_ssid:
                    found = connect_to_wifi(wifi["ssid"], self._config.wifi_password)
                    time.sleep(3)
                    break
            if not found:
                print("Cannot connect to WiFi: %s." % self._config.target_ssid)
                return

            self._client.update_status()
            self._client.update_isp()

        if not self._client.login_status:
            if not self._client.login(
                self._config.isp, self._config.account, self._config.password
            ):
                print("Login attempt failed.")
                return
            print("Login succeeded.")
        
        print("Current ip: %s" % self._client.current_ip)


    def process_message(self, message: ServiceMessage) -> None:
        if message["type"] == "update":
            self._reload_config(message["args"])
        elif message["type"] == "save":
            self._save_config()

    def mainloop(self) -> None:
        self._client.update_status()
        self._client.update_isp()
        self._timestamp = 0
        while True:
            try:
                data = self._tunnel.get_nowait()
                if data is None:
                    break
                self.process_message(data)
                self._scan_once()
                self._timestamp = time.time()
            except Empty:
                if time.time() - self._timestamp > self._config.scan_interval:
                    self._scan_once()
                    self._timestamp = time.time()
            finally:
                time.sleep(1.0)

    def check_full_admin(self) -> bool:
        return self._config.advanced_flags["full_admin_mode"]


    def save_config(self) -> None:
        self._tunnel.put({"type": "save", "args": {}})

    def update_config(self, kwargs: dict[str, Any]) -> None:
        self._tunnel.put({"type": "update", "args": kwargs})
    
    def stop(self) -> None:
        self._tunnel.put(None)

    @property
    def config(self) -> ServiceConfig:
        return self._config

    @property
    def client(self) -> SudaLoginClient:
        return self._client
