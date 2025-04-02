from random import uniform
from simpn.simulator import SimProblem, SimToken
from typing import Dict

def safe_eval(condition: str, attributes: Dict) -> bool:
    """
    Safely evaluate the condition string using attributes.
    Replace with your actual safe evaluation method if different.
    """
    try:
        return eval(condition, {"__builtins__": {}}, attributes)
    except Exception:
        return False

def setup_rework(sim_problem: SimProblem, config: dict):
    """
    Sets up self-loop rework where a token is sent back to the same activity's input queue.
    Uses conditions defined in config.json for dynamic behavior.
    """
    for rework_config in config.get("rework", []):
        activity = rework_config["activity"]
        max_iteration = rework_config["max_iteration"]
        probability = rework_config["probability"]
        condition = rework_config.get("condition", "True")  # Default to True if no condition

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
            print(f"Decision place '{decision_place_name}' already exists. Using existing place.")
            decision_place = sim_problem.id2node[decision_place_name]
        else:
            decision_place = sim_problem.add_var(decision_place_name)

        # Redirect the activity’s output to the decision place
        prototype.outgoing[0] = decision_place

        # Define the decision behavior
        def decision_behavior(c):
            # Unpack the token value; expected structure: (identifier, (attributes, rework_counts))
            identifier, (attributes, rework_counts) = c
            count = rework_counts.get(activity, 0)
            if safe_eval(condition, attributes) and count < max_iteration and uniform(0, 1) < probability:
                # Rework: increment count and send token back to input queue
                new_rework_counts = {**rework_counts, activity: count + 1}
                new_token = (identifier, (attributes, new_rework_counts))
                return [SimToken(new_token), None]
            # Proceed: normalize token by removing this activity's rework count before proceeding
            new_rework_counts = rework_counts.copy()
            if activity in new_rework_counts:
                del new_rework_counts[activity]
            new_token = (identifier, (attributes, new_rework_counts))
            return [None, SimToken(new_token)]

        # Add the decision event without a guard
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
            print(f"Added event: {event_name}")

def setup_long_rework(sim_problem: SimProblem, config: dict):
    """
    Sets up long rework where a token is sent back to an earlier activity.
    Uses conditions defined in config.json for dynamic behavior.
    """
    for long_rework_config in config.get("long_rework", []):
        trigger_activity = long_rework_config["trigger_activity"]
        back_to_activity = long_rework_config["back_to"]
        max_iteration = long_rework_config["max_iteration"]
        probability = long_rework_config["probability"]
        condition = long_rework_config.get("condition", "True")  # Default to True if no condition is specified

        # Find prototypes for trigger and back-to activities
        trigger_prototype = next((p for p in sim_problem.prototypes if p.get_id() == trigger_activity), None)
        back_to_prototype = next((p for p in sim_problem.prototypes if p.get_id() == back_to_activity), None)
        if not trigger_prototype or not back_to_prototype:
            raise ValueError(f"Activity not found: '{trigger_activity}' or '{back_to_activity}'")

        # Get the input queue of the back-to activity and the next place after trigger
        back_to_input = back_to_prototype.incoming[0]
        next_place = trigger_prototype.outgoing[0]

        # Create a dynamic decision place
        decision_place_name = f"long_rework_decision_{trigger_activity}_to_{back_to_activity}"
        if decision_place_name in sim_problem.id2node:
            print(f"Decision place '{decision_place_name}' already exists. Using existing place.")
            decision_place = sim_problem.id2node[decision_place_name]
        else:
            decision_place = sim_problem.add_var(decision_place_name)

        # Redirect the trigger activity's output to the decision place
        trigger_prototype.outgoing[0] = decision_place

        # Unique key for tracking this specific long rework
        rework_key = f"{trigger_activity}_to_{back_to_activity}"

        # Decision: Rework or proceed, conditioned on the specified condition
        def decision_behavior(c):
            identifier, (attributes, rework_counts) = c
            count = rework_counts.get(rework_key, 0)
            if safe_eval(condition, attributes) and count < max_iteration and uniform(0, 1) < probability:
                new_rework_counts = {**rework_counts, rework_key: count + 1}
                new_token = (identifier, (attributes, new_rework_counts))
                return [SimToken(new_token), None]
            # Proceed: normalize by removing the rework count for this long rework
            new_rework_counts = rework_counts.copy()
            if rework_key in new_rework_counts:
                del new_rework_counts[rework_key]
            new_token = (identifier, (attributes, new_rework_counts))
            return [None, SimToken(new_token)]

        # Add the long rework decision event only if it doesn't already exist
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
            print(f"Added event: {event_name}")
