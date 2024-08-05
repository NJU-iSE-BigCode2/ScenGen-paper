from typing import Any, Dict, Optional

from testbot.llm import LLMChatManager
from testbot.logger import logger
from testbot.memory import Memory
from testbot.prompt.decider import (
    system_prompt_next_action,
    user_prompt_rematch_widget,
    user_prompt_confirm_input_action,
    user_prompt_next_action,
    user_prompt_modify_next_action,
    user_prompt_confirm_touch_action,
    user_prompt_confirm_next_action,
    user_prompt_fix_location,
    user_prompt_analyze_situation,
    user_prompt_analyze_missing_widget
)
from testbot.utils import (
    extract_json,
    remove_punctuation,
    literally_related
)


class ActionDecider:
    def __init__(self, chat_manager: LLMChatManager):
        self.chat_manager = chat_manager
        self.stage = "action-decision"
        self.enable_text_match = True

    def next_action(
            self,
            memory: Memory,
            correcting: bool = False,
            situation: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not correcting:
            sys_prompt = system_prompt_next_action(memory=memory)
            user_prompt = user_prompt_next_action(memory=memory)
            user_message = {"text": user_prompt, "image": memory.current_screenshot}
            self.chat_manager.context_pool[self.stage].refresh()
            logger.info("Deciding Next Action")
        else:
            assert situation is not None
            sys_prompt = None
            user_message = user_prompt_modify_next_action(situation)
            logger.info("Re-Deciding Next Action")

        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage,
            model="gpt-4-vision-preview",
            prompt=user_message,
            system=sys_prompt,
        )
        logger.info("Action Decision Received.")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        action = extract_json(response)
        if action is None \
                or action.get("intent") is None \
                or action.get("action-type") is None:
            logger.error("No Valid Action Found")
            return None

        logger.info("Action Decision Parsed.")
        return action

    def confirm_next_action(
            self,
            memory: Memory,
            action: Dict[str, Any],
            repeat_times: int = 0,
    ) -> Optional[Dict[str, Any]]:
        if repeat_times > 2:
            logger.error("Repeat Confirming Too Many Times")
            return None

        # directly return `back` and `scroll` action
        if action["action-type"] == "back" or action["action-type"] == "scroll":
            logger.info(f"Action {action['action-type']} requires no target widget")
            action["target-widget"] = None
            return action

        # action-type: input / touch
        # try to match target widget by text
        matched_element = None
        if action.get("target-widget") is not None and self.enable_text_match:
            for element in memory.current_elements:
                if element.get("text_content") is not None:
                    ocr_text = element.get("text_content").lower()
                    ocr_text = remove_punctuation(ocr_text)
                    wid_desc = action["target-widget"].lower()
                    wid_desc = remove_punctuation(wid_desc)
                    if literally_related(ocr_text, wid_desc):
                        matched_element = element
                        break
        if matched_element is not None:
            # successfully matched
            matched_element["description"] = action["target-widget"]
            action["target-widget"] = matched_element
            logger.info("Target Widget Found By Text Matching")
            # add match context
            user_prompt = user_prompt_confirm_next_action()
            user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
            self.chat_manager.context_pool[self.stage].append_user_message(user_message)
            self.chat_manager.context_pool[self.stage].append_assistant_message(
                f"Widget: {{\"target-widget-number\": {matched_element['id']}}}"
            )
            # confirm touch position for input action
            if action["action-type"] == "input":
                w_id = action["target-widget"]["id"]
                user_prompt = user_prompt_confirm_input_action(w_id)
                user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
                self.chat_manager.context_pool["temporary"].refresh()
                self.chat_manager.context_pool["temporary"].copy_from(
                    self.chat_manager.context_pool[self.stage]
                )

                logger.info("Confirming Input Location")
                response, p_usage, r_usage = self.chat_manager.get_response(
                    stage="temporary",
                    model="gpt-4-vision-preview",
                    prompt=user_message,
                )
                logger.info("Confirm Result Received")
                logger.debug(f"Response: ```{response}```")

                position = extract_json(response)
                if position is None \
                        or position.get("position") is None \
                        or position["position"] not in ("up", "down", "left", "right", "self"):
                    logger.warning("No Valid Position Confirmed & Use Default")
                    action["position"] = "self"
                else:
                    action["position"] = position["position"]
            return action

        # try to match target widget by vision (gpt4-v)
        user_prompt = user_prompt_confirm_next_action()
        user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
        logger.info("Querying Target Widget")
        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage,
            model="gpt-4-vision-preview",
            prompt=user_message,
        )
        logger.info("Query Result Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        # extract widget number
        widget = extract_json(response)
        if widget is None or widget.get("target-widget-number") is None:
            logger.error("No Widget Number Found")
            return None

        # no widget matched, predict location based on existing widgets
        if int(widget["target-widget-number"]) == -1:
            logger.warning("No Target Widget Detected")
            user_message = user_prompt_analyze_missing_widget()
            self.chat_manager.context_pool["temporary"].refresh()
            self.chat_manager.context_pool["temporary"].copy_from(
                self.chat_manager.context_pool[self.stage]
            )
            logger.info("Analyzing Missing Target Widget")
            response, p_usage, r_usage = self.chat_manager.get_response(
                stage="temporary",
                model="gpt-4-vision-preview",
                prompt=user_message,
            )
            logger.info("Analysis Result Received")
            logger.info(f"Token Cost: {p_usage} + {r_usage}")
            logger.debug(f"Response: ```{response}```")
            option = extract_json(response)
            if option is None \
                    or option.get("option-number") is None \
                    or option["option-number"] not in (1, 2):
                logger.error("No Valid Option Found")
                return None
            option_num = option['option-number']
            logger.info(f"Option Number Extracted: {option_num}")
            if option_num == 1:
                action = self.next_action(
                    memory,
                    correcting=True,
                    situation=(
                        "necessary preliminary action was neglected"
                        " causing the app to not respond correctly"
                    )
                )
                return self.confirm_next_action(memory, action, repeat_times + 1)

            if action["action-type"] == "input":
                user_message = user_prompt_confirm_input_action()
            elif action["action-type"] == "touch":
                user_message = user_prompt_confirm_touch_action()
            else:
                logger.error(f"Invalid Action Type: {action['action-type']}")
                return None
            # confirm where to touch
            logger.info("Querying Possible Location")
            response, p_usage, r_usage = self.chat_manager.get_response(
                stage="action-decision",
                model="gpt-4-vision-preview",
                prompt=user_message,
            )
            logger.info("Possible Location Received")
            logger.info(f"Token Cost: {p_usage} + {r_usage}")
            logger.debug(f"Response: ```{response}```")
            # extract location description
            location = extract_json(response)
            if location is None \
                    or location.get("position") is None \
                    or location.get("widget-number") is None \
                    or location["position"] not in ("up", "down", "left", "right"):
                logger.error("No Valid Location Clarified")
                return None
            # get matched widget in location description
            for element in memory.current_elements:
                if element["id"] == int(location["widget-number"]):
                    action["target-widget"] = element
                    action["target-widget"]["id"] = -1
                    if action["action-type"] == "input":
                        action["target-widget"]["description"] = "blank_field"
                    else:
                        action["target-widget"]["description"] = "undetected_button"
                    break
            action["position"] = location["position"]
            return action

        # widget matched, get matched widget
        for element in memory.current_elements:
            if element["id"] == int(widget["target-widget-number"]):
                if action.get("target-widget") is not None:
                    element["description"] = action["target-widget"]
                else:
                    element["description"] = "target widget"
                action["target-widget"] = element
                logger.info("Target Widget Found By Vision")
                break
        # confirm touch position for input action
        if action["action-type"] == "input":
            w_id = action["target-widget"]["id"]
            user_prompt = user_prompt_confirm_input_action(w_id)
            user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
            self.chat_manager.context_pool["temporary"].refresh()
            self.chat_manager.context_pool["temporary"].copy_from(
                self.chat_manager.context_pool[self.stage]
            )

            logger.info("Confirming Input Location")
            response, p_usage, r_usage = self.chat_manager.get_response(
                stage="temporary",
                model="gpt-4-vision-preview",
                prompt=user_message,
            )
            logger.info("Confirm Result Received")
            logger.info(f"Token Cost: {p_usage} + {r_usage}")
            logger.debug(f"Response: ```{response}```")

            # extract position description
            position = extract_json(response)
            if position is None \
                    or position.get("position") is None \
                    or position["position"] not in ("up", "down", "left", "right", "self"):
                logger.warning("No Valid Position Confirmed & Use Default")
                action["position"] = "self"
            else:
                action["position"] = position["position"]
        return action

    def rematch_next_action(self, memory: Memory) -> Optional[Dict[str, Any]]:
        action = memory.performed_actions[-1]
        if action["target-widget"]["id"] != -1:
            user_message = user_prompt_rematch_widget()

            logger.info("Rematching Target Widget")
            response, p_usage, r_usage = self.chat_manager.get_response(
                stage=self.stage,
                model="gpt-4-vision-preview",
                prompt=user_message,
            )
            logger.info("Rematch Result Received")
            logger.info(f"Token Cost: {p_usage} + {r_usage}")
            logger.debug(f"Response: ```{response}```")

            widget = extract_json(response)
            if widget is None or widget.get("target-widget-number") is None:
                logger.error("No Widget Number Found")
                return None

            # no widget matched, predict location
            if int(widget["target-widget-number"]) == -1:
                logger.warning("No Widget Rematched")
                if action["action-type"] == "input":
                    user_message = user_prompt_confirm_input_action()
                elif action["action-type"] == "touch":
                    user_message = user_prompt_confirm_touch_action()
                else:
                    logger.error(f"Invalid Action Type: {action['action-type']}")
                    return None
                # confirm where to touch
                logger.info("Querying Possible Location")
                response, p_usage, r_usage = self.chat_manager.get_response(
                    stage="action-decision",
                    model="gpt-4-vision-preview",
                    prompt=user_message,
                )
                logger.info("Possible Location Received")
                logger.info(f"Token Cost: {p_usage} + {r_usage}")
                logger.debug(f"Response: ```{response}```")
                # extract location description
                location = extract_json(response)
                if location is None \
                        or location.get("position") is None \
                        or location.get("widget-number") is None \
                        or location["position"] not in ("up", "down", "left", "right"):
                    logger.error("No Valid Location Clarified")
                    return None
                # get matched widget in location description
                for element in memory.current_elements:
                    if element["id"] == int(location["widget-number"]):
                        action["target-widget"] = element
                        action["target-widget"]["id"] = -1
                        if action["action-type"] == "input":
                            action["target-widget"]["description"] = "blank_field"
                        else:
                            action["target-widget"]["description"] = "undetected_button"
                        break
                action["position"] = location["position"]
                return action

            # widget matched, get matched widget
            for element in memory.current_elements:
                if element["id"] == int(widget["target-widget-number"]):
                    if action["target-widget"].get("description") is not None:
                        widget_desc = action["target-widget"]["description"]
                        action["target-widget"] = element
                        action["target-widget"]["description"] = widget_desc
                    else:
                        action["target-widget"] = element
                        action["target-widget"]["description"] = "target widget"
                    logger.info("Target Widget Found By Vision")
                    break

            # confirm touch position for input action
            if action["action-type"] == "input":
                w_id = action["target-widget"]["id"]
                user_prompt = user_prompt_confirm_input_action(w_id)
                user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
                self.chat_manager.context_pool["temporary"].refresh()
                self.chat_manager.context_pool["temporary"].copy_from(
                    self.chat_manager.context_pool[self.stage]
                )

                logger.info("Confirming Input Location")
                response, p_usage, r_usage = self.chat_manager.get_response(
                    stage="temporary",
                    model="gpt-4-vision-preview",
                    prompt=user_message,
                )
                logger.info("Confirm Result Received")
                logger.info(f"Token Cost: {p_usage} + {r_usage}")
                logger.debug(f"Response: ```{response}```")

                position = extract_json(response)
                if position is None \
                        or position.get("position") is None \
                        or position["position"] not in ("up", "down", "left", "right", "self"):
                    logger.warning("No Valid Position Confirmed & Use Default")
                    action["position"] = "self"
                else:
                    action["position"] = position["position"]
            return action
        else:
            user_message = user_prompt_fix_location()

            logger.info("Re-predicting Target Widget Location")
            response, p_usage, r_usage = self.chat_manager.get_response(
                stage=self.stage,
                model="gpt-4-vision-preview",
                prompt=user_message,
            )
            logger.info("Prediction Result Received")
            logger.info(f"Token Cost: {p_usage} + {r_usage}")
            logger.debug(f"Response: ```{response}```")

            location = extract_json(response)
            if location is None \
                    or location.get("position") is None \
                    or location.get("widget-number") is None \
                    or location["position"] not in ("up", "down", "left", "right"):
                logger.error("No Valid Location Clarified")
                return None

            for element in memory.current_elements:
                if element["id"] == int(location["widget-number"]):
                    action["target-widget"] = element
                    action["target-widget"]["id"] = -1
                    if action["action-type"] == "input":
                        action["target-widget"]["description"] = "blank_field"
                    else:
                        action["target-widget"]["description"] = "undetected_button"
                    break
            action["position"] = location["position"]
            return action

    def issue_feedback(self, need_back: bool) -> Optional[int]:
        self.chat_manager.context_pool["temporary"].refresh()
        self.chat_manager.context_pool["temporary"].copy_from(
            self.chat_manager.context_pool[self.stage]
        )
        user_prompt = user_prompt_analyze_situation(need_back)

        logger.info("Querying Situation")
        response, p_usage, r_usage = self.chat_manager.get_response(
            stage="temporary",
            model="gpt-4-vision-preview",
            prompt=user_prompt,
        )
        logger.info("Situation Feedback Received.")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        situation = extract_json(response)
        if situation is None \
                or situation.get("situation-number") is None \
                or situation["situation-number"] not in (1, 2, 3, 4):
            logger.error("No Valid Action Found")
            return None
        logger.info(f"Situation Number Extracted: {situation['situation-number']}")
        return situation["situation-number"]
