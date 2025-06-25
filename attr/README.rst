Enriching the Event Log with Custom Attributes
==============================================

The ``attr`` package lets you attach domain‐specific attributes to each case in your SimPN event log  
—for example, loan amount, loan type, or priority flags. By enriching the standard five‐column log  
(``case_id``, ``task``, ``resource``, ``start_time``, ``completion_time``), you can support deeper analysis:

  - Correlate case attributes with cycle times  
  - Filter or group by loan type, urgency, or other custom fields  
  - Answer questions like “Do urgent cases complete faster?”

Prerequisites
-------------

1. A BPMN‐style process model defined in your script.  
2. The enrichment modules in ``attr/``:  
   - ``case_attributes.py``  
   - ``custom_reporters.py``  

Configuration (``config.json``)
-------------------------------

Under the top‐level ``"case_attributes"`` key define each attribute:

Numerical attribute example::

   "case_attributes": {
     "requestedAmount": {
       "type": "numerical",
       "distribution": {
         "type": "bins",
         "bins": [
           { "range": [1000, 50000],   "probability": 0.5 },
           { "range": [50001, 100000], "probability": 0.5 }
         ]
       }
     }
   }

String attribute example::

   "case_attributes": {
     "loanType": {
       "type": "string",
       "distribution": {
         "type": "discrete",
         "values": [
           { "value": "personal", "probability": 0.6 },
           { "value": "mortgage", "probability": 0.2 },
           { "value": "auto",     "probability": 0.2 }
         ]
       }
     }
   }

Boolean attribute example::

   "case_attributes": {
     "isUrgent": {
       "type": "boolean",
       "distribution": {
         "type": "discrete",
         "values": [
           { "value": true,  "probability": 0.3 },
           { "value": false, "probability": 0.7 }
         ]
       }
     }
   }

Usage
-----

1. **Import the utilities** at the top of your script::

       from attr.case_attributes import start_behavior
       from attr.custom_reporters import EnhancedEventLogReporter

2. **Load your configuration**::

       import json
       with open("config.json") as f:
           config = json.load(f)

3. **Attach case attributes** to your start event::

       BPMNStartEvent(
           loan_process,
           [],
           [waiting],
           "application_received",
           lambda: exp(1/20),
           behavior=lambda: start_behavior(loan_process)
       )

4. **Replace the reporter**::

       reporter = EnhancedEventLogReporter(
           "sequence.csv",
           config=config,
           sim_problem=loan_process
       )
       loan_process.simulate(24*60*10, reporter)
       reporter.close()

After simulation, ``sequence.csv`` will include your custom columns:  
``case_id, task, resource, start_time, completion_time, requestedAmount, loanType, isUrgent``.
