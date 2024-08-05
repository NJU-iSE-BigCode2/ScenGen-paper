import os
import platform
import subprocess
import time
from typing import Optional, Tuple

import cv2

from testbot.logger import logger
from testbot.utils import gen_timestamp


class Device:
    def __init__(self, device_platform: str = "android", device_id: Optional[str] = None):
        self.platform = device_platform
        if self.platform == "android":
            output = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            device_list = [line.split("\t")[0] for line in output.stdout.strip().split("\n")[1:]]
            if len(device_list) == 0:
                raise RuntimeError("No devices available")
            else:
                if device_id is None:
                    self.device_id = device_list[0]
                elif device_id in device_list:
                    self.device_id = device_id
                else:
                    raise ValueError(f"Unknown device_id: {device_id}")
            self.width = None
            self.height = None
        else:
            raise ValueError(f"Unsupported platform: {device_platform}")
        
        
class DeviceManager:
    def __init__(self, device: Device, base_dir: str, mode: str = "SILENT"):
        self.mode = mode
        self.device = device
        self.resize_ratio = None
        self.default_package = self.get_current_app_message()[0]
        self.special_character = ("'", "?", "&", "#", "<", ">")
        self.xml_folder = os.path.join(base_dir, "data", "xml")
        self.apk_folder = os.path.join(base_dir, "data", "apk")
        self.screenshot_folder = os.path.join(base_dir, "data", "input")
        self.marked_screenshot_folder = os.path.join(base_dir, "output", "merge")

    def set_resize_ratio(self, ratio: float) -> None:
        self.resize_ratio = ratio
        if self.mode == "DEBUG":
            logger.debug(f"Resize Ratio Set: {self.resize_ratio}")

    def op_click(self, x: int, y: int) -> str:
        """Click on x, y."""
        if self.resize_ratio is not None:
            x = x // self.resize_ratio
            y = y // self.resize_ratio
        else:
            logger.warning("Resize ratio not set")
        cmd = f"adb -s {self.device.device_id} shell input tap {x} {y}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: click on x={x}, y={y}")
        return cmd

    def op_input(self, text: str) -> str:
        """Input text."""
        text_bk = text
        if len(text) > 0:
            text = text.replace(" ", "%s")
            text = text.replace('"', "'")
            for char in self.special_character:
                text = text.replace(f"{char}", f"\\{char}")
            cmd = f"adb -s {self.device.device_id} shell input text \"{text}\""
            subprocess.run(cmd, shell=True)
        else:
            cmd = "input blank string"
        if self.mode == "DEBUG":
            text = text_bk.replace("\n", "\\n")
            logger.debug(f"Execution: input text ```{text}```")
        return cmd

    def op_scroll(self, x_start: int, y_start: int, x_end: int, y_end: int, duration: int = 500) -> str:
        """Scroll screen."""
        cmd = f"adb -s {self.device.device_id} shell input swipe {x_start} {y_start} {x_end} {y_end} {duration}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: swipe screen ({x_start}, {y_start}) to ({x_end}, {y_end})")
        return cmd
    
    def install_app(self, apk_path: str) -> str:
        """Install app from apk file."""
        cmd = f"adb -s {self.device.device_id} install {apk_path}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Installed: {apk_path}")
        return cmd

    def uninstall_app(self, app_package: str) -> str:
        """Uninstall app by package name."""
        cmd = f"adb -s {self.device.device_id} uninstall {app_package}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Uninstalled: {app_package}")
        return cmd

    def get_current_app_message(self) -> Tuple[str, str]:
        """Show current app message."""
        system_name = platform.system().lower()
        filter_cmd = "findstr" if system_name == "windows" else "grep"
        cmd = f"adb -s {self.device.device_id} shell dumpsys window windows | {filter_cmd} mFocusedApp"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        result = result[result.find("u0") + 2:].strip().split(" ")[0]
        package, activity = result.split("/", maxsplit=1)
        return package, activity

    def launch_app(self, app_package: str, app_launch_activity: str) -> str:
        """Launch app by package name and launch activity."""
        cmd = f"adb -s {self.device.device_id} shell am start {app_package}/{app_launch_activity}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Launched: {app_package}/{app_launch_activity}")
        return cmd

    def close_app(self, app_package: str) -> str:
        """Close app by package name."""
        cmd = f"adb -s {self.device.device_id} shell am force-stop {app_package}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Stopped: {app_package}")
        return cmd

    def back(self) -> str:
        """Back to previous page."""
        cmd = f"adb -s {self.device.device_id} shell input keyevent 4"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: back")
        return cmd

    def wait(self) -> str:
        """Wait for loading"""
        time.sleep(2)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: wait")
        return "wait 2 seconds"

    def delete_char(self, repeat: int = 1) -> str:
        cmd = f"adb -s {self.device.device_id} shell input keyevent KEYCODE_DEL"
        for _ in range(repeat):
            subprocess.run(cmd, shell=True)
            time.sleep(.1)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: delete char * {repeat}")
        return f"{cmd} * {repeat}"

    def get_screenshot(self) -> str:
        """Get screenshot and save to local."""
        screenshot_src = "/sdcard/screenshot.png"
        screenshot_dest = f"{self.screenshot_folder}/screenshot-{gen_timestamp()}.png"
        cmd1 = f"adb -s {self.device.device_id} shell screencap -p {screenshot_src}"
        cmd2 = f"adb pull {screenshot_src} {screenshot_dest}"
        subprocess.run(cmd1, shell=True)
        subprocess.run(cmd2, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Screenshot Captured: {screenshot_dest}")
        if self.device.width is None and self.device.height is None:
            screen = cv2.imread(screenshot_dest)
            self.device.width = screen.shape[1]
            self.device.height = screen.shape[0]
        return screenshot_dest

    def get_apk_file(self, app_package: str) -> str:
        """Get apk file from device."""
        cmd = f"adb -s {self.device.device_id} shell pm path {app_package}"
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        apk_file_src = output.stdout.strip("package:")
        apk_file_dest = f"{self.apk_folder}/{gen_timestamp()}.apk"
        cmd = f"adb -s {self.device.device_id} pull {apk_file_src} {apk_file_dest}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"APK file downloaded: {apk_file_dest}")
        return apk_file_dest

