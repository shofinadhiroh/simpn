Simulation Templates
====================

The ``templates`` folder contains ready‐made BPMN process definitions to help you get started:

- **sequence.py**  
  A simple linear workflow: Task A → Task B → Task C.

- **parallel.py**  
  A fork/join pattern where multiple tasks run concurrently.

- **choice.py**  
  An exclusive decision gateway with configurable branch probabilities.

- **mix.py**  
  A mixed workflow combining sequence, parallel, and choice patterns.

- **bottleneck.py**  
  A pre-template for demonstrating a planned resource shortage scenario.

Usage
-----

Run standalone::

   python templates/sequence.py