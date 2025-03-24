SimPN Thesis Extension Project
==============================

Overview
--------

This thesis project, by Shofiyyah Nadhiroh, extends the SimPN library to generate synthetic event logs for educational purposes. It demonstrates advanced process modeling using BPMN elements and introduces configurable process behaviors—such as rework (self-loop and long rework), bottlenecks, and other modifications—to simulate realistic process scenarios.

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

The simulation uses ``config.json`` to control various process behaviors. For instance, you can specify conditions for rework or introduce bottlenecks by adjusting parameters in the configuration file:

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
     ]
   }

Usage
~~~~~

1. **Model the Process:**

   Define your process using BPMN elements. See the ``test.py`` file for an example that includes:
   
   - A start event to initialize the simulation.
   - Tasks such as ``review_application``, ``pre_approval_check``, and ``loan_approval``.
   - An end event to complete the process.

2. **Configure Process Behaviors:**

   Load the configuration and set up behaviors using:

.. code-block:: python

   with open('config.json', 'r') as f:
       config = json.load(f)
   setup_rework(shop, config)        # Configurable self-loop rework or other behaviors
   setup_long_rework(shop, config)   # Configurable long rework or other process modifications

   The functions in ``rework.py`` dynamically add decision events to determine whether a token should re-enter a process step or proceed.

3. **Run the Simulation:**

   Execute the simulation by running::

      python test.py

Code Structure
~~~~~~~~~~~~~~

- **test.py:** Main simulation code, including process definition and execution.
- **config.json:** Configuration file for process behaviors.
- **rework.py:** Implements functions (e.g., ``setup_rework`` and ``setup_long_rework``) to inject customizable process behaviors into the simulation.
