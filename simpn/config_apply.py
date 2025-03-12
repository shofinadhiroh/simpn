import json
import os
import shutil
from datetime import datetime, timedelta
from simpn.simulator import SimProblem
# Import filtering functions and CalendarReporter from filtering.py
from simpn.filtering import CalendarReporter, simulate_calendar, filter_by_working_hours_by_end_task, filter_by_weekdays, filter_complete_cases
# Import rework functions from rework.py
from simpn.rework import postprocess_single_rework, postprocess_long_rework, postprocess_inserted_loop

def apply_configuration(problem: SimProblem, config_file: str):
    with open(config_file, "r") as f:
        config = json.load(f)

    # Determine simulation duration from calendar_period.
    calendar_period = config.get("calendar_period", None)
    if calendar_period:
        calendar_start = datetime.strptime(calendar_period["start"], "%Y-%m-%d %H:%M:%S")
        calendar_end = datetime.strptime(calendar_period["end"], "%Y-%m-%d %H:%M:%S")
        simulation_duration = (calendar_end - calendar_start).total_seconds() / 60.0  # minutes
    else:
        simulation_duration = 1e9
        calendar_start = datetime.now()

    base_log = config.get("event_log_filename", "my_event_log.csv")
    final_log = config.get("final_event_log_filename", "my_event_log_final.csv")
    separator = config.get("separator", ";")

    config_end_tasks = config.get("end_tasks", ["application_completed"])
    working_hours = config.get("working_hours", None)
    allowed_weekdays = config.get("allowed_weekdays", [0, 1, 2, 3, 4])  # default Monday–Friday

    # Use the CalendarReporter to run the simulation (without trace limit).
    reporter = CalendarReporter(problem, base_log, separator, initial_time=calendar_start)
    simulate_calendar(problem, simulation_duration, reporter)
    print(f"Simulation ended. Started={reporter.started_count}, Completed={reporter.completed_count}.")

    # Apply rework scenarios.
    single_rework_scenarios = config.get("single_rework_scenarios", [])
    for scenario in single_rework_scenarios:
        if scenario.get("enabled", False):
            print(f"Applying single rework scenario on {base_log} => {final_log}")
            postprocess_single_rework(base_log, final_log, scenario, separator)
            base_log = final_log

    long_rework_scenarios = config.get("long_rework_scenarios", [])
    for scenario in long_rework_scenarios:
        if scenario.get("enabled", False):
            print(f"Applying long rework scenario on {base_log} => {final_log}")
            postprocess_long_rework(base_log, final_log, scenario, separator)
            base_log = final_log

    inserted_loop_scenarios = config.get("inserted_loop_scenarios", [])
    for scenario in inserted_loop_scenarios:
        if scenario.get("enabled", False):
            print(f"Applying inserted loop rework scenario on {base_log} => {final_log}")
            postprocess_inserted_loop(base_log, final_log, scenario, separator)
            base_log = final_log

    # Ensure final log exists.
    if not os.path.exists(final_log):
        print(f"Final log file {final_log} not found; copying base log to {final_log}.")
        shutil.copy(base_log, final_log)

    # Apply filtering with debug prints.
    print("Starting filtering process...")
    if working_hours:
        print("Filtering event log by working hours (all tasks).")
        filter_by_working_hours_by_end_task(final_log, final_log, working_hours, config_end_tasks, separator)
    else:
        print("No working hours defined in config; skipping working hours filter.")
    print("Filtering event log by allowed weekdays.")
    filter_by_weekdays(final_log, final_log, allowed_weekdays, config_end_tasks, separator)
    print("Filtering out incomplete cases.")
    filter_complete_cases(final_log, final_log, separator, config_end_tasks)

    print("Run with configuration complete.")