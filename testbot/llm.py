import base64
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

client = OpenAI()


# Function to encode the image
def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_content(
        message: Union[str, Dict[str, Any]],
) -> Union[str, List[Dict[str, Any]]]:
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        image = message.get("image")
        text = message.get("text")
        if image is None or text is None:
            raise TypeError(message)
        if isinstance(image, str):
            image = [image]

        user_content = [{"type": "text", "text": text}]
        for image_path in image:
            base64_image = encode_image(image_path)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        return user_content

    raise TypeError(message)


def build_messages(
        user_messages: List[Union[str, Dict[str, Any]]],
        system_message: Optional[str] = None,
        assistant_messages: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    messages = []
    if system_message is not None:
        messages.append({"role": "system", "content": system_message})
    if assistant_messages is None and len(user_messages) == 1:
        user_content = build_content(user_messages[0])
        messages.append({"role": "user", "content": user_content})
    elif assistant_messages is not None and len(user_messages) == len(assistant_messages) + 1:
        for i in range(len(assistant_messages)):
            user_content = build_content(user_messages[i])
            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": assistant_messages[i]})
        user_content = build_content(user_messages[-1])
        messages.append({"role": "user", "content": user_content})
    else:
        raise RuntimeError("Message Numbers Mismatched")
    return messages


class ChatContext:
    def __init__(
            self,
            user_messages: Optional[List[Union[str, Dict[str, Any]]]] = None,
            assistant_messages: Optional[List[str]] = None,
            system_message: Optional[str] = None,
    ):
        self.user_messages = user_messages
        self.assistant_messages = assistant_messages
        self.system_message = system_message
        self.history_storage = []

    def append_user_message(self, message: Union[str, Dict[str, Any]]) -> None:
        if self.user_messages is None:
            self.user_messages = []
        self.user_messages.append(message)

    def append_assistant_message(self, message: str) -> None:
        if self.assistant_messages is None:
            self.assistant_messages = []
        self.assistant_messages.append(message)

    def set_system_message(self, message: str) -> None:
        if self.system_message is None:
            self.system_message = message

    def copy_from(self, other: "ChatContext") -> None:
        self.user_messages = other.user_messages
        self.assistant_messages = other.assistant_messages
        self.system_message = other.system_message

    def messages(self) -> List[Dict[str, Any]]:
        if self.user_messages is not None:
            return build_messages(
                user_messages=self.user_messages,
                system_message=self.system_message,
                assistant_messages=self.assistant_messages,
            )
        raise RuntimeError("No User Message Found")

    def refresh(self) -> None:
        if self.user_messages is not None and self.assistant_messages is not None:
            assert len(self.user_messages) == len(self.assistant_messages)
            self.history_storage.append((
                self.system_message,
                self.user_messages,
                self.assistant_messages
            ))
        self.system_message = None
        self.user_messages = None
        self.assistant_messages = None

    def __str__(self):
        context_str = ""
        for i, context in enumerate(self.history_storage):
            context_str += f"CONTEXT-{i}:\n"
            system, user, assistant = context
            if system is not None:
                context_str += f"- SYS: ```{system}```\n"
            for j in range(len(user)):
                if isinstance(user[j], dict):
                    txt_prompt = user[j]["text"]
                    img_prompt = user[j]["image"]
                    context_str += f"- USER: ```{img_prompt}\n{txt_prompt}```\n"
                else:
                    context_str += f"- USER: ```{user[j]}```\n"
                context_str += f"- ASSI: ```{assistant[j]}```\n"
            context_str += "\n"
        return context_str.strip()


class LLMChatManager:
    def __init__(self):
        self.action_decision_context = ChatContext()
        self.loading_check_context = ChatContext()
        self.ending_check_context = ChatContext()
        self.visual_change_check_context = ChatContext()
        self.valid_change_check_context = ChatContext()
        self.temporary_context = ChatContext()
        self.context_pool: Dict[str, ChatContext] = {
            "action-decision": self.action_decision_context,
            "loading-check": self.loading_check_context,
            "ending-check": self.ending_check_context,
            "visual-change-check": self.visual_change_check_context,
            "valid-change-check": self.valid_change_check_context,
            "temporary": self.temporary_context,
        }

    def refresh_context(self) -> None:
        for context in self.context_pool.values():
            context.refresh()

    def context_pool2string(self) -> str:
        context_pool_str = ""
        for stage, context in self.context_pool.items():
            context_pool_str += f"**STAGE {stage}**\n"
            context_pool_str += f"{str(context)}\n\n\n"
        return context_pool_str.strip()

    def get_response(
            self,
            stage: str,
            model: str,
            prompt: Union[str, Dict[str, Any]],
            system: Optional[str] = None,
            max_tokens: int = 1024,
            temperature: float = 0.0,
    ):
        target_context = self.context_pool[stage]
        target_context.append_user_message(prompt)
        if system is not None:
            target_context.set_system_message(system)
        messages = target_context.messages()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        prompt_cost = response.usage.prompt_tokens
        response_cost = response.usage.completion_tokens
        response_content = response.choices[0].message.content
        target_context.append_assistant_message(response_content)
        return response_content, prompt_cost, response_cost
