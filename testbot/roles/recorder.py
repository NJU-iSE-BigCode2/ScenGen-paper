import os
import json
from typing import Any, Dict, Optional

from testbot.logger import logger
from testbot.llm import LLMChatManager
from testbot.memory import Memory
from testbot.utils import gen_timestamp


class TestRecorder:
    def __init__(self, chat_manager: LLMChatManager, base_dir: str):
        self.history_action = []
        self.chat_manager = chat_manager
        self.script_base_dir = os.path.join(base_dir, "data", "script")
        self.chat_base_dir = os.path.join(base_dir, "data", "chat")

    def record(self, action: Dict[str, Any], memory: Memory, require_widget: bool) -> None:
        action["screenshot"] = memory.current_screenshot if not require_widget \
            else memory.current_screenshot_with_bbox
        self.history_action.append(action.copy())

    def scripted(
            self,
            app_id: str,
            scenario_id: str,
            addition: Optional[Dict[str, Any]] = None,
            failed: bool = False,
            full_chat: bool = False,
    ) -> str:
        timestamp = gen_timestamp()
        if failed:
            script_file_name = f"{scenario_id}-{app_id}-{timestamp}-failed.json"
        else:
            script_file_name = f"{scenario_id}-{app_id}-{timestamp}.json"
        script_file_path = os.path.join(self.script_base_dir, script_file_name)
        script_content = {"actions": self.history_action}
        if addition is not None:
            script_content.update(addition)
        with open(script_file_path, "w", encoding="utf-8") as f:
            json.dump(script_content, f, indent=2)
        logger.info(f"Script Saved to {script_file_name}")
        if full_chat:
            chat_file_name = f"{scenario_id}-{app_id}-{timestamp}-chat.txt"
            chat_file_path = os.path.join(self.chat_base_dir, chat_file_name)
            self.chat_manager.refresh_context()
            chat_file_content = self.chat_manager.context_pool2string()
            with open(chat_file_path, "w", encoding="utf-8") as f:
                f.write(chat_file_content)
            logger.info(f"Chat Details Saved to {chat_file_name}")
        return script_file_path
