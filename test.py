import os
import sys

from testbot.core import TestAgent
from testbot.device import Device, DeviceManager

base_dir = os.path.dirname(__file__)


def main(a_id, s_id) -> None:
    device = Device()
    dm = DeviceManager(device=device, base_dir=base_dir)
    agent = TestAgent(device_manager=dm, base_dir=base_dir)
    agent.initialize(app_id=a_id, scenario_id=s_id)
    print("Please open the app and direct it to the initial page of the scenario.")
    input("Press enter to start the test...")
    while agent.state != "FAILED" and agent.state != "END" and agent.state != "ERROR":
        agent.step()


if __name__ == "__main__":
    app_id, scenario_id = sys.argv[1], sys.argv[2]
    main(app_id, scenario_id)
