import json

def print_resource_constraints(config):
    """
    Prints the resource constraints defined in the config to the console, 
    including warnings for potential bottlenecks caused by resource constraints.
    
    :param config: The configuration dictionary loaded from config.json.
    """
    print("\nResource Constraints:\n")
    resource_constraints = config.get('resource_constraints', [])
    if not resource_constraints:
        print("No resource constraints defined.")
        return
    
    for constraint in resource_constraints:
        task = constraint['task']
        print(f"Task: {task}")
        conditions = constraint.get('conditions', [])
        if not conditions:
            print("  No specific conditions. All resources are allowed.")
        else:
            for cond in conditions:
                condition_str = cond['condition']
                resources = cond['resources']
                resources_str = ', '.join(resources)
                if len(resources) == 1:
                    print(f"  - If {condition_str}: Only resource {resources_str} is allowed.")
                    print("    WARNING: Resource constraint may cause bottlenecks if this condition is common.")
                else:
                    print(f"  - If {condition_str}: Only resources {resources_str} are allowed.")
        print()  # Add a blank line for readability

def create_guard(task_name, config):
    """
    Creates a guard function for a specific task based on resource constraints in the config.
    
    :param task_name: The name of the task (e.g., 'pre_approval_check').
    :param config: The configuration dictionary from config.json.
    :return: A guard function if constraints exist, else None.
    """
    task_constraints = next((tc for tc in config.get('resource_constraints', []) if tc['task'] == task_name), None)
    if task_constraints:
        def guard(c, r):
            """
            Checks if the resource is allowed to perform the task for the case.
            
            :param c: Case token as (case_id, (attributes, rework_counts)).
            :param r: Resource identifier (e.g., 's1').
            :return: True if allowed, False otherwise.
            """
            attributes = c[1][0]  # Extract attributes from case token
            for condition in task_constraints['conditions']:
                if eval(condition['condition'], {}, attributes):
                    return r in condition['resources']
            return True  # No conditions met means any resource is allowed
        return guard
    return None

def apply_resource_constraints(agency, config):
    """
    Applies resource constraints to task start events in the simulation problem 
    and prints the constraints to the console.
    
    :param agency: The SimProblem instance.
    :param config: The configuration dictionary from config.json.
    """
    print_resource_constraints(config)  # Print constraints before applying
    for task_constraint in config.get('resource_constraints', []):
        task_name = task_constraint['task']
        start_event_name = f"{task_name}<task:start>"
        if start_event_name in agency.id2node:
            event = agency.id2node[start_event_name]
            guard = create_guard(task_name, config)
            if guard is not None:
                event.set_guard(guard)