from typing import Optional

from testbot.memory import Memory


def system_prompt_next_action(memory: Memory) -> str:
    system_prompt = (
        "You are a helpful assistant to guide a user "
        f"to accomplish the task **{memory.target_scenario}** "
        f"on a mobile application named {memory.app_name}.\n\n"
    )
    system_prompt += (
        "The basic information about the user is as follows:\n"
        f"{memory.describe_basic_info()}\n\n"
    ) if memory.describe_basic_info() is not None else ""
    system_prompt += (
        "The user can perform the following types of actions:\n"
        "- Touch a clickable widget (action-type: touch)\n"
        "- Fill in an editable widget (action-type: input)\n"
        "- Scroll up/down/left/right the screen to view more widgets (action-type: scroll)\n"
        "- Navigate back to the previous page (action-type: back)"
    )
    return system_prompt


def user_prompt_next_action(memory: Memory) -> str:
    prompt = ""
    if memory.performed_actions is None:
        prompt += "I have performed no actions.\n"
    else:
        prompt += (
            f"The actions I have performed are as follows:\n"
            f"{memory.describe_performed_actions()}\n"
        )
    prompt += (
        "And here is the screenshot of the current page.\n"
        "\n"
        "Please select the next suitable action to perform.\n"
        "\n"
        "Note that:\n"
        "1. Your decision should be flexible based on the page content,"
        " which means you can't only follow the logic to select next action.\n"
        "2. **input action** consists of touching the widget to set it focused and entering text."
        " So don't additionally perform **touch action** on editable widgets.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "1. Description of the current app state: "
        "<1 sentence, briefly in one line according to the provided screenshot and performed actions>\n"
        "2. Reasoning for the next action: "
        "<1 sentence reasoning the most logical action to take next on the current state>\n"
        "3. Description of the next action: "
        "<1 json object in one line with necessary keys `intent`, `action-type`"
        " and optional keys `target-widget`, `input-text`, `scroll-direction`>"
    )
    return prompt


def user_prompt_confirm_next_action() -> str:
    return (
        "This image displays the widget detection result of the current page's screenshot.\n"
        "Each widget is outlined in a green bounding box and"
        " labeled with a serial number in the upper left corner.\n"
        "\n"
        "Based on your decision, compare this image with the"
        " original screenshot to find the target widget.\n"
        "Note that if this action doesn't require a target widget"
        " or the target widget is missing, set it to -1.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "Widget: <1 json object with attribute `target-widget-number`>"
    )


def user_prompt_analyze_missing_widget() -> str:
    return (
        "Reflect on the action you selected,"
        " choose why the target widget is missing from the following options:\n"
        "1. Necessary preliminary action is required to"
        " bring about the appearance of the target widget.\n"
        "2. The target widget is not included in the detection result.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "Option: <1 json object with attribute `option-number`>\n"
        "Reason: <1 sentence, one line briefly giving reason to support your answer>"
    )


def user_prompt_confirm_input_action(target_widget_id: Optional[int] = None) -> str:
    if target_widget_id is not None:
        return (
            "This image displays the widget detection result of the current page's screenshot.\n"
            "Each widget is outlined in a green bounding box and"
            " labeled with a serial number in the upper left corner.\n"
            "\n"
            f"Based on your decision, I think the related target widget"
            f" is labeled {target_widget_id} in this image.\n"
            "\n"
            "For an input action, a touch to set the input field focused is necessary."
            " I want to 1) void touching the prompt text and"
            " 2) touch the space for text entering to set the input field focused."
            " However, the bounding box only contain prompt text at most cases."
            " Please tell me where, relative to the bounding box, I should touch.\n"
            "For example, if the bounding box has obvious blank space on the right of it,"
            " this undetected blank space is where the text will actually be entered,"
            " and I should touch it instead of the bounding box itself.\n"
            "\n"
            "=== Below is the template for your answer ===\n"
            "Position: <1 json object with attribute `position`,"
            " which can only take one of five values: 'up', 'left', 'down', 'right', or 'self'>\n"
            "Reason: <1 sentence, one line briefly giving reason to support your answer>"
        )
    else:
        return (
            "Since the target widget is missing, I need you to tell me "
            "the most possible location to touch and perform the input action. "
            "This location can be described in terms of 'position relative to a widget'.\n"
            "\n"
            "=== Below is the template for your answer ===\n"
            "Location: <1 json object with attribute `widget-number` and `position`,"
            " where the 'position' attribute has a finite set of possible values:"
            " 'up', 'left', 'down', and 'right'."
        )


def user_prompt_confirm_touch_action() -> str:
    return (
        "Since the target widget is missing, I need you to tell me "
        "the most possible location to perform the touch action. "
        "This location can be described in terms of 'position relative to a widget'.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "Location: <1 json object with attribute `widget-number` and `position`,"
        " where the 'position' attribute has a finite set of possible values:"
        " 'up', 'left', 'down', and 'right'."
    )


def user_prompt_modify_next_action(situation: str) -> str:
    return (
        "The action you described is not working.\n"
        f"The situation is: **{situation}**\n"
        "And you need to accordingly select a more suitable action to perform.\n"
        "Please re-observe the screenshot and modify your answer following the same template.\n"
        "\n"
        "=== As a reminder, below is the template for your answer ===\n"
        "1. Description of the current app state: "
        "<1 sentence, briefly in one line according to the provided screenshot and performed actions>\n"
        "2. Reasoning for the next action: "
        "<1 sentence reasoning the most logical action to take next on the current state>\n"
        "3. Description of the next action: "
        "<1 json object in one line with necessary keys `intent`, `action-type`"
        " and optional keys `target-widget`, `input-text`, `scroll-direction`>"
    )


def user_prompt_rematch_widget() -> str:
    return (
        "The target-widget-number you offered proves wrong.\n"
        "You made a mistake in matching the true target widget with its number.\n"
        "Please re-observe the screenshot and modify your answer following the same template."
    )


def user_prompt_fix_location() -> str:
    return (
        "The location you described proves wrong.\n"
        "I need a new description of the most possible location to perform the action.\n"
        "Please re-observe the screenshot and modify your answer following the same template."
    )


def user_prompt_analyze_situation(need_back: bool) -> str:
    task_prompt = "The execution result of the action you selected is "
    if need_back:
        task_prompt += "not task-oriented. The app page changed to an unrelated page.\n"
    else:
        task_prompt += "invalid. The app page didn't change.\n"
    task_prompt += (
        "I need you to analyze and choose a situation from the following options:\n"
        "1. The selected action is appropriate, but error occurred in matching"
        " target widget with its number, causing the app to not respond correctly.\n"
        "2. The selected action is appropriate, but necessary preliminary"
        " action was neglected, causing the app to not respond correctly.\n"
        "3. The selected action is appropriate, the error may arise from bug of the app.\n"
        "4. The selected action is inappropriate, because it doesn't correspond to the task scenario.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "Situation: <1 json object with attribute `situation-number`>\n"
        "Reason: <1 sentence, one line briefly giving reason to support your answer>"
    )
    return task_prompt
