
import os
import sys
import winreg

from pysudo import sudo_function


FROZEN = True if getattr(sys, 'frozen', False) else False
KEYPATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_command_value(script: str) -> str:
    if not FROZEN:
        python = sys.executable
        return f'"{python}" "{script}"'
    else:
        return f'"{sys.argv[0]}"'

@sudo_function()
def setup_start_on_boot(script: str = "") -> bool:
    command = get_command_value(script)
    try:
        # 尝试为当前用户设置
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEYPATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "DyNamicS", 0, winreg.REG_SZ, command)
        print(f"Autostart installed.")
        return True
    except OSError as e:
        print(f"Autostart installation failed: {e}")
    return False

@sudo_function()
def remove_start_on_boot() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEYPATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "DyNamicS")
        print(f"Autostart removed.")
        return True
    except FileNotFoundError:
        print(f"Registry not found.")
        return True
    except OSError as e:
        print(f"Error removing autostart: {e}")
    return False

def change_working_dir():
    execute_path = sys.argv[0]
    working_dir, _ = os.path.split(execute_path)
    working_dir = os.path.abspath(os.path.normpath(working_dir))
    os.chdir(working_dir)
