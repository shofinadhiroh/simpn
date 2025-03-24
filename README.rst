SimPN Thesis Extension Project
==============================

Overview
--------

This thesis project, by Shofiyyah Nadhiroh, extends the SimPN library to generate synthetic event logs for educational purposes. It demonstrates advanced process modeling using BPMN elements and introduces configurable process behaviors—such as rework (self-loop and long rework), bottlenecks, and other modifications—to simulate realistic process scenarios. In addition, the simulation now supports adding configurable case attributes (numerical, string, or boolean) to the event log.

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

- Python 3.x
- `SimPN Library <https://github.com/bpogroup/simpn/tree/master>`_ (install via pip)
- Other Python dependencies as required (see ``requirements.txt``)

Installation
~~~~~~~~~~~~

1. **Install SimPN:**

   Install the SimPN library using pip::

      pip install simpn

2. **Clone the Repository:**

   .. code-block:: bash

      git clone <repository-url>
      cd <repository-folder>

3. **Install Dependencies:**

   .. code-block:: bash

      pip install -r requirements.txt

Configuration
~~~~~~~~~~~~~

The simulation uses ``config.json`` to control various process behaviors and to configure case attributes that will be added to the event log. For example, you can specify conditions for rework or introduce bottlenecks, as well as define attributes (e.g., numerical, string, boolean) to be generated for each case:

.. code-block:: json

   {
     "rework": [
       {
         "activity": "review_application",
         "max_iteration": 1,
         "probability": 0.2
       }
     ],
     "long_rework": [
       {
         "trigger_activity": "pre_approval_check",
         "back_to": "review_application",
         "max_iteration": 1,
         "probability": 0.2
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
~~~~~

1. **Model the Process:**

   Define your process using BPMN elements. See the ``test.py`` file for an example that includes:

   - A start event to initialize the simulation.
   - Tasks such as ``review_application``, ``pre_approval_check``, and ``loan_approval``.
   - An end event to complete the process.

2. **Configure Process Behaviors and Case Attributes:**

   Load the configuration and set up behaviors using:

.. code-block:: python

   with open('config.json', 'r') as f:
       config = json.load(f)
   setup_rework(shop, config)        # Configurable self-loop rework or other behaviors
   setup_long_rework(shop, config)   # Configurable long rework or other process modifications

   In addition, case attributes (e.g., requestedAmount, loanType, isUrgent) will be generated when a case starts and included in the event log.

3. **Run the Simulation with the Enhanced Reporter:**

   The simulation uses an enhanced reporter to log events along with the configured case attributes. Execute the simulation by running::

      python test.py

Code Structure
~~~~~~~~~~~~~~

- **test.py:** Main simulation code, including process definition and execution.
- **config.json:** Configuration file for process behaviors and case attributes.
- **rework.py:** Implements functions (e.g., ``setup_rework`` and ``setup_long_rework``) to inject customizable process behaviors into the simulation.
- **custom_reporters.py:** Contains the ``EnhancedEventLogReporter``, which logs events along with additional case attributes.
