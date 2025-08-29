import math
import json
import re

def estimate_interarrival_time(behavior_func, prefix, num_samples=1000):
    total_delay = 0.0
    for _ in range(num_samples):
        result = behavior_func(prefix + "0")
        total_delay += float(result[0].delay)
    return total_delay / num_samples

def estimate_service_time(behavior_func, num_samples=1000):
    total_delay = 0.0
    for _ in range(num_samples):
        result = behavior_func("case", "resource")
        total_delay += float(result[0].delay)
    return total_delay / num_samples

# -----------------------------
# Rework-aware visits-per-case
# -----------------------------

def _prob_discrete(attr_cfg, val):
    dist = (attr_cfg or {}).get("distribution", {})
    if dist.get("type") != "discrete":
        return 0.0
    p = 0.0
    for entry in dist.get("values", []):
        if entry.get("value") == val:
            p += float(entry.get("probability", 0.0))
    return p

def _prob_bins_gt(attr_cfg, thr):
    dist = (attr_cfg or {}).get("distribution", {})
    if dist.get("type") != "bins":
        return 0.0
    p = 0.0
    for b in dist.get("bins", []):
        lo, hi = b.get("range", [None, None])
        if lo is None or hi is None:
            continue
        prob = float(b.get("probability", 0.0))
        if lo > thr:
            p += prob
        elif lo <= thr < hi:
            span = hi - lo
            if span > 0:
                p += prob * (hi - thr) / span
    return p

def _cond_prob(cond_str, case_attrs_cfg):
    """Very small parser: attr=='x', attr==True/False, attr>n, attr<n. Empty -> 1.0."""
    if not cond_str or not cond_str.strip():
        return 1.0
    s = cond_str.strip()

    m = re.match(r"^\s*([A-Za-z_]\w*)\s*==\s*'([^']+)'\s*$", s)
    if m:
        attr, val = m.group(1), m.group(2)
        return _prob_discrete(case_attrs_cfg.get(attr, {}), val)

    m = re.match(r"^\s*([A-Za-z_]\w*)\s*==\s*(True|False)\s*$", s)
    if m:
        attr, val = m.group(1), (m.group(2) == "True")
        return _prob_discrete(case_attrs_cfg.get(attr, {}), val)

    m = re.match(r"^\s*([A-Za-z_]\w*)\s*>\s*([0-9]+(?:\.[0-9]+)?)\s*$", s)
    if m:
        attr, thr = m.group(1), float(m.group(2))
        return _prob_bins_gt(case_attrs_cfg.get(attr, {}), thr)

    m = re.match(r"^\s*([A-Za-z_]\w*)\s*<\s*([0-9]+(?:\.[0-9]+)?)\s*$", s)
    if m:
        attr, thr = m.group(1), float(m.group(2))
        eps = 1e-9
        p_ge = _prob_bins_gt(case_attrs_cfg.get(attr, {}), thr - eps)
        return max(0.0, min(1.0, 1.0 - p_ge))

    return 0.0  # unknown pattern

def _visits_per_case(sim_problem, config):
    """Start at 1 visit/task; add expected extra visits from rework rules."""
    tasks = [e for e in sim_problem.events if e.get_id().endswith("<task:start>")]
    v = {e.get_id().split("<")[0]: 1.0 for e in tasks}
    if not config:
        return v

    case_attrs = config.get("case_attributes", {})

    # Self-loop rework on activity A
    for item in config.get("rework", []):
        act = item.get("activity")
        p = float(item.get("probability", 0.0))
        m = int(item.get("max_iteration", 0))
        q = _cond_prob(item.get("condition", ""), case_attrs)
        if act in v and p > 0 and m > 0:
            v[act] += p * m * q

    # Long rework that jumps back to task B
    for item in config.get("long_rework", []):
        back_to = item.get("back_to")
        p = float(item.get("probability", 0.0))
        m = int(item.get("max_iteration", 0))
        q = _cond_prob(item.get("condition", ""), case_attrs)
        if back_to in v and p > 0 and m > 0:
            v[back_to] += p * m * q

    return v

# -----------------------------
# Main
# -----------------------------

def calculate_optimal_resources(sim_problem, config_path="config.json", num_samples=1000):
    """
    Simple rework-aware sizing at 100% utilization:
      c_task = ceil( lambda_global * visits_per_case[task] * E[S_task] )
    """
    # Load config (optional)
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception:
        config = None

    # Start event -> global arrival rate
    start_events = [e for e in sim_problem.events if e.get_id().endswith("<start_event>")]
    if len(start_events) != 1:
        raise ValueError("Expected exactly one start event")
    start_event = start_events[0]
    prefix = start_event.get_id().split("<")[0]
    mean_interarrival_time = estimate_interarrival_time(start_event.behavior, prefix, num_samples=num_samples)
    arrival_rate = 1.0 / mean_interarrival_time if mean_interarrival_time > 0 else 0.0

    # Rework-aware expected visits per case (per task)
    vpc = _visits_per_case(sim_problem, config)

    # Tasks
    task_start_events = [e for e in sim_problem.events if e.get_id().endswith("<task:start>")]
    resource_needs = {}
    current_resources = {}

    for event in task_start_events:
        task_name = event.get_id().split("<")[0]
        mean_service_time = estimate_service_time(event.behavior, num_samples=num_samples)

        # 100% utilization with rework: lambda_task = lambda_global * visits_per_case
        lambda_task = arrival_rate * float(vpc.get(task_name, 1.0))
        required = lambda_task * mean_service_time
        optimal = max(1, math.ceil(required)) if required > 0 else 1

        # current pool (best-effort: incoming[1])
        try:
            resource_var = event.incoming[1]
            current = len(resource_var.marking)
        except Exception:
            current = 0

        resource_needs[task_name] = optimal
        current_resources[task_name] = current

    # Simple messages
    if any(current_resources[t] < resource_needs[t] for t in resource_needs):
        print("\nThe amount of resources is not ideal and may cause bottlenecks.\n")
    else:
        print("\nResources look adequate (at 100% utilization).\n")

    for task in resource_needs:
        optimal = resource_needs[task]
        current = current_resources[task]
        if current >= optimal:
            print(f"The amount of resources for {task} is already ideal: {current}")
        else:
            print(f"{task} should have {optimal} resources, but currently has {current}")

    return resource_needs
