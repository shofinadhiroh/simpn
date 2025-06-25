SimPN
=====

SimPN is a Python library for BPMN‐style process simulation, with first‐class support for:

  - Enriching event logs with custom case attributes  
  - Modeling rework loops (self and long)  
  - Calculating and simulating resource bottlenecks  
  - Providing reusable templates for common workflow patterns  

Project Structure
-----------------

  ├── attr/            Custom‐attribute enrichment  
  ├── bottleneck/      Resource analysis & bottleneck simulation  
  ├── rework/          Self‐loop & long‐loop rework behavior  
  ├── templates/       Example BPMN process definitions  
  ├── config.json      Sample configuration for attributes, rework, bottlenecks  
  └── README.rst       This overview  

Quick Start
-----------

1. **Clone** the repo and install dependencies (e.g. ``pip install simpn``).  
2. **Edit** ``config.json`` to define your case attributes, rework rules, or bottleneck scenarios.  
3. **Write** a driver script that:
   - Imports the modules you need (``attr``, ``rework``, ``bottleneck``)  
   - Attaches behaviors to your ``BPMNStartEvent``  
   - Calls ``setup_rework(...)``, ``adjust_bottlenecks(...)``, etc.  
   - Uses ``EnhancedEventLogReporter`` to capture enriched logs  
4. **Run** your simulation::

       python run_simulation.py

5. **Analyze** the generated ``sequence.csv`` for deeper process insights.

For detailed instructions, see each sub‐folder’s README.
