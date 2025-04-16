from simpn.simulator import SimToken, SimProblem
from random import uniform, choices
import json
from datetime import datetime, timedelta

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Define the initial simulation start time
INITIAL_TIME = datetime(2020, 1, 1, 0, 0, 0)

def start_behavior(sim_problem):
    """
    Generates case attributes based on distribution configurations in config.json.
    Returns a SimToken containing the attributes and an empty rework_counts dictionary.
    """
    attributes = {}
    for attr_name, attr_config in config.get("case_attributes", {}).items():
        attr_type = attr_config["type"]
        dist_config = attr_config.get("distribution", {})
        dist_type = dist_config.get("type")

        if dist_type == "discrete":
            # Handle discrete distributions (for strings, booleans)
            values = [item["value"] for item in dist_config["values"]]
            probabilities = [item["probability"] for item in dist_config["values"]]
            # Validate probabilities
            if not (0.99 <= sum(probabilities) <= 1.01):
                raise ValueError(f"Probabilities for {attr_name} must sum to 1, got {sum(probabilities)}")
            # Select one value based on probabilities
            value = choices(values, weights=probabilities, k=1)[0]
            attributes[attr_name] = value

        elif dist_type == "bins" and attr_type == "numerical":
            # Handle binned numerical distributions
            bins = dist_config["bins"]
            ranges = [item["range"] for item in bins]
            probabilities = [item["probability"] for item in bins]
            # Validate probabilities
            if not (0.99 <= sum(probabilities) <= 1.01):
                raise ValueError(f"Probabilities for {attr_name} must sum to 1, got {sum(probabilities)}")
            # Select a bin based on probabilities
            selected_bin = choices(ranges, weights=probabilities, k=1)[0]
            # Generate a uniform random value within the selected bin
            min_val, max_val = selected_bin
            value = uniform(min_val, max_val)
            attributes[attr_name] = value

        else:
            raise ValueError(f"Unsupported distribution type '{dist_type}' for attribute '{attr_name}'")

    # Add the start time as a datetime
    start_time = INITIAL_TIME + timedelta(minutes=sim_problem.clock)
    attributes["start_time"] = start_time
    # Token format: (attributes, rework_counts)
    return [SimToken((attributes, {}))]