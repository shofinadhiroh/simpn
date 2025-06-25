import math
from resource_calculator import estimate_interarrival_time, estimate_service_time
from datetime import datetime
from simpn.simulator import SimToken

def adjust_bottlenecks(sim_problem, config):
    """
    Adjusts bottlenecks in the simulation based on the configuration.
    Supports both static and time-based resource shortages, including removing specific resources.
    
    Args:
        sim_problem: The SimProblem instance to adjust.
        config: Configuration dictionary containing bottleneck specifications.
    """
    bottlenecks = config.get("bottlenecks", None)
    if not bottlenecks or bottlenecks.get("type") != "resource_shortage":
        print("No bottlenecks added")
        return

    where = bottlenecks.get("where", [])
    if all(isinstance(item, str) for item in where):
        # Static bottleneck: reduce resources permanently
        print("Adding Static Bottlenecks:")
        start_events = [e for e in sim_problem.events if e.get_id().endswith("<start_event>")]
        if len(start_events) != 1:
            raise ValueError("Expected exactly one start event")
        start_event = start_events[0]
        prefix = start_event.get_id().split("<")[0]
        mean_interarrival_time = estimate_interarrival_time(start_event.behavior, prefix)
        arrival_rate = 1 / mean_interarrival_time

        reductions_made = False
        for task in where:
            task_start_events = [e for e in sim_problem.events if e.get_id() == task + "<task:start>"]
            if task_start_events:
                event = task_start_events[0]
                resource_var = event.incoming[1]
                mean_service_time = estimate_service_time(event.behavior)
                optimal = math.ceil(arrival_rate * mean_service_time)
                current = len(resource_var.marking)
                if current >= optimal:
                    desired = max(1, optimal - 1)
                    initial = current
                    while len(resource_var.marking) > desired:
                        resource_var.remove_token(resource_var.marking[0])
                    final = len(resource_var.marking)
                    if final < initial:
                        print(f"Reduced the number of resources in {task}, from {initial} to {final}")
                        reductions_made = True
        if not reductions_made:
            print("No bottlenecks added")
    elif all(isinstance(item, dict) and "task" in item and "periods" in item for item in where):
        # Time-based bottleneck: schedule resource adjustments
        print("Adding Time-Based Bottlenecks (e.g., summer holidays, Christmas, New Year):")
        print("- Simulating reduced resource availability during defined peak or holiday periods.\n")
        
        initial_time = datetime(2020, 1, 1)
        schedule = sim_problem.add_var("schedule")
        tasks_with_bottlenecks = set(item["task"] for item in where)
        removed_resources_vars = {}
        resource_vars = {}
        removed_active_vars = {}

        # Initialize variables for each task with bottlenecks
        for task in tasks_with_bottlenecks:
            var_name = f"removed_resources_{task}"
            removed_resources_vars[task] = sim_problem.add_var(var_name)
            removed_active_var_name = f"removed_active_{task}"
            removed_active_vars[task] = sim_problem.add_var(removed_active_var_name)
            start_events = [e for e in sim_problem.events if e.get_id() == task + "<task:start>"]
            if start_events:
                start_event = start_events[0]
                resource_var = start_event.incoming[1]
                resource_vars[task] = resource_var
            else:
                raise ValueError(f"No start event found for task {task}")

        # Print bottleneck information
        for task in tasks_with_bottlenecks:
            initial_resources = len(resource_vars[task].marking)
            print(f"- Task: {task}")
            print(f"  - Initial Resources: {initial_resources}")
            for item in where:
                if item["task"] == task:
                    for period in item["periods"]:
                        start_date = period["start_date"]
                        end_date = period["end_date"]
                        resources_to_remove = period["resources_to_remove"]
                        if isinstance(resources_to_remove, int):
                            reduced_resources = max(1, initial_resources - resources_to_remove)
                            print(f"  - From {start_date} to {end_date}: Resources reduced to {reduced_resources} (removed {resources_to_remove})")
                        elif isinstance(resources_to_remove, list):
                            print(f"  - From {start_date} to {end_date}: Resources removed: {', '.join(resources_to_remove)}")

        print("\nResource Settings Over Time:")
        for task in tasks_with_bottlenecks:
            initial_resources = len(resource_vars[task].marking)
            print(f"- {task}:")
            print(f"  - Normally: {initial_resources} resources")
            for item in where:
                if item["task"] == task:
                    for period in item["periods"]:
                        start_date = period["start_date"]
                        end_date = period["end_date"]
                        resources_to_remove = period["resources_to_remove"]
                        if isinstance(resources_to_remove, int):
                            reduced_resources = max(1, initial_resources - resources_to_remove)
                            print(f"  - During {start_date} to {end_date}: Resources reduced to {reduced_resources}")
                        elif isinstance(resources_to_remove, list):
                            print(f"  - During {start_date} to {end_date}: Resources {', '.join(resources_to_remove)} are unavailable")

        print("\nPotential Impacts:")
        for task in tasks_with_bottlenecks:
            initial_resources = len(resource_vars[task].marking)
            for item in where:
                if item["task"] == task:
                    for period in item["periods"]:
                        start_date = period["start_date"]
                        end_date = period["end_date"]
                        resources_to_remove = period["resources_to_remove"]
                        if isinstance(resources_to_remove, int):
                            reduction_percentage = (resources_to_remove / initial_resources) * 100 if initial_resources > 0 else 0
                            print(f"- During {start_date} to {end_date} for '{task}':")
                            print(f"  - Resource reduction: from {initial_resources} to {max(1, initial_resources - resources_to_remove)} (removed {resources_to_remove})")
                            print(f"  - Reduction percentage: {reduction_percentage:.0f}%")
                            print(f"  - Potential bottleneck: Increased waiting times for '{task}' due to reduced resource availability.")
                        elif isinstance(resources_to_remove, list):
                            print(f"- During {start_date} to {end_date} for '{task}':")
                            print(f"  - Resources removed: {', '.join(resources_to_remove)}")
                            print(f"  - Potential bottleneck: Increased waiting times for '{task}' due to unavailability of specific resources.")

        print("\nNote: These reductions reflect temporary constraints in resource availability during specified periods.")

        # Schedule resource adjustments
        for item in where:
            task = item["task"]
            for period in item["periods"]:
                start_date = datetime.strptime(period["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(period["end_date"], "%Y-%m-%d")
                t_start = (start_date - initial_time).total_seconds() / 60
                t_end = (end_date - initial_time).total_seconds() / 60
                resources_to_remove = period["resources_to_remove"]
                if isinstance(resources_to_remove, int):
                    schedule.put(("reduce_resources", task, resources_to_remove), time=t_start)
                    schedule.put(("restore_resources", task, resources_to_remove), time=t_end)
                elif isinstance(resources_to_remove, list):
                    schedule.put(("set_removed", task, resources_to_remove), time=t_start)
                    schedule.put(("unset_removed", task), time=t_end)
                    for resource_id in resources_to_remove:
                        schedule.put(("restore", task, resource_id), time=t_end)

        # Define events for each task
        for task in tasks_with_bottlenecks:
            resource_var = resource_vars[task]
            removed_var = removed_resources_vars[task]
            removed_active_var = removed_active_vars[task]
            remove_signal = sim_problem.add_var(f"remove_signal_{task}")
            restore_signal = sim_problem.add_var(f"restore_signal_{task}")

            # Logic for reducing by number
            def start_reduce_guard(task):
                def guard(schedule_value):
                    if isinstance(schedule_value, tuple) and len(schedule_value) == 3:
                        action, t, num = schedule_value
                        return action == "reduce_resources" and t == task
                    return False
                return guard

            def start_reduce_behavior(task):
                def behavior(schedule_value):
                    _, _, num_to_remove = schedule_value
                    return [SimToken(num_to_remove)]
                return behavior

            sim_problem.add_event(
                [schedule],
                [remove_signal],
                start_reduce_behavior(task),
                guard=start_reduce_guard(task),
                name=f"start_reduce_{task}"
            )

            def remove_resource_guard(to_remove, resource):
                return to_remove > 0

            def remove_resource_behavior(to_remove, resource):
                if to_remove > 0:
                    return [SimToken(to_remove - 1) if to_remove > 1 else None, SimToken(resource)]
                return None

            sim_problem.add_event(
                [remove_signal, resource_var],
                [remove_signal, removed_var],
                remove_resource_behavior,
                guard=remove_resource_guard,
                name=f"remove_resource_{task}"
            )

            # Logic for setting removed resources list
            def set_removed_guard(task):
                def guard(schedule_value):
                    if isinstance(schedule_value, tuple) and len(schedule_value) == 3:
                        action, t, resources_list = schedule_value
                        return action == "set_removed" and t == task
                    return False
                return guard

            def set_removed_behavior(task):
                def behavior(schedule_value):
                    _, _, resources_list = schedule_value
                    return [SimToken(resources_list, delay=0)]
                return behavior

            sim_problem.add_event(
                [schedule],
                [removed_active_var],
                set_removed_behavior(task),
                guard=set_removed_guard(task),
                name=f"set_removed_{task}"
            )

            # Logic for unsetting removed resources list
            def unset_removed_guard(task):
                def guard(schedule_value, removed_list):
                    if isinstance(schedule_value, tuple) and len(schedule_value) == 2:
                        action, t = schedule_value
                        return action == "unset_removed" and t == task
                    return False
                return guard

            def unset_removed_behavior(schedule_value, removed_list):
                return []

            sim_problem.add_event(
                [schedule, removed_active_var],
                [],
                unset_removed_behavior,
                guard=unset_removed_guard(task),
                name=f"unset_removed_{task}"
            )

            # Logic for moving removed resources to removed_var
            def move_removed_guard(task, removed_active_var):
                def guard(resource, removed_list):
                    return resource in removed_list
                return guard

            def move_removed_behavior(resource, removed_list):
                return [SimToken(resource, delay=0), SimToken(removed_list, delay=0)]

            sim_problem.add_event(
                [resource_var, removed_active_var],
                [removed_var, removed_active_var],
                move_removed_behavior,
                guard=move_removed_guard(task, removed_active_var),
                name=f"move_removed_{task}"
            )

            # Logic for restoring specific resources
            def restore_specific_guard(task, removed_var):
                def guard(schedule_value, removed_resource):
                    if isinstance(schedule_value, tuple) and len(schedule_value) == 3:
                        action, t, resource_id = schedule_value
                        return action == "restore" and t == task and removed_resource == resource_id
                    return False
                return guard

            def restore_specific_behavior(schedule_value, removed_resource):
                return [SimToken(removed_resource, delay=0)]

            sim_problem.add_event(
                [schedule, removed_var],
                [resource_var],
                restore_specific_behavior,
                guard=restore_specific_guard(task, removed_var),
                name=f"restore_specific_resource_{task}"
            )

            # Restoration logic for reducing by number
            def start_restore_guard(task):
                def guard(schedule_value):
                    if isinstance(schedule_value, tuple) and len(schedule_value) == 3:
                        action, t, num = schedule_value
                        return action == "restore_resources" and t == task
                    return False
                return guard

            def start_restore_behavior(task):
                def behavior(schedule_value):
                    _, _, num_to_restore = schedule_value
                    return [SimToken(num_to_restore)]
                return behavior

            sim_problem.add_event(
                [schedule],
                [restore_signal],
                start_restore_behavior(task),
                guard=start_restore_guard(task),
                name=f"start_restore_{task}"
            )

            def restore_resource_guard(restore_count, removed_resource):
                return restore_count > 0

            def restore_resource_behavior(restore_count, removed_resource):
                if restore_count > 0:
                    return [SimToken(restore_count - 1) if restore_count > 1 else None, SimToken(removed_resource)]
                return None

            sim_problem.add_event(
                [restore_signal, removed_var],
                [restore_signal, resource_var],
                restore_resource_behavior,
                guard=restore_resource_guard,
                name=f"restore_resource_{task}"
            )

    else:
        raise ValueError("Invalid format for 'where' in bottlenecks")