Modelling and Simulating Bottlenecks
====================================

The ``bottleneck`` package helps you identify, adjust, and simulate resource-based bottlenecks in your BPMN processes:

- **Optimal Resource Calculation**: find under-resourced activities
- **Time-Based Shortages**: temporarily remove staff/machines (e.g., holidays)
- **Resource Constraints**: restrict which resources may work on a task
- **Task Scheduling Constraints**: restrict tasks to run only on specific days or date ranges

Modules
-------

- ``resource_calculator.calculate_optimal_resources``
- ``bottleneck_manager.adjust_bottlenecks``
- ``resource_constraints.apply_resource_constraints``
- ``task_constraints.apply_task_constraints``

1. Calculate Optimal Resources
------------------------------

.. code-block:: python

   from bottleneck.resource_calculator import calculate_optimal_resources

   resources = calculate_optimal_resources(agency)
   # Console shows recommended headcounts vs. current

2. Simulate Time-Based Shortages
--------------------------------

In ``config.json``:

.. code-block:: json

   "bottlenecks": {
     "type": "resource_shortage",
     "where": [
       {
         "task": "approve_application",
         "periods": [
           {
             "start_date": "2020-12-24",
             "end_date": "2020-12-26",
             "resources_to_remove": ["m1", "m2", "m3"]
           }
         ]
       }
     ]
   }

In your script:

.. code-block:: python

   from bottleneck.bottleneck_manager import adjust_bottlenecks

   adjust_bottlenecks(agency, config)

3. Apply Resource Constraints
-----------------------------

In ``config.json``:

.. code-block:: json

   "resource_constraints": [
     {
       "task": "pre_approval_check",
       "conditions": [
         {
           "condition": "loanType == 'personal'",
           "resources": ["s1"]
         }
       ]
     }
   ]

In your script:

.. code-block:: python

   from bottleneck.resource_constraints import apply_resource_constraints

   apply_resource_constraints(agency, config)

4. Apply Task Scheduling Constraints
------------------------------------

Use this when tasks should only run on specific weekdays or date ranges.

In ``config.json``:

.. code-block:: json

   "task_constraints": {
     "pre_approval_check": {
       "type": "day_of_week",
       "days": ["Thursday"]
     },
     "approve_application": {
       "type": "date_range",
       "start_day": 5,
       "end_day": 10
     }
   }

In your script:

.. code-block:: python

   from bottleneck.task_constraints import apply_task_constraints

   apply_task_constraints(agency, config)
This simulates time-based gating. Tasks will queue until a valid execution date, which can induce bottlenecks if not managed.

Run your simulation as usual. The logs and console output will reflect the bottleneck behavior you have configured.
