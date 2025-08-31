from random import uniform
from simpn.simulator import SimProblem, SimToken
from typing import Dict, Optional
from datetime import datetime

def safe_eval(condition: str, attributes: Dict) -> bool:
    """
    Safely evaluate the condition string using attributes.
    """
    try:
        # Include datetime in the evaluation environment
        env = {"__builtins__": {}, "datetime": datetime}
        env.update(attributes)
        return eval(condition, env)
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

def _find_prototype(sim_problem: SimProblem, activity_id: str):
    return next((p for p in sim_problem.prototypes if p.get_id() == activity_id), None)

def _must(condition: bool, msg: str):
    if not condition:
        raise ValueError(msg)

def setup_rework_impact(sim_problem: SimProblem, config: dict):
    """
    Make a decision event's behavior depend on whether the case had rework.
    The decision config must be present in config["decision"].

    Behavior:
      - If attributes.get("has_rework") is true: use the "rework" probabilities.
      - Otherwise: use the "normal" probabilities.

    This function will:
      - Locate the decision event by its name.
      - Optionally rewire the event's two outgoing arcs to the provided end-event targets.
      - Replace the event behavior to apply rework-aware probabilities.
    """
    # -------- Read and validate config --------
    dcfg = config.get("decision")
    _must(dcfg is not None, "Missing 'decision' in config.json.")

    event_name = dcfg.get("event_name")
    _must(isinstance(event_name, str) and event_name.strip(),
          "decision.event_name must be a non-empty string.")

    normal = dcfg.get("normal", {})
    rework = dcfg.get("rework", {})

    def _prob_pair(block: dict, label: str):
        try:
            pp = float(block["positive_probability"])
            np = float(block["negative_probability"])
        except Exception:
            raise ValueError(
                f"decision.{label} must contain numeric 'positive_probability' and "
                f"'negative_probability'. Example: {{'positive_probability': 0.5, 'negative_probability': 0.5}}"
            )
        _must(0.0 <= pp <= 1.0 and 0.0 <= np <= 1.0, f"decision.{label} probabilities must be in [0,1].")
        # Do not force exact sum to 1 to allow tiny rounding; normalize if slightly off.
        s = pp + np
        _must(s > 0.0, f"decision.{label} probabilities must not both be zero.")
        return (pp / s, np / s)

    normal_p = _prob_pair(normal, "normal")
    rework_p = _prob_pair(rework, "rework")

    pos_target = dcfg.get("positive_target")
    neg_target = dcfg.get("negative_target")

    # -------- Find the decision event node --------
    node = sim_problem.id2node.get(event_name)
    _must(node is not None, f"Decision event '{event_name}' not found in the model. "
                            f"Ensure you created the split event with name='{event_name}'.")

    _must(hasattr(node, "incoming") and hasattr(node, "outgoing"),
          f"Node '{event_name}' is not an event with flows.")

    _must(len(node.outgoing) == 2,
          f"Decision event '{event_name}' must have exactly two outgoing arcs. "
          f"Found {len(node.outgoing)}.")

    # -------- Optionally rewire to match targets --------
    # If targets are provided, locate their incoming places and set them as outflows in order [positive, negative].
    if pos_target and neg_target:
        pos_proto = _find_prototype(sim_problem, pos_target)
        neg_proto = _find_prototype(sim_problem, neg_target)
        _must(pos_proto is not None, f"Positive target end activity '{pos_target}' not found.")
        _must(neg_proto is not None, f"Negative target end activity '{neg_target}' not found.")

        _must(len(pos_proto.incoming) == 1, f"'{pos_target}' must have exactly one incoming place.")
        _must(len(neg_proto.incoming) == 1, f"'{neg_target}' must have exactly one incoming place.")

        pos_place = pos_proto.incoming[0]
        neg_place = neg_proto.incoming[0]

        # Keep existing incoming places as-is. Only set the two outgoing places.
        try:
            node.set_outflow([pos_place, neg_place])
        except Exception as e:
            raise ValueError(
                f"Failed to set outflows for '{event_name}'. "
                f"Check that the targets are reachable. Details: {e}"
            )

    # -------- Replace behavior with rework-aware logic --------
    original_outgoing = list(node.outgoing)  # after optional rewiring

    def _rework_aware_choice(token):
        # token content is expected to be (case_id, (attributes_dict, rework_counts_dict))
        try:
            identifier, payload = token
            attributes, rework_counts = payload
        except Exception:
            # Be permissive and default to no rework if the shape is unexpected
            attributes = {}
        has_rework = bool((attributes or {}).get("has_rework", False))

        if has_rework:
            pos_prob = normal_p[0] if rework_p is None else rework_p[0]
            # Using rework_p already; above line is safety but rework_p always exists
            pos_prob = rework_p[0]
        else:
            pos_prob = normal_p[0]

        if uniform(0.0, 1.0) < pos_prob:
            # Send to first outgoing (positive)
            return [SimToken(token), None]
        else:
            # Send to second outgoing (negative)
            return [None, SimToken(token)]

    node.behavior = _rework_aware_choice
