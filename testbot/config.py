import os
import json
from typing import Any, Dict, Tuple


def load_conf() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with open(os.path.join(os.path.dirname(__file__), "conf.json"), mode="r", encoding="utf-8") as f:
        conf_data = json.load(f)
    app_list = conf_data["apps"]
    scenario_list = conf_data["scenarios"]
    apps = {}
    for app in app_list:
        apps[app["id"]] = app
    scenarios = {}
    for scenario in scenario_list:
        scenarios[scenario["id"]] = scenario
    return apps, scenarios


APPS, SCENARIOS = load_conf()
