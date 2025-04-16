from random import uniform
from simpn.simulator import SimProblem, SimToken
from typing import Dict

def safe_eval(condition: str, attributes: Dict) -> bool:
    """
    Safely evaluate the condition string using attributes.
    """
    try:
        return eval(condition, {"__builtins__": {}}, attributes)
    except Exception:
        return False

def setup_rework(sim_problem: SimProblem, config: dict):
    """
    Sets up self-loop rework where a token is sent back to the same activity's input queue.
    Rework occurs based on conditions and resource used, as defined in config.json.
    """
    for rework_config in config.get("rework", []):
        activity = rework_config["activity"]
        max_iteration = rework_config["max_iteration"]
        probability = rework_config["probability"]
        condition = rework_config.get("condition", "True")
        resource_condition = rework_config.get("resource", None)  # Resource that triggers rework

        # Find the prototype for the activity
        prototype = next((p for p in sim_problem.prototypes if p.get_id() == activity), None)
        if not prototype:
            raise ValueError(f"Activity '{activity}' not found in the process model")

        # Get the input and output places for the activity
        input_queue = prototype.incoming[0]
        output_queue = prototype.outgoing[0]

        # Create a decision place if it doesn’t exist
        decision_place_name = f"rework_decision_{activity}"
        if decision_place_name in sim_problem.id2node:
            decision_place = sim_problem.id2node[decision_place_name]
        else:
            decision_place = sim_problem.add_var(decision_place_name)

        # Modify the complete event to output to decision_place instead of output_queue
        complete_event_name = f"{activity}<task:complete>"
        if complete_event_name in sim_problem.id2node:
            complete_event = sim_problem.id2node[complete_event_name]
            resource_place = complete_event.outgoing[1]  # Assuming [output_place, resource_place]
            complete_event.set_outflow([decision_place, resource_place])

            # Modify behavior to include resource in attributes
            def complete_with_resource(busy, activity=activity):
                case, resource = busy  # busy is the tuple ((case_id, (attributes, rework_counts)), resource)
                identifier, (attributes, rework_counts) = case
                new_attributes = {**attributes, f"{activity}_resource": resource}
                new_case = (identifier, (new_attributes, rework_counts))
                return [SimToken(new_case, delay=0), SimToken(resource, delay=0)]
            complete_event.behavior = complete_with_resource

        # Define the decision behavior with resource check
        def decision_behavior(c):
            identifier, (attributes, rework_counts) = c
            count = rework_counts.get(activity, 0)
            resource_used = attributes.get(f"{activity}_resource", None)
            # Check if resource matches the condition (if specified) and other criteria
            if ((resource_condition is None or resource_used == resource_condition) and
                safe_eval(condition, attributes) and
                count < max_iteration and
                uniform(0, 1) < probability):
                # Rework: increment count and send token back to input queue
                new_rework_counts = {**rework_counts, activity: count + 1}
                new_attributes = {**attributes, "has_rework": True}
                new_token = (identifier, (new_attributes, new_rework_counts))
                return [SimToken(new_token), None]
            # Proceed: remove this activity's rework count
            new_rework_counts = rework_counts.copy()
            if activity in new_rework_counts:
                del new_rework_counts[activity]
            new_token = (identifier, (attributes, new_rework_counts))
            return [None, SimToken(new_token)]

        # Add the decision event
        event_name = f"rework_decision_event_{activity}"
        if event_name in sim_problem.id2node:
            print(f"Event '{event_name}' already exists. Skipping addition.")
        else:
            sim_problem.add_event(
                [decision_place],
                [input_queue, output_queue],
                decision_behavior,
                name=event_name
            )

def setup_long_rework(sim_problem: SimProblem, config: dict):
    """
    Sets up long rework where a token is sent back to an earlier activity.
    Rework occurs based on conditions and resource used, as defined in config.json.
    """
    for long_rework_config in config.get("long_rework", []):
        trigger_activity = long_rework_config["trigger_activity"]
        back_to_activity = long_rework_config["back_to"]
        max_iteration = long_rework_config["max_iteration"]
        probability = long_rework_config["probability"]
        condition = long_rework_config.get("condition", "True")
        resource_condition = long_rework_config.get("resource", None)  # Resource that triggers rework

        # Find prototypes
        trigger_prototype = next((p for p in sim_problem.prototypes if p.get_id() == trigger_activity), None)
        back_to_prototype = next((p for p in sim_problem.prototypes if p.get_id() == back_to_activity), None)
        if not trigger_prototype or not back_to_prototype:
            raise ValueError(f"Activity not found: '{trigger_activity}' or '{back_to_activity}'")

        # Get places
        back_to_input = back_to_prototype.incoming[0]
        next_place = trigger_prototype.outgoing[0]

        # Create a decision place
        decision_place_name = f"long_rework_decision_{trigger_activity}_to_{back_to_activity}"
        if decision_place_name in sim_problem.id2node:
            decision_place = sim_problem.id2node[decision_place_name]
        else:
            decision_place = sim_problem.add_var(decision_place_name)

        # Modify the complete event for the trigger activity
        complete_event_name = f"{trigger_activity}<task:complete>"
        if complete_event_name in sim_problem.id2node:
            complete_event = sim_problem.id2node[complete_event_name]
            resource_place = complete_event.outgoing[1]
            complete_event.set_outflow([decision_place, resource_place])

            def complete_with_resource(busy, activity=trigger_activity):
                case, resource = busy
                identifier, (attributes, rework_counts) = case
                new_attributes = {**attributes, f"{activity}_resource": resource}
                new_case = (identifier, (new_attributes, rework_counts))
                return [SimToken(new_case, delay=0), SimToken(resource, delay=0)]
            complete_event.behavior = complete_with_resource

        # Unique key for this rework loop
        rework_key = f"{trigger_activity}_to_{back_to_activity}"

        # Decision behavior with resource check
        def decision_behavior(c):
            identifier, (attributes, rework_counts) = c
            count = rework_counts.get(rework_key, 0)
            resource_used = attributes.get(f"{trigger_activity}_resource", None)
            if ((resource_condition is None or resource_used == resource_condition) and
                safe_eval(condition, attributes) and
                count < max_iteration and
                uniform(0, 1) < probability):
                new_rework_counts = {**rework_counts, rework_key: count + 1}
                new_attributes = {**attributes, "has_rework": True}
                new_token = (identifier, (new_attributes, new_rework_counts))
                return [SimToken(new_token), None]
            new_rework_counts = rework_counts.copy()
            if rework_key in new_rework_counts:
                del new_rework_counts[rework_key]
            new_token = (identifier, (attributes, new_rework_counts))
            return [None, SimToken(new_token)]

        # Add the decision event
        event_name = f"long_rework_decision_event_{trigger_activity}_to_{back_to_activity}"
        if event_name in sim_problem.id2node:
            print(f"Event '{event_name}' already exists. Skipping addition.")
        else:
            sim_problem.add_event(
                [decision_place],
                [back_to_input, next_place],
                decision_behavior,
                name=event_name
            )

        # Modify subsequent decision event if exists
        decision_events = [
            e for e in sim_problem.events
            if back_to_prototype.outgoing[0] in e.incoming and trigger_prototype.incoming[0] in e.outgoing
        ]
        if decision_events and len(decision_events) == 1:
            decision_event = decision_events[0]
            original_behavior = decision_event.behavior
            def new_behavior(token):
                identifier, (attributes, _) = token
                if attributes.get("has_rework", False):
                    index = decision_event.outgoing.index(trigger_prototype.incoming[0])
                    result = [None] * len(decision_event.outgoing)
                    result[index] = SimToken(token)
                    return result
                return original_behavior(token)
            decision_event.behavior = new_behavior