import os
from typing import Any, Dict, Optional

from testbot.memory import Memory
from testbot.device import DeviceManager
from testbot.llm import LLMChatManager
from testbot.logger import logger
from testbot.config import APPS, SCENARIOS
from testbot.roles.decider import ActionDecider
from testbot.roles.executor import ActionExecutor
from testbot.roles.observer import Observer
from testbot.roles.recorder import TestRecorder
from testbot.roles.supervisor import TestSupervisor


class TestAgent:
    def __init__(self, device_manager: DeviceManager, base_dir: str):
        self.state = "UNINITIALIZED"
        self.app = None
        self.scenario = None
        self.llm = LLMChatManager()
        self.device_manager = device_manager
        self.observer = Observer(device_manager, self.llm)
        self.decider = ActionDecider(self.llm)
        self.recorder = TestRecorder(self.llm, base_dir)
        self.executor = ActionExecutor(device_manager, self.recorder)
        self.supervisor = TestSupervisor(self.llm)
        self.memory = Memory()
        self.loading_check_fail_count = 0
        self.match_error_count = 0
        self.decide_error_count = 0
        self.rotate_angle = 0
        self.issue_table = [
            "",
            "error occurred in matching target widget with its number",  # 1
            "necessary preliminary action was neglected causing the app to not respond correctly",  # 2
            "the selected action triggered the bug of the app",  # 3
            "the selected action doesn't correspond to the task scenario"  # 4
        ]

    def initialize(self, app_id: str, scenario_id: str, rotate_angle: int = 0):
        if self.state == "UNINITIALIZED":
            logger.info("Initializing TestAgent")
            self.state = "INITIALIZED"
            self.app: Dict = APPS[app_id]
            self.scenario: Dict = SCENARIOS[scenario_id]
            self.rotate_angle = rotate_angle
            self.executor.rotate_angle = rotate_angle
            self.memory.app_name = self.app["name"]
            self.memory.app_package = self.app["package"]
            self.memory.app_launch_activity = self.app["launch-activity"]
            self.memory.target_scenario = self.scenario["description"]
            if "extra-info" in self.scenario.keys():
                self.memory.add_basic_info(self.scenario["extra-info"])
            self.device_manager.launch_app(
                self.memory.app_package,
                self.memory.app_launch_activity,
            )
        else:
            logger.warning("TestAgent has already been initialized")

    def step(self) -> Optional[Any]:
        if self.state == "UNINITIALIZED":
            _continue = self._state_uninitialized()
            if not _continue:
                return None

        if self.state == "EXECUTING":
            _continue = self._state_executing()
            if not _continue:
                return None

        screenshot_path = self.observer.capture_screenshot(self.rotate_angle)
        self.memory.cache_screenshot(screenshot_path)

        if self.state == "INITIALIZED":
            _continue = self._state_initialized()
            if not _continue:
                return None

        if self.state == "LOAD-CHECKING":
            _continue = self._state_load_checking()
            if not _continue:
                return None

        if self.state == "EFFECT-CHECKING":
            _continue = self._state_effect_checking()
            if not _continue:
                return None

        if self.state == "END-CHECKING":
            _continue = self._state_end_checking()
            if not _continue:
                return None

        if self.state == "CORRECTING":
            _continue = self._state_correcting()
            if not _continue:
                return None

        if self.state == "OBSERVING":
            _continue = self._state_observing()
            if not _continue:
                return None

        return None

    def report_self(self):
        meta_info = {
            "resize-ratio": self.device_manager.resize_ratio,
            "device-width": self.device_manager.device.width,
            "device-height": self.device_manager.device.height,
        }
        if self.state == "FAILED" or self.state == "ERROR":
            script_path = self.recorder.scripted(
                self.app["id"],
                self.scenario["id"],
                addition=meta_info,
                failed=True,
                full_chat=True,
            )
            logger.info(f"Script Generated: {script_path}")
        elif self.state == "END":
            script_path = self.recorder.scripted(
                self.app["id"],
                self.scenario["id"],
                addition=meta_info,
                full_chat=True,
            )
            logger.info(f"Script Generated: {script_path}")
        else:
            logger.info(f"Agent State: {self.state}. TestING...")

    def _state_uninitialized(self) -> bool:
        logger.waring(f"TestAgent State: {self.state}")
        return False

    def _state_initialized(self) -> bool:
        self.state = "OBSERVING"
        return True

    def _state_executing(self) -> bool:
        # call function to execute decided action and record the action
        self.executor.execute(self.memory)
        self.state = "LOAD-CHECKING"
        return True

    def _state_load_checking(self) -> bool:
        if self.loading_check_fail_count > 2:
            self.loading_check_fail_count = 0
            self.state = "EFFECT-CHECKING"
            return True
        is_loading = self.supervisor.check_loading(self.memory)
        if is_loading is None:
            self.state = "ERROR"
            self.report_self()
            return False
        if is_loading:
            self.loading_check_fail_count += 1
            wait_action = {"action-type": "wait", "intent": "wait for loading"}
            self.memory.add_action(wait_action)
            self.executor.execute(self.memory)
            self.memory.remove_last_action()
            return False
        else:
            self.loading_check_fail_count = 0
            self.state = "EFFECT-CHECKING"
            return True

    def _state_effect_checking(self) -> bool:
        valid, need_back = self.supervisor.check_effect(self.memory)
        if valid is None:
            self.state = "ERROR"
            self.report_self()
            return False
        if not valid:
            if need_back:
                back_action = {"action-type": "back", "intent": "NEED-BACK"}
                self.memory.add_action(back_action)
                self.executor.execute(self.memory)
            self.state = "CORRECTING"
        else:
            self.match_error_count = 0
            self.decide_error_count = 0
            self.state = "END-CHECKING"
        return True

    def _state_end_checking(self) -> bool:
        test_end = self.supervisor.check_end(self.memory)
        if test_end is None:
            self.state = "ERROR"
            self.report_self()
            return False
        if test_end:
            self.state = "END"
            logger.info("Test Finished")
            self.report_self()
            return False
        else:
            self.state = "OBSERVING"
            return True

    def _state_observing(self) -> bool:
        self.memory.save_screenshot(self.memory.cached_screenshot)
        self.memory.cached_screenshot = None
        # 1. send original image and prompt to llm, decide next action
        action = self.decider.next_action(self.memory)
        # 2. detect widgets in original image, generate marked image
        screenshot_path = self.memory.current_screenshot
        screenshot_with_bbox_path, resize_ratio, elements = self.observer.detect_widgets(screenshot_path)
        self.memory.save_screenshot_with_bbox(screenshot_with_bbox_path)
        self.memory.current_elements = elements
        # 3. decide concrete action by widget matching or marked image analysis
        action = self.decider.confirm_next_action(self.memory, action)
        self.memory.add_action(action)
        if action is None:
            self.state = "ERROR"
            self.report_self()
            return False
        # record resize ratio
        if self.device_manager.resize_ratio is None:
            self.device_manager.set_resize_ratio(resize_ratio)
        self.state = "EXECUTING"
        return False

    def _state_correcting(self) -> bool:
        last_action = self.memory.performed_actions[-1]
        if last_action["action-type"] == "back" and last_action["intent"] == "NEED-BACK":
            self.memory.remove_last_action()
            need_back = True
        else:
            need_back = False

        situation_number = 1 if self.match_error_count > 0 \
            else self.decider.issue_feedback(need_back)
        if situation_number is None:
            self.state = "ERROR"
            self.report_self()
            return False
        elif situation_number == 1:
            self.match_error_count += 1
            if self.match_error_count > 2:
                self.state = "FAILED"
                self.report_self()
                return False
            action = self.decider.rematch_next_action(self.memory)
        else:
            situation = self.issue_table[situation_number]
            self.decide_error_count += 1
            if self.decide_error_count > 2:
                self.state = "FAILED"
                self.report_self()
                return False
            action = self.decider.next_action(self.memory, correcting=True, situation=situation)
            if action is not None:
                action = self.decider.confirm_next_action(self.memory, action)

        if action is None:
            self.state = "ERROR"
            self.report_self()
            return False
        self.memory.remove_last_action()
        self.memory.add_action(action)
        self.state = "EXECUTING"
        return False
