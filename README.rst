SimPN Thesis Extension Project
==============================

Overview
--------

This thesis project, developed by **Shofiyyah Nadhiroh**, extends the `SimPN <https://github.com/bpogroup/simpn>`_ library to generate **synthetic event logs for educational purposes**. It demonstrates advanced process modeling using BPMN elements and introduces configurable process behaviors—such as **rework (self-loop and long rework), bottlenecks, and case-specific attributes**—to simulate realistic process scenarios. The simulation now supports **conditional behaviors** and the generation of **case attributes** (numerical, string, or boolean) within the event log.

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
