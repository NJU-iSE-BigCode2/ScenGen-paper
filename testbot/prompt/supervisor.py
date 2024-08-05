from typing import Tuple

from testbot.memory import Memory


def system_prompt_loading_check() -> str:
    return (
        "You are a professional assistant in GUI testing and image comprehension."
    )


def system_prompt_ending_check(memory: Memory) -> str:
    system_prompt = (
        "You are a helpful assistant to guide a user "
        f"to accomplish the task **{memory.target_scenario}** "
        f"on a mobile application named {memory.app_name}.\n\n"
    )
    system_prompt += (
        "The basic information about the user is as follows:\n"
        f"{memory.describe_basic_info()}\n\n"
    ) if memory.describe_basic_info() is not None else ""
    return system_prompt.strip()


def system_prompt_effect_check() -> str:
    return (
        "You are a helpful assistant who can interpret two consecutive GUI screens "
        "before and after a user's action and explain the result of the action to the user."
    )


def user_prompt_loading_check() -> str:
    return (
        "Here is the screenshot of the current page during a GUI test of a mobile app.\n"
        "Please determine whether the page is undergoing a loading process. "
        "(e.g., showing a blank screen, displaying \"loading\" or indicating network latency).\n"
        "=== Below is the template for your answer ===\n"
        "answer: T/F —— If the current page is in a loading state, return T; otherwise, return F\n"
        "reason: <1 sentence briefly giving reasons to support your answer>"
    )


def user_prompt_ending_check(memory: Memory) -> Tuple[str, str, str, str]:
    task_prompt = f"My test task is **{memory.target_scenario}**\n"
    if memory.basic_info is not None \
            and memory.basic_info.get("requirement") is not None:
        extra_requirement = memory.basic_info["requirement"]
        task_prompt += f"Requirement: {extra_requirement}\n"
    task_prompt += (
        "The actions I have performed are as follows:\n"
        f"{memory.describe_performed_actions()}\n"
        "\n"
        "Based on the screenshots and the performed actions (especially the latest"
        " performed action), please tell me whether the test task has been completed.\n"
        "\n"
        "Note that, if the last performed action is expected to complete the task and the"
        " current page is similar to the initial page, the task should be deemed as completed.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "answer: T/F —— If the task has been completed, return T; otherwise, return F.\n"
        "reason: <1 sentence briefly giving reasons to support your answer>"
    )
    prev_screenshot_prompt = "This is the previous GUI screen."
    curr_screenshot_prompt = "This is the current GUI screen."
    init_screenshot_prompt = "This is the initial GUI screen."
    return task_prompt, prev_screenshot_prompt, curr_screenshot_prompt, init_screenshot_prompt


def user_prompt_page_change_check() -> Tuple[str, str, str]:
    task_prompt = (
        "Now, I will give you two consecutive APP GUI screens before and after my action. "
        "Please judge whether my action has successfully caused the change of the APP.\n"
        "\n"
        "Notice:\n"
        "1.In the screenshots, changes in elements such as time, battery level, network icons,"
        " that are unrelated with the APP itself, cannot be regarded as successful change caused by my action."
        "2.Rotating contents always have Indicator Points or Thumbnails:"
        " In order to let the user know how much content is in rotation and which item is currently"
        " being displayed, the GUI will usually contain a series of indicator points or thumbnails."
        " These indicator points are usually located below or above the rotating content, and the point that"
        " corresponds to the content currently being displayed may be displayed in a different colour or style.\n"
        "3.In some apps, there are always rotating contents changing at regular intervals. So, when you see"
        " different pictures or banners in the screens, you need to determine carefully if the changed element"
        " is rotational content. If only the rotational content has changed in the page,"
        " it cannot be judged as a valid change. And you should answer 'NO'.\n"
        "4.If the page changes to another APP, it can be judged as a successful change.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "answer: YES/NO"
        " -- if my action has successfully caused the change of the APP, return YES; otherwise, return NO.\n"
        "reason: <1 sentence briefly giving reasons to support your answer>"
    )
    prev_screenshot_prompt = "This is the previous GUI screen."
    curr_screenshot_prompt = "This is the current GUI screen."
    return task_prompt, prev_screenshot_prompt, curr_screenshot_prompt


def user_prompt_valid_change_check(memory: Memory) -> Tuple[str, str, str, str]:
    task_prompt = (
        f"I have performed action **{memory.describe_performed_action()}** during the"
        f" task scenario **{memory.target_scenario}** in the app {memory.app_name}.\n"
        "I'll give you two consecutive app GUI screenshots before and after my action,"
        " and the initial screenshot of the app.\n"
        "Please determine whether the app has correctly responded to my action.\n"
        "\n"
        "Notice:\n"
        "1. The basis of your judgement is changes to the current page relative to the previous page.\n"
        "2. If this action may be the last action to complete the task scenario, current page may become"
        " similar to initial page. This should be considered as a correct response of the app.\n"
        "3. If this action doesn't directly work but triggers possible further confirmation dialog,"
        " this should be considered as a correct response of the app.\n"
        "4. If this action doesn't directly work but indicates further related actions I should perform,"
        " this should be considered as a correct response of the app.\n"
        "5. If the type this action is `input` and the text has been entered in the right place,"
        " this should be considered as a correct response of the app.\n"
        "\n"
        "=== Below is the template for your answer ===\n"
        "answer: YES/NO"
        " -- if the change in the GUI screen is as expected under the"
        " performed action and the task scenario, return YES; otherwise, return NO.\n"
        "reason: <1 sentence briefly giving reasons to support your answer>"
    )
    prev_screenshot_prompt = "This is the previous GUI screen."
    curr_screenshot_prompt = "This is the current GUI screen."
    init_screenshot_prompt = "This is the initial GUI screen."
    return task_prompt, prev_screenshot_prompt, curr_screenshot_prompt, init_screenshot_prompt
