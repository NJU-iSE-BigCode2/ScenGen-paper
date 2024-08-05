# ScenGen: LLM-guided Scenario-based GUI Testing

### Environment Setup

To set up the environment for this project, please follow the steps below:

1. **Python Version**: Ensure that your Python version is 3.9. You can check your Python version by running the following command in your terminal: `python --version`.
2. **Install Dependencies**: Use the `pip` package manager to install the necessary dependencies listed in the `requirements.txt` file. Run the following command in your project directory: `pip install -r requirements.txt`.
3. **OpenAI API Key**: This project requires a valid OpenAI API key to access models with vision capabilities. You need to set the API key as a system environment variable named `OPENAI_API_KEY`. 
4. **ADB Installation**: The system requires the Android Debug Bridge (ADB) tool to control Android devices via ADB commands. You can verify that ADB is correctly installed by running the following command: `adb --version`.

### Project Structure

The project's codebase is organized into the following directories and key files:

- **prompt folder**: This directory contains modules responsible for constructing prompts used for interactions with large language models. It includes predefined templates and functions for generating prompts dynamically.
- **roles folder**: This directory contains implementations of various agents involved in the project. Each agent has a specific role and functionality within the system, facilitating the orchestration and execution of tasks.
- **uied folder**: Built upon the project [UIED](https://github.com/MulongXie/UIED), this directory focuses on extracting GUI widgets using traditional computer vision algorithms and OCR models. The extracted widgets are used to support the operations of the Observer agent.
- **core.py**: This is the main file responsible for executing the core process of scenario-based automated GUI testing. It coordinates the different agents, orchestrating their actions to perform the necessary tests and interactions.
- **device.py**: This file handles the control and management of the devices under test. It includes functions to interact with the devices, send commands, and receive responses.
- **llm.py**: This file is responsible for interfacing with large language model services. It includes functions for making requests to the models and handling the responses, enabling the project to leverage the capabilities of LLMs.
- **memory.py**: This file implements the context memory required by the agents. It manages the storage and retrieval of information, allowing agents to maintain and utilize context across different interactions and sessions.
- **config.py**: This file handles the configuration settings of the project. It reads and manages configuration information, ensuring that all components have access to the necessary parameters and settings.

### Configuration and Execution

To configure and run the project, please follow these steps: (Suppose the project root directory is `/scengen`)

1. **Set Configuration Variables**:

   - `self.ROOT_INPUT` and `self.ROOT_OUTPUT` in `testbot/uied/CONFIG.py`  (recommended setting: `/scengen/data/input` and `/scengen/data/output`)

   - `self.output_root` in `testbot/uied/detect.py` (recommended setting: `/scengen/data/output`)

   - `self.model_folder` in `testbot/uied/detect_text/ocr.py` (recommended setting: `/scengen/testbot/uied/detect_text/inference/`)

2. **Add Configuration Information**:

   Add the configuration information for the apps and the test scenarios in `testbot/conf.json`. Ensure that the relevant apps are installed on the device under test.

   Here is an example configuration:

   ```json
   {
     "apps": [
       {
         "id": "A1",
         "name": "QQ Mail",
         "package": "com.tencent.androidqqmail",
         "launch-activity": "com.tencent.qqmail.launcher.desktop.LauncherActivity",
       },
       {
         "id": "A2",
         "name": "FairEmail",
         "package": "eu.faircode.email",
         "launch-activity": ".ActivityMain",
       }
     ],
     "scenarios": [
       {
         "id": "S1",
         "name": "send email",
         "description": "send an email to friend",
         "extra-info": {
           "friend's email": "example@example.com",
           "email subject": "example",
           "email content": "example"
         }
       },
       {
         "id": "S4",
         "name": "take photo",
         "description": "take a photo",
         "extra-info": {}
       }
     ]
   }
   ```

   The `extra-info` field is optional and can be added based on the actual testing needs.

   More details can be found in our demo `conf.json`.

3. Run the Project

   To execute the tests, run the `test.py` script with the appropriate APP ID and SCENARIO ID: `python test.py <APP-ID> <SCENARIO-ID>` (Replace `<APP-ID>` and `<SCENARIO-ID>` with the IDs you configured in `conf.json`)

