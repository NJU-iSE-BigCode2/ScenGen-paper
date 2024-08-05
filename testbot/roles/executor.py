import time
from typing import Any, Dict, Tuple

from testbot.device import DeviceManager
from testbot.logger import logger
from testbot.memory import Memory
from testbot.roles.recorder import TestRecorder


class ActionExecutor:
    def __init__(self, device_manager: DeviceManager, recorder: TestRecorder):
        self.device_manager = device_manager
        self.recorder = recorder
        self.rotate_angle = 0

    def execute(self, memory: Memory):
        action = memory.performed_actions[-1]
        op_type = action["action-type"]
        op_position = action.get("position")
        op_target_widget = action.get("target-widget")
        op_widget_position = op_target_widget.get("position") if op_target_widget is not None else None
        op_direction = action.get("scroll-direction") if op_type == "scroll" else None
        op_input_text = action.get("input-text") if op_type == "input" else None

        if op_type == "touch":
            if op_widget_position is not None:
                if op_position is None:
                    x, y = self.get_touch_coordinate(op_widget_position)
                else:
                    x, y = self.get_touch_coordinate(op_widget_position, op_position)
                cmd = self.click(x, y)
                action["command"] = cmd
                self.recorder.record(action, memory, True)
                logger.info(f"Touch on ({x}, {y})")
            else:
                logger.warning("Unknown widget position")

        elif op_type == "input":
            if op_widget_position is not None:
                if op_position is None:
                    x, y = self.get_touch_coordinate(op_widget_position)
                else:
                    x, y = self.get_touch_coordinate(op_widget_position, op_position)
            else:
                x, y = -1, -1
            if op_input_text is not None:
                cmd = self.input(x, y, op_input_text)
                action["command"] = cmd
                self.recorder.record(action, memory, True)
                text4log = op_input_text.replace("\n", "\\n")
                if len(text4log) > 25:
                    text4log = text4log[:20] + "..."
                logger.info(f"Input ```{text4log}``` ({x}, {y})")
            else:
                logger.warning("No text for input action")

        elif op_type == "scroll":
            if op_direction is not None:
                cmd = self.scroll(op_direction)
                action["command"] = cmd
                self.recorder.record(action, memory, True)
                logger.info(f"Scroll {op_direction} the screen")
            else:
                logger.warning("No direction for scroll action")

        elif op_type == "back":
            back_intent = action["intent"]
            if back_intent == "NEED-BACK":
                backed_action = memory.performed_actions[-2]
                cmd = self.back(backed_action)
            else:
                cmd = self.device_manager.back()
                time.sleep(.5)
            action["command"] = cmd
            self.recorder.record(action, memory, False)
            logger.info("Back operation")

        elif op_type == "wait":
            cmd = self.wait()
            action["command"] = cmd
            self.recorder.record(action, memory, False)
            logger.info("Wait operation")

        elif op_type == "start":
            cmd = self.launch(memory.app_package, memory.app_launch_activity)
            action["command"] = cmd
            self.recorder.record(action, memory, False)
            logger.info("Launch the application")

        elif op_type == "end":
            cmd = self.stop(memory.app_package)
            action["command"] = cmd
            self.recorder.record(action, memory, False)
            logger.info("Stop the application")

        elif op_type == "reload":
            raise NotImplementedError()

        else:
            logger.error("Unknown action")

        if self.device_manager.get_current_app_message()[0] \
                == self.device_manager.default_package:
            self.device_manager.launch_app(
                memory.app_package,
                memory.app_launch_activity,
            )

    def launch(self, package_name: str, launch_act_name: str, sleep_time: float = 5.0) -> str:
        cmd = self.device_manager.launch_app(package_name, launch_act_name)
        time.sleep(sleep_time)
        return cmd

    def stop(self, package_name: str, sleep_time: float = 0.5) -> str:
        cmd = self.device_manager.close_app(package_name)
        time.sleep(sleep_time)
        return cmd

    def back(self, backed_action: Dict[str, Any], sleep_time: float = 0.5) -> str:
        if backed_action["action-type"] == "touch":
            cmd = self.device_manager.back()
        elif backed_action["action-type"] == "input":
            text = backed_action["input-text"]
            cmd = self.device_manager.delete_char(repeat=len(text))
        elif backed_action["action-type"] == "scroll":
            direction = backed_action["scroll-direction"]
            w, h = self.device_manager.device.width, self.device_manager.device.height
            back_scroll_arg = {
                "UP": (w // 2, int(h * 0.2), w // 2, int(h * 0.8)),
                "DOWN": (w // 2, int(h * 0.8), w // 2, int(h * 0.2)),
                "LEFT": (int(w * 0.2), h // 2, int(w * 0.8), h // 2),
                "RIGHT": (int(w * 0.8), h // 2, int(w * 0.2), h // 2),
            }
            x_start, y_start, x_end, y_end = back_scroll_arg[direction.upper()]
            cmd = self.device_manager.op_scroll(x_start, y_start, x_end, y_end, 500)
            time.sleep(sleep_time)
        else:
            cmd = "<None>"
        time.sleep(sleep_time)
        return cmd

    def wait(self) -> str:
        return self.device_manager.wait()

    def click(self, x: int, y: int, sleep_time: float = 2.0) -> str:
        cmd = self.device_manager.op_click(x, y)
        time.sleep(sleep_time)
        return cmd

    def input(self, x: int, y: int, text: str, sleep_time: float = 1.0) -> str:
        if x > 0 and y > 0:
            cmd = self.device_manager.op_click(x, y)
            time.sleep(sleep_time + 1)
            cmd += " & "
        else:
            cmd = ""
        cmd += self.device_manager.op_input(text)
        time.sleep(sleep_time)
        return cmd

    def scroll(self, direction: str, duration: int = 500, sleep_time: float = 1.0) -> str:
        w, h = self.device_manager.device.width, self.device_manager.device.height
        scroll_arg = {
            "DOWN": (w // 2, int(h * 0.8), w // 2, int(h * 0.2)),
            "UP": (w // 2, int(h * 0.2), w // 2, int(h * 0.8)),
            "RIGHT": (int(w * 0.8), h // 2, int(w * 0.2), h // 2),
            "LEFT": (int(w * 0.2), h // 2, int(w * 0.8), h // 2),
        }
        x_start, y_start, x_end, y_end = scroll_arg[direction.upper()]
        cmd = self.device_manager.op_scroll(x_start, y_start, x_end, y_end, duration)
        time.sleep(sleep_time)
        return cmd

    def get_touch_coordinate(self, position: Dict[str, int], mode: str = "self") -> Tuple[int, int]:
        x_min, y_min = position["column_min"], position["row_min"]
        x_max, y_max = position["column_max"], position["row_max"]
        x_limit = self.device_manager.device.width * self.device_manager.resize_ratio
        y_limit = self.device_manager.device.height * self.device_manager.resize_ratio
        x_offset, y_offset = 40, 60  # be flexible to change

        x0, y0 = (x_min + x_max) // 2, (y_min + y_max) // 2
        if mode == "left":
            x0 = min(max(x_min - x_offset, 0), max(x_min - x_offset // 2, 0))
        elif mode == "right":
            x0 = max(min(x_max + x_offset, x_limit), min(x_max + x_offset // 2, x_limit))
        elif mode == "up":
            y0 = min(max(y_min - y_offset, 0), max(y_min - y_offset // 2, 0))
        elif mode == "down":
            y0 = max(min(y_max + y_offset, y_limit), min(y_max + y_offset // 2, y_limit))

        if self.rotate_angle == 90:
            return y0, x_limit - x0
        if self.rotate_angle == 180:
            return x_limit - x0, y_limit - y0
        if self.rotate_angle == 270:
            return y_limit - y0, x0
        return x0, y0
