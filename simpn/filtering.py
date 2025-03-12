import csv
from datetime import datetime, timedelta
from simpn.reporters import EventLogReporter, TimeUnit
from simpn.simulator import SimToken

# ---------- Log I/O and Utility Functions ----------

def read_event_log(filename: str, separator: str):
    with open(filename, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=separator)
        return [row for row in reader]

def write_event_log(rows, filename: str, separator: str):
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = ["case_id", "task", "resource", "start_time", "completion_time"]
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=separator)
        writer.writeheader()
        writer.writerows(rows)

def group_by_case(rows):
    cases = {}
    for row in rows:
        cid = row["case_id"]
        if cid not in cases:
            cases[cid] = []
        cases[cid].append(row)
    return cases

def parse_times(row):
    try:
        st = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S.%f")
        ct = datetime.strptime(row["completion_time"], "%Y-%m-%d %H:%M:%S.%f")
        return (st, ct)
    except Exception as e:
        print(f"Time parse error in row {row}: {e}")
        return None

def shift_row_time(row, delta: timedelta):
    times = parse_times(row)
    if not times:
        return
    st, ct = times
    st += delta
    ct += delta
    row["start_time"] = st.strftime("%Y-%m-%d %H:%M:%S.%f")
    row["completion_time"] = ct.strftime("%Y-%m-%d %H:%M:%S.%f")

# ---------- Filtering Functions ----------

def filter_by_working_hours_by_end_task(log_filename: str, final_filename: str, working_hours: dict, config_end_tasks: list, separator: str):
    rows = read_event_log(log_filename, separator)
    if not rows:
        print("No rows to filter by working hours.")
        return
    cases = group_by_case(rows)
    try:
        working_start = datetime.strptime(working_hours["start"], "%H:%M:%S").time()
        working_end = datetime.strptime(working_hours["end"], "%H:%M:%S").time()
    except Exception as e:
        print(f"Error parsing working hours: {e}")
        return

    filtered_rows = []
    for cid, crows in cases.items():
        all_within_hours = True
        for row in crows:
            start_dt = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S.%f").time()
            end_dt = datetime.strptime(row["completion_time"], "%Y-%m-%d %H:%M:%S.%f").time()
            if not (working_start <= start_dt <= working_end and working_start <= end_dt <= working_end):
                all_within_hours = False
                print(f"Case {cid} has task {row['task']} outside working hours ({start_dt}–{end_dt}).")
                break
        if all_within_hours:
            filtered_rows.extend(crows)
        else:
            print(f"Case {cid} filtered out due to tasks outside working hours.")
    write_event_log(filtered_rows, final_filename, separator)
    print(f"Working hours filtered event log saved to '{final_filename}'.")

def filter_by_weekdays(log_filename: str, final_filename: str, allowed_weekdays: list, config_end_tasks: list, separator: str):
    rows = read_event_log(log_filename, separator)
    if not rows:
        print("No rows to filter by weekdays.")
        return
    cases = group_by_case(rows)
    filtered_rows = []
    for cid, crows in cases.items():
        end_event = next((r for r in crows if r["task"] in config_end_tasks), None)
        if not end_event:
            print(f"Case {cid} has no end task; filtering out.")
            continue
        end_dt = datetime.strptime(end_event["completion_time"], "%Y-%m-%d %H:%M:%S.%f")
        if end_dt.weekday() in allowed_weekdays:
            filtered_rows.extend(crows)
        else:
            print(f"Case {cid} completed on weekday {end_dt.weekday()} which is not allowed; filtering out.")
    write_event_log(filtered_rows, final_filename, separator)
    print(f"Weekday filtered event log saved to '{final_filename}'.")

def filter_complete_cases(log_filename: str, final_filename: str, separator: str, end_tasks: list):
    rows = read_event_log(log_filename, separator)
    if not rows:
        print("Event log is empty. No filtering applied.")
        return
    cases = group_by_case(rows)
    complete_rows = []
    for cid, crows in cases.items():
        if any(row["task"] in end_tasks for row in crows):
            complete_rows.extend(crows)
        else:
            print(f"Case {cid} is incomplete and will be filtered out.")
    write_event_log(complete_rows, final_filename, separator)
    print(f"Filtered complete cases saved to '{final_filename}'.")

# ---------- Calendar Reporter (for simulation without trace limit) ----------
class CalendarReporter(EventLogReporter):
    """
    A reporter that converts simulation time (in minutes) into calendar timestamps.
    """
    def __init__(self, problem, filename: str, separator: str, initial_time: datetime = None):
        super().__init__(filename, TimeUnit.MINUTES, separator=separator)
        self.problem = problem
        self.started_count = 0
        self.completed_count = 0
        self.initial_time = initial_time if initial_time is not None else datetime.now()

    def convert_time(self, sim_time: float) -> str:
        real_time = self.initial_time + timedelta(minutes=sim_time)
        return real_time.strftime("%Y-%m-%d %H:%M:%S.%f")

    def callback(self, timed_binding):
        super().callback(timed_binding)
        (binding, time, event) = timed_binding
        eid = event.get_id()
        if eid.endswith("<start_event>"):
            self.started_count += 1
        if eid.endswith("<end_event>"):
            self.completed_count += 1

def simulate_calendar(problem, duration: float, reporter: CalendarReporter):
    problem.simulate(duration, reporter)
    print(f"Simulation ended. Started={reporter.started_count}, Completed={reporter.completed_count}.")