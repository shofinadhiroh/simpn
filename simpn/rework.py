import csv
import json
import random
from datetime import datetime, timedelta
from simpn.simulator import SimToken
from simpn.filtering import read_event_log, write_event_log, group_by_case, parse_times, shift_row_time

###############################################################################
# Rework Functions
###############################################################################
def inject_single_rework(case_rows, affected_activity: str, additional_delay: float):
    new_case_rows = []
    rework_injected = False
    for row in case_rows:
        new_case_rows.append(row)
        if not rework_injected and row["task"] == affected_activity:
            times = parse_times(row)
            if not times:
                continue
            st, ct = times
            duration = ct - st
            new_row = row.copy()
            new_start = ct + timedelta(seconds=additional_delay)
            new_end = new_start + duration
            new_row["start_time"] = new_start.strftime("%Y-%m-%d %H:%M:%S.%f")
            new_row["completion_time"] = new_end.strftime("%Y-%m-%d %H:%M:%S.%f")
            new_case_rows.append(new_row)
            rework_injected = True
    if rework_injected:
        inserted_index = None
        count = 0
        for i, r in enumerate(new_case_rows):
            if r["task"] == affected_activity:
                count += 1
                if count == 2:
                    inserted_index = i
                    break
        if inserted_index is not None:
            for i in range(inserted_index+1, len(new_case_rows)):
                shift_row_time(new_case_rows[i], timedelta(seconds=additional_delay))
    return new_case_rows

def postprocess_single_rework(base_log: str, final_log: str, scenario, separator: str):
    affected_activities = scenario.get("affected_activities", [])
    rework_percentage = scenario.get("rework_percentage", 0.15)
    additional_delay = scenario.get("additional_delay", 1.0)
    rows = read_event_log(base_log, separator)
    if not rows:
        print("Base event log empty, skipping single rework.")
        return
    cases = group_by_case(rows)
    final_rows = []
    for cid, crows in cases.items():
        for act in affected_activities:
            if random.random() < rework_percentage:
                print(f"Injecting single rework for {act} in case {cid}")
                crows = inject_single_rework(crows, act, additional_delay)
        final_rows.extend(crows)
    write_event_log(final_rows, final_log, separator)
    print(f"Single rework event log saved to '{final_log}'.")

def inject_long_rework(case_rows, scenario, trigger_index: int, additional_delay: float):
    if "back_to" in scenario:
        return inject_back_to_review_and_credit(case_rows, scenario, trigger_index, additional_delay)
    else:
        return inject_sequence_rework(case_rows, scenario, trigger_index, additional_delay)

def inject_back_to_review_and_credit(case_rows, scenario, trigger_index: int, additional_delay: float):
    target_activities = scenario.get("back_to", [])
    if not target_activities:
        print("Warning: 'back_to' is empty. Skipping.")
        return case_rows
    main_target = target_activities[0]
    last_occ_index = None
    for i in range(trigger_index, -1, -1):
        if case_rows[i]["task"] == main_target:
            last_occ_index = i
            break
    if last_occ_index is None:
        print(f"Warning: No occurrence of '{main_target}' found. Skipping rework.")
        return case_rows
    times_trigger = parse_times(case_rows[trigger_index])
    if not times_trigger:
        return case_rows
    _, trigger_end = times_trigger
    last_row = case_rows[last_occ_index]
    times_back = parse_times(last_row)
    if not times_back:
        return case_rows
    back_start, back_end = times_back
    duration_review = back_end - back_start
    new_case_rows = case_rows.copy()
    insertion_index = trigger_index + 1
    new_review = last_row.copy()
    rework_start = trigger_end + timedelta(seconds=additional_delay)
    rework_end = rework_start + duration_review
    new_review["start_time"] = rework_start.strftime("%Y-%m-%d %H:%M:%S.%f")
    new_review["completion_time"] = rework_end.strftime("%Y-%m-%d %H:%M:%S.%f")
    new_case_rows.insert(insertion_index, new_review)
    insertion_index += 1
    rework_cc_row = {
        "case_id": new_review["case_id"],
        "task": "credit_check",
        "resource": new_review["resource"],
        "start_time": "",
        "completion_time": ""
    }
    rework_cc_duration = timedelta(minutes=15)
    cc_start = rework_end + timedelta(seconds=additional_delay)
    cc_end = cc_start + rework_cc_duration
    rework_cc_row["start_time"] = cc_start.strftime("%Y-%m-%d %H:%M:%S.%f")
    rework_cc_row["completion_time"] = cc_end.strftime("%Y-%m-%d %H:%M:%S.%f")
    new_case_rows.insert(insertion_index, rework_cc_row)
    insertion_index += 1
    shift_delta = duration_review + rework_cc_duration + timedelta(seconds=2 * additional_delay)
    for i in range(insertion_index, len(new_case_rows)):
        shift_row_time(new_case_rows[i], shift_delta)
    return new_case_rows

def inject_sequence_rework(case_rows, scenario, trigger_index: int, additional_delay: float):
    sequence_of_new_activities = scenario.get("sequence_of_new_activities", [])
    if not sequence_of_new_activities:
        print("No sequence_of_new_activities. Skipping rework.")
        return case_rows
    new_case_rows = []
    rework_inserted = False
    final_inserted_end = None
    times_trigger = parse_times(case_rows[trigger_index])
    if not times_trigger:
        return case_rows
    _, trigger_end = times_trigger
    for idx, row in enumerate(case_rows):
        new_case_rows.append(row)
        if idx == trigger_index and not rework_inserted:
            current_start = trigger_end
            for new_act in sequence_of_new_activities:
                current_start += timedelta(seconds=additional_delay)
                step_duration = timedelta(minutes=10)
                current_end = current_start + step_duration
                new_row = row.copy()
                new_row["task"] = new_act
                new_row["start_time"] = current_start.strftime("%Y-%m-%d %H:%M:%S.%f")
                new_row["completion_time"] = current_end.strftime("%Y-%m-%d %H:%M:%S.%f")
                new_case_rows.append(new_row)
                current_start = current_end
            rework_inserted = True
            final_inserted_end = current_start
    if rework_inserted and final_inserted_end:
        inserted_count = 0
        last_idx = None
        for i, r in enumerate(new_case_rows):
            if r["task"] in sequence_of_new_activities:
                inserted_count += 1
                if inserted_count == len(sequence_of_new_activities):
                    last_idx = i
                    break
        if last_idx is not None:
            times_last = parse_times(new_case_rows[last_idx])
            if times_last:
                shift_delta = times_last[1] - times_trigger[1]
                for i in range(last_idx+1, len(new_case_rows)):
                    shift_row_time(new_case_rows[i], shift_delta)
    return new_case_rows

def postprocess_long_rework(base_log: str, final_log: str, scenario, separator: str):
    rework_percentage = scenario.get("rework_percentage", 0.2)
    additional_delay = scenario.get("additional_delay", 2.0)
    trigger_activity = scenario.get("trigger_activity", "credit_check")
    rows = read_event_log(base_log, separator)
    if not rows:
        print("Base event log is empty, skipping long rework.")
        return
    cases = group_by_case(rows)
    final_rows = []
    for cid, crows in cases.items():
        if random.random() < rework_percentage:
            print(f"Injecting long rework in case {cid} triggered by {trigger_activity}")
            triggered = False
            for i, row in enumerate(crows):
                if row["task"] == trigger_activity:
                    crows = inject_long_rework(crows, scenario, i, additional_delay)
                    triggered = True
                    break
            if not triggered:
                print(f"No occurrence of {trigger_activity} in case {cid}, skipping rework.")
            final_rows.extend(crows)
        else:
            final_rows.extend(crows)
    write_event_log(final_rows, final_log, separator)
    print(f"Long rework event log saved to '{final_log}'.")

def postprocess_inserted_loop(base_log, final_log, scenario, separator):
    rows = read_event_log(base_log, separator)
    cases = group_by_case(rows)
    final_rows = []

    for cid, crows in cases.items():
        new_case_rows = []
        iteration_count = 0
        idx = 0
        end_task = None  # Store the end task
        rework_applied = False  # Flag to track if rework has been applied

        # Decide once per case whether to apply the rework
        apply_rework = random.random() < scenario["percentage"]

        while idx < len(crows):
            row = crows[idx]

            # Capture end task (to re-add later if missing)
            if row["task"] in ["application_approved", "application_rejected"]:
                end_task = row

            new_case_rows.append(row)

            # Check if the current task matches the after_activity to insert the loop
            if row["task"] == scenario["after_activity"] and not rework_applied and apply_rework:
                # Randomly determine the number of iterations (between 1 and max_iterations)
                num_iterations = random.randint(1, scenario["max_iterations"])
                # Apply the loop for the determined number of iterations
                for _ in range(num_iterations):
                    iteration_count += 1
                    current_end_time = parse_times(row)[1]

                    # Insert `request_missing_document`
                    loop_start = current_end_time + timedelta(seconds=scenario["additional_delay"])
                    loop_duration = timedelta(minutes=random.uniform(*scenario["processing_time"]))
                    loop_end = loop_start + loop_duration

                    loop_row = {
                        "case_id": row["case_id"],
                        "task": scenario["inserted_activity"],  # request_missing_document
                        "resource": row["resource"],
                        "start_time": loop_start.strftime("%Y-%m-%d %H:%M:%S.%f"),
                        "completion_time": loop_end.strftime("%Y-%m-%d %H:%M:%S.%f")
                    }
                    new_case_rows.append(loop_row)

                    # Insert `review_application` after `request_missing_document`
                    review_start = loop_end + timedelta(seconds=1)  # Small gap to ensure chronological order
                    review_duration = timedelta(minutes=random.uniform(55, 75))
                    review_end = review_start + review_duration

                    review_row = {
                        "case_id": row["case_id"],
                        "task": scenario.get("target_activity", scenario["after_activity"]),  # Use target_activity if provided
                        "resource": row["resource"],
                        "start_time": review_start.strftime("%Y-%m-%d %H:%M:%S.%f"),
                        "completion_time": review_end.strftime("%Y-%m-%d %H:%M:%S.%f")
                    }
                    new_case_rows.append(review_row)

                    # Shift all remaining original events (in crows) after the current idx
                    shift_delta = loop_duration + review_duration + timedelta(seconds=scenario["additional_delay"] + 1)
                    for future_idx in range(idx + 1, len(crows)):
                        shift_row_time(crows[future_idx], shift_delta)

                    # Update the current row to the newly inserted review_application for the next iteration
                    row = review_row

                rework_applied = True  # Mark rework as applied to prevent re-triggering

            idx += 1  # Move to the next event

        # Ensure the end task is included if it was in the original case
        if end_task and end_task["task"] not in [row["task"] for row in new_case_rows]:
            new_case_rows.append(end_task)

        # Sort new_case_rows by start_time to ensure chronological order
        new_case_rows.sort(key=lambda x: parse_times(x)[0])

        # Log the sequence for debugging
        print(f"Case {cid} sequence: {[r['task'] for r in new_case_rows]}")
        final_rows.extend(new_case_rows)

    write_event_log(final_rows, final_log, separator)
    print(f"Inserted loop scenario applied and saved to '{final_log}'.")