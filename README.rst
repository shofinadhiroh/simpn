SimPN Thesis Extension Project
==============================

Overview
--------

This thesis project, developed by **Shofiyyah Nadhiroh**, extends the `SimPN`_ library to generate **synthetic event logs for educational purposes**. It demonstrates advanced process modeling using BPMN elements and introduces configurable process behaviors—such as **rework (self-loop and long rework), bottlenecks, and case-specific attributes**—to simulate realistic process scenarios. The simulation now supports **conditional behaviors** and the generation of **case attributes** (numerical, string, or boolean) within the event log.

.. _SimPN: https://github.com/bpogroup/simpn

Getting Started
---------------

### Prerequisites

- Python 3.x  
- `SimPN`_ (install via pip)  
- Other dependencies listed in ``requirements.txt``

### Installation

1. **Install SimPN**

   .. code-block:: bash

      pip install simpn

2. **Clone this Repository**

   .. code-block:: bash

      git clone <repository-url>
      cd <repository-folder>

3. **Install Dependencies**

   .. code-block:: bash

      pip install -r requirements.txt

Configuration
-------------

Simulation behavior is controlled through the ``config.json`` file. This includes:

- Rework scenarios (with conditions)
- Case attributes (numerical, string, or boolean)

### Example ``config.json``

.. code-block:: json

   {
     "rework": [
       {
         "activity": "review_application",
         "max_iteration": 1,
         "probability": 0.2,
         "condition": "loanType == 'personal'"
       }
     ],
     "long_rework": [
       {
         "trigger_activity": "pre_approval_check",
         "back_to": "review_application",
         "max_iteration": 1,
         "probability": 0.2,
         "condition": "loanType == 'personal'"
       }
     ],
     "case_attributes": {
       "requestedAmount": {
         "type": "numerical",
         "min": 1000,
         "max": 10000
       },
       "loanType": {
         "type": "string",
         "values": ["personal", "mortgage", "auto"]
       },
       "isUrgent": {
         "type": "boolean"
       }
     }
   }

Usage
-----

You can either use one of the predefined execution files (**recommended for quick setup**) or configure your own custom simulation.

### Option 1: Use a Predefined Execution File

Five example process scenarios are available:

- ``sequence.py``
- ``choice.py``
- ``choice2.py``
- ``parallel.py``
- ``mix.py``

Each file defines a different process structure. To run one, simply execute:

.. code-block:: bash

   python sequence.py

You can modify the process behavior and attributes by editing ``config.json``.

### Option 2: Configure Manually (Custom Setup)

Follow these steps to build and simulate your own process from scratch.

#### 1. Load Configuration and Generate Case Attributes

.. code-block:: python

   import json
   from random import uniform, choice
   from simpn.simulator import SimToken

   with open('config.json', 'r') as f:
       config = json.load(f)

   # Define start behavior to generate case attributes
   def start_behavior():
       attributes = {}
       for attr_name, attr_config in config.get("case_attributes", {}).items():
           attr_type = attr_config["type"]
           if attr_type == "numerical":
               value = uniform(attr_config["min"], attr_config["max"])
           elif attr_type == "string":
               value = choice(attr_config["values"])
           elif attr_type == "boolean":
               value = choice([True, False])
           else:
               raise ValueError(f"Unsupported attribute type: {attr_type}")
           attributes[attr_name] = value
       # Token format: (attributes, rework_counts)
       return [SimToken((attributes, {}))]

#### 2. Model the Process

Define your process using BPMN elements. You can refer to the ``test.py`` file for a full example. A typical process includes:

- A start event to initialize the simulation.
- Tasks such as ``review_application``, ``pre_approval_check``, and ``loan_approval``.
- An end event to complete the process.

#### 3. Configure Rework (Optional)

To simulate rework, include one or both of the following:

.. code-block:: python

   setup_rework(loan_process, config)
   setup_long_rework(loan_process, config)

- You may comment out any function you don't need.
- These inject conditional rework behavior based on the ``config.json`` file.

#### 4. Run the Simulation with the Enhanced Reporter

.. code-block:: python

   from custom_reporters import EnhancedEventLogReporter

   # Run the simulation with the enhanced reporter
   reporter = EnhancedEventLogReporter("choice.csv", config=config)
   loan_process.simulate(24*60, reporter)  # Simulate for 10 days (in minutes)
   reporter.close()

#### 5. Execute the File

.. code-block:: bash

   python your_script.py

The simulation will output a ``.csv`` event log containing:

- Case attributes
- Events
- Rework traces (if configured)

Code Structure
--------------

+--------------------------+-----------------------------------------------------+
| File                     | Description                                         |
+==========================+=====================================================+
| ``sequence.py``, etc.    | Simulation entry points with BPMN process models   |
+--------------------------+-----------------------------------------------------+
| ``config.json``          | Defines case attributes and rework behavior        |
+--------------------------+-----------------------------------------------------+
| ``rework.py``            | Implements ``setup_rework()`` and ``setup_long_rework()`` |
+--------------------------+-----------------------------------------------------+
| ``custom_reporters.py``  | Logs events and case data using EnhancedEventLogReporter |
+--------------------------+-----------------------------------------------------+

Extras
------

Let me know if you'd like to:

- Export the event log to ``.xes`` format
- Visualize results in **Disco** or **ProM**
- Generate sample event logs automatically for teaching or testing purposes

Happy simulating! 🧪📊
