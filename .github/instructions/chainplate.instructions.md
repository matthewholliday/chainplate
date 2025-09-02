---
applyTo: '**'
---
# Project Overview
- This project is structured to facilitate the creation and execution of AI-driven workflows using XML configurations. The core components include:
  - `src/aixml/`: Contains the main logic for parsing XML and executing AI workflows.
  - `src/aixml/elements/`: Houses individual element implementations that define specific actions or controls within the workflow.
  - `src/aixml/services/`: Provides services such as CLI interactions to support workflow execution.
  - `src/aixml/helpers/`: Contains utility functions and classes to assist with various tasks.
  - `examples/`: Contains example XML files demonstrating various workflow configurations.
  - `tests/`: Contains unit tests to ensure code reliability and correctness.
  - `src/aixml/__main__.py`: The entry point for executing the AI workflows defined in XML files.
  - `src/aixml/ainode.py`: Defines the `AiNode` class, which represents nodes in the AI workflow tree and manages their execution.
  - `src/aixml/message.py`: Defines the `Message` class, which encapsulates the data passed between nodes during execution.
  - `src/aixml/modes.py`: Defines different modes of operation for the AI workflows. These include:
    - `Chat Mode`: For interactive chat-based workflows.
    - `Workflow Mode`: Invokes a single execution of the defined workflow.

# Unit Testing
- All unit tests should be placed in the `tests` directory at the root of the project. Use the `unittest` framework for writing and running tests. 
- All test classes should be prefixed with `Test` and all test methods should be prefixed with `test_`.
