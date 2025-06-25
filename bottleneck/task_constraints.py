from datetime import datetime, timedelta
from simpn.simulator import SimProblem
import simpn.prototypes as prototype

def make_guard(constraint):
    initial_time = datetime(2020, 1, 1)  # Matches EventLogReporter default
    def guard(*args):
        t = args[-1]  # Simulation time in minutes
        dt = initial_time + timedelta(minutes=t)
        if constraint["type"] == "day_of_week":
            return dt.strftime("%A") in constraint["days"]
        elif constraint["type"] == "date_range":
            day = dt.day
            return constraint["start_day"] <= day <= constraint["end_day"]
        else:
            return True  # Default to always enabled if type is unrecognized
    return guard

def apply_task_constraints(sim_problem: SimProblem, config):
    task_constraints = config.get("task_constraints", {})
    if not task_constraints:
        print("No task constraints applied.")
    else:
        print("\nApplying Task Constraints:\n")
        for task_name, constraint in task_constraints.items():
            for proto in sim_problem.prototypes:
                if proto.name == task_name and isinstance(proto, prototype.BPMNTask):
                    start_event = proto.events[0]  # Start event of the task
                    time_var = sim_problem.var("time")  # Access or create time variable
                    original_incoming = start_event.incoming
                    start_event.set_inflow(original_incoming + [time_var])
                    original_behavior = start_event.behavior
                    start_event.behavior = lambda *args: original_behavior(*args[:len(original_incoming)])
                    guard = make_guard(constraint)
                    start_event.set_guard(guard)
                    # Print the applied constraint
                    if constraint["type"] == "day_of_week":
                        days = ', '.join(constraint["days"])
                        print(f"Applied task constraint to {task_name}: only on {days}")
                    elif constraint["type"] == "date_range":
                        start_day = constraint["start_day"]
                        end_day = constraint["end_day"]
                        print(f"Applied task constraint to {task_name}: between day {start_day} and {end_day} of the month")
                    break
        # Add warning about potential bottlenecks
        if task_constraints:
            constrained_tasks = list(task_constraints.keys())
            print(f"Warning: Task constraints applied to {', '.join(constrained_tasks)} may cause bottlenecks.")