import json
import time
from typing import Any, Dict, List, Optional


def gen_timestamp() -> str:
    """Generate timestamp"""
    timestamp = int(time.time())
    return str(timestamp)


def extract_json(s: str) -> Optional[Dict[str, Any]]:
    """Extract json from string"""
    print_len_limit = min(len(s), 20)
    stack = []
    json_start_index = None
    for i, char in enumerate(s):
        if char == '{':
            stack.append(char)
            if len(stack) == 1:
                json_start_index = i
        elif char == '}':
            if stack:
                stack.pop()
                if not stack and json_start_index is not None:
                    json_string = s[json_start_index:i + 1]
                    try:
                        return json.loads(json_string)
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON Object in ```{s[:print_len_limit]}```")
                        return None
    print(f"Error: No JSON Object found in ```{s[:print_len_limit]}```")
    return None


def remove_punctuation(s: str, more_punc: Optional[List[str]] = None) -> str:
    """Remove punctuation marks from string"""
    punctuation = [',', '.', ':', ';', '_']
    if more_punc is not None:
        punctuation.extend(more_punc)
    for char in punctuation:
        s = s.replace(char, ' ')
    return s.strip()


def literally_related(s1: str, s2: str) -> bool:
    s1 = s1.lower()
    s2 = s2.lower()
    if not s1.startswith(s2) or not s2.startswith(s1):
        return False

    if s1.strip() == "" or s2.strip() == "":
        return False

    s1_frags = s1.strip().split(" ")
    s2_frags = s2.strip().split(" ")
    if s2.startswith(s1):
        for frag in s1_frags:
            if len(frag) > 0 and frag not in s2_frags:
                return False
        return True

    if s1.startswith(s2):
        for frag in s2_frags:
            if len(frag) > 0 and frag not in s1_frags:
                return False
        return True

