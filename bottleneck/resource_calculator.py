import math

def estimate_interarrival_time(behavior_func, prefix, num_samples=1000):
    """
    Estimate the mean interarrival time by sampling the start event's behavior function.
    
    Args:
        behavior_func: The behavior function of the start event.
        prefix: The base name of the event (e.g., "receive_application").
        num_samples: Number of samples to take for estimation.
    Returns:
        The estimated mean interarrival time.
    """
    total_delay = 0
    for _ in range(num_samples):
        result = behavior_func(prefix + "0")
        delay = result[0].delay
        total_delay += delay
    return total_delay / num_samples

def estimate_service_time(behavior_func, num_samples=1000):
    """
    Estimate the mean service time by sampling the task start event's behavior function.
    
    Args:
        behavior_func: The behavior function of the task start event.
        num_samples: Number of samples to take for estimation.
    Returns:
        The estimated mean service time.
    """
    total_delay = 0
    for _ in range(num_samples):
        result = behavior_func("case", "resource")
        delay = result[0].delay
        total_delay += delay
    return total_delay / num_samples

def calculate_optimal_resources(sim_problem):
    """
    Calculate the optimal number of resources for each task and print messages accordingly.
    
    Args:
        sim_problem: The SimProblem instance containing the process model.
    Returns:
        A dictionary mapping task names to their optimal resource counts.
    """
    # Find the start event
    start_events = [e for e in sim_problem.events if e.get_id().endswith("<start_event>")]
    if len(start_events) != 1:
        raise ValueError("Expected exactly one start event")
    start_event = start_events[0]
    
    # Extract prefix from event ID
    prefix = start_event.get_id().split("<")[0]
    
    # Estimate mean interarrival time and calculate arrival rate
    mean_interarrival_time = estimate_interarrival_time(start_event.behavior, prefix)
    arrival_rate = 1 / mean_interarrival_time
    
    # Find all task start events
    task_start_events = [e for e in sim_problem.events if e.get_id().endswith("<task:start>")]
    
    resource_needs = {}
    current_resources = {}
    
    # Calculate optimal and current resources for each task
    for event in task_start_events:
        task_name = event.get_id().split("<")[0]
        mean_service_time = estimate_service_time(event.behavior)
        required_resources = arrival_rate * mean_service_time
        optimal = math.ceil(required_resources)
        resource_var = event.incoming[1]
        current = len(resource_var.marking)
        resource_needs[task_name] = optimal
        current_resources[task_name] = current
    
    # Check if any task has fewer resources than optimal
    if any(current_resources[task] < resource_needs[task] for task in resource_needs):
        print("\nThe amount of resources is not ideal and may cause bottlenecks.\n")
    
    # Print specific messages for each task
    for task in resource_needs:
        optimal = resource_needs[task]
        current = current_resources[task]
        if current >= optimal:
            print(f"The amount of resources for {task} is already ideal: {current}")
        else:
            print(f"{task} should have {optimal} resources, but currently has {current}")
    
    return resource_needs