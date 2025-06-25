Overview
--------

This thesis project, developed by **Shofiyyah Nadhiroh**, extends the `SimPN <https://github.com/bpogroup/simpn>`_ library to generate **synthetic event logs for educational purposes**. The goal is to help educators and students better understand business processes and process mining concepts.

The project introduces **configurable process behaviors** that simulate realistic scenarios using BPMN modeling elements. Key supported features include:

- **Rework**: self-loop and long rework behavior, with conditional triggers
- **Bottlenecks**: time-based resource shortages and optimal resource calculation
- **Case Attributes**: generation of per-case metadata (e.g., loan type, amount, urgency)
- **Resource Constraints**: control which resources may execute specific tasks

All simulation outputs are stored in enriched CSV logs

Project Structure
-----------------

.. code-block:: text

   ├── attr/             # Custom case attribute generation
   │   ├── case_attributes.py
   │   ├── custom_reporters.py  # Logs enriched event data
   │   ├── config.json       # Sample configuration for case attributes
   │   └── README.rst
   │
   ├── bottleneck/       # Bottleneck simulation: resource shortages, constraints
   │   ├── resource_calculator.py
   │   ├── bottleneck_manager.py
   │   ├── resource_constraints.py
   │   ├── task_constraints.py
   │   └── README.rst
   │
   ├── rework/           # Rework behavior: self-loop and long rework
   │   ├── rework.py
   │   ├── config.json
   │   └── README.rst
   │
   ├── templates/        # Example BPMN process definitions
   │
   └── README.rst        # This overview

Quick Start
-----------

1. **Clone** the repo and install dependencies (e.g., ``pip install simpn``).

2. **Edit** ``config.json`` to define your case attributes, rework rules, or bottleneck scenarios.

3. **Write** a driver script that:

   - Imports the modules you need (``attr``, ``rework``, ``bottleneck``)
   - Defines the BPMN process using ``BPMNStartEvent``, ``BPMNTask``, etc. You can copy the model from the template folder or create your own from scratch.
   - Calls one or more configuration functions:
     ``setup_rework(...)``, ``adjust_bottlenecks(...)``, or ``apply_resource_constraints(...)``
   - Uses ``EnhancedEventLogReporter`` to capture enriched logs

4. **Run** your simulation:

   .. code-block:: bash

      python run_simulation.py

5. **Analyze** the generated ``sequence.csv`` or any output CSV file for deeper process insights.

For detailed instructions, see each sub-folder’s ``README.rst``.
