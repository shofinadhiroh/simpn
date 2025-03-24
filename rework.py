from simpn.simulator import SimProblem, SimToken
from random import uniform

def setup_rework(sim_problem: SimProblem, config: dict):
    """
    Sets up self-loop rework where a token is sent back to the same activity's input queue.
    Driven entirely by config.json.
    """
    for rework_config in config.get("rework", []):
        activity = rework_config["activity"]
        max_iteration = rework_config["max_iteration"]
        probability = rework_config["probability"]

        # Find the prototype for the activity
        prototype = next((p for p in sim_problem.prototypes if p.get_id() == activity), None)
        if not prototype:
            raise ValueError(f"Activity '{activity}' not found in the process model")

        # Get the input and output places for the activity
        input_queue = prototype.incoming[0]  # First incoming place (queue)
        output_queue = prototype.outgoing[0]  # First outgoing place

        # Guard: Check if rework iterations are below the limit
        def guard(c):
            _, (case_id, rework_counts) = c
            count = rework_counts.get(activity, 0)
            return count < max_iteration

        # Decision: Rework or proceed
        def decision_behavior(c):
            identifier, (case_id, rework_counts) = c
            count = rework_counts.get(activity, 0)
            if count < max_iteration and uniform(0, 1) < probability:
                # Increment rework count for this activity
                new_rework_counts = {**rework_counts, activity: count + 1}
                new_token = (identifier, (case_id, new_rework_counts))
                return [SimToken(new_token), None]  # Back to input queue
            return [None, SimToken(c)]  # Proceed to output queue

        # Add the rework decision event
        sim_problem.add_event(
            [output_queue],
            [input_queue, output_queue],
            decision_behavior,
            name=f"rework_decision_{activity}",
            guard=guard
        )

def setup_long_rework(sim_problem: SimProblem, config: dict):
    """
    Sets up long rework where a token is sent back to an earlier activity.
    Driven entirely by config.json with no hardcoded assumptions.
    """
    for long_rework_config in config.get("long_rework", []):
        trigger_activity = long_rework_config["trigger_activity"]
        back_to_activity = long_rework_config["back_to"]
        max_iteration = long_rework_config["max_iteration"]
        probability = long_rework_config["probability"]

        # Find prototypes for trigger and back-to activities
        trigger_prototype = next((p for p in sim_problem.prototypes if p.get_id() == trigger_activity), None)
        back_to_prototype = next((p for p in sim_problem.prototypes if p.get_id() == back_to_activity), None)
        if not trigger_prototype or not back_to_prototype:
            raise ValueError(f"Activity not found: '{trigger_activity}' or '{back_to_activity}'")

        # Get the input queue of the back-to activity and the next place after trigger
        back_to_input = back_to_prototype.incoming[0]  # First incoming place
        next_place = trigger_prototype.outgoing[0]      # Original next place

        # Create a dynamic decision place
        decision_place_name = f"rework_decision_{trigger_activity}_to_{back_to_activity}"
        decision_place = sim_problem.add_var(decision_place_name)

        # Redirect the trigger activity's output to the decision place
        trigger_prototype.outgoing[0] = decision_place

        # Unique key for tracking this specific long rework
        rework_key = f"{trigger_activity}_to_{back_to_activity}"

        # Decision: Rework or proceed
        def decision_behavior(c):
            identifier, (case_id, rework_counts) = c
            count = rework_counts.get(rework_key, 0)
            if count < max_iteration and uniform(0, 1) < probability:
                # Increment rework count for this specific rework
                new_rework_counts = {**rework_counts, rework_key: count + 1}
                new_token = (identifier, (case_id, new_rework_counts))
                return [SimToken(new_token), None]  # Back to back_to_input
            return [None, SimToken(c)]  # Proceed to next_place

        # Add the long rework decision event without guard
        sim_problem.add_event(
            [decision_place],
            [back_to_input, next_place],
            decision_behavior,
            name=f"long_rework_decision_{trigger_activity}_to_{back_to_activity}"
        )