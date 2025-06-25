Modelling and Simulating Rework
===============================

The ``rework`` package enables you to inject both **self‐loop** and **long‐loop** rework behavior  
into your BPMN simulations, including conditional rules based on attributes, resources, or time windows.

Features
--------

- **Self‐Loop Rework**: repeat the same activity  
- **Long‐Loop Rework**: jump back to an earlier activity  
- **Conditional Rules**: apply only when case attributes, resources, or time windows match  

Configuration (``config.json``)
-------------------------------

Self‐Loop example::

   "rework": [
     {
       "activity":      "credit_check",
       "max_iteration": 1,
       "probability":   0.5,
       "condition":     "loanType == 'personal'"
     }
   ]

Long‐Loop example::

   "long_rework": [
     {
       "trigger_activity": "credit_check",
       "back_to":          "review_application",
       "max_iteration":    1,
       "probability":      0.5,
       "condition":        "loanType == 'personal'"
     }
   ]
Usage
-----

1. **Import the utilities** at the top of your script::

       from attr.case_attributes import start_behavior
       from attr.custom_reporters import EnhancedEventLogReporter
       from rework.rework import setup_rework, setup_long_rework
       import json

2. **Load your configuration**::

       import json
       with open("config.json") as f:
           config = json.load(f)

3. **Ensure case attributes are added on start**::
       
      BPMNStartEvent(
           loan_process,
           [], [waiting],
           "application_received",
           lambda: exp(1/20),
           behavior=lambda: start_behavior(loan_process)
       )
      
4. **Activate rework**::
       
       setup_rework(loan_process, config)
       setup_long_rework(loan_process, config)

5. **Activate rework**::

      reporter = EnhancedEventLogReporter("sequence.csv", config=config, sim_problem=loan_process)
      loan_process.simulate(24*60*10, reporter)
      reporter.close()

Your event log will then show any rework loops as configured.
