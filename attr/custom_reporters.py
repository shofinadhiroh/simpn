from datetime import datetime, timedelta
from simpn.reporters import Reporter, TimeUnit

class EnhancedEventLogReporter(Reporter):
    """
    An enhanced event log reporter that logs events with additional case attributes.
    Attributes are extracted from simulation tokens to match the simulation's case attributes.

    :param filename: The name of the file to store the event log.
    :param config: A dictionary containing configuration, including optional 'case_attributes'.
    :param sim_problem: The SimProblem instance to access simulation state.
    :param timeunit: The TimeUnit of simulation time (default: MINUTES).
    :param initial_time: A datetime value for the simulation start (default: 2020-01-01).
    :param time_format: A datetime formatting string (default: "%Y-%m-%d %H:%M:%S.%f").
    :param separator: The separator to use in the log (default: ",").
    """
    def __init__(self, filename, config=None, sim_problem=None, timeunit=TimeUnit.MINUTES, 
                 initial_time=datetime(2020, 1, 1), time_format="%Y-%m-%d %H:%M:%S.%f", separator=","):
        # Initialize basic attributes
        self.task_start_times = {}  # Store task start times
        self.timeunit = timeunit
        self.initial_time = initial_time
        self.time_format = time_format
        self.sep = separator
        self.logfile = open(filename, "wt")
        self.sim_problem = sim_problem  # Access to simulation state
        self.case_attributes = {}  # Store attributes per case_id from simulation

        # Handle case attributes from config
        self.case_attributes_config = config.get("case_attributes", {}) if config else {}
        self.attribute_names = list(self.case_attributes_config.keys())

        # Write the CSV header with base columns plus attribute names
        base_columns = ["case_id", "task", "resource", "start_time", "completion_time"]
        header = base_columns + self.attribute_names
        self.logfile.write(self.sep.join(header) + "\n")

    def displace(self, time):
        """Convert simulation time to a datetime based on the time unit."""
        if self.timeunit == TimeUnit.MINUTES:
            return self.initial_time + timedelta(minutes=time)
        elif self.timeunit == TimeUnit.SECONDS:
            return self.initial_time + timedelta(seconds=time)
        elif self.timeunit == TimeUnit.HOURS:
            return self.initial_time + timedelta(hours=time)
        elif self.timeunit == TimeUnit.DAYS:
            return self.initial_time + timedelta(days=time)
        return None

    def log_event(self, case_id, task, resource, start_time, completion_time, attributes):
        """Log an event with case attributes from the simulation."""
        line = [
            str(case_id),
            task,
            str(resource),
            start_time.strftime(self.time_format),
            completion_time.strftime(self.time_format)
        ]
        # Use the provided attributes
        for attr_name in self.attribute_names:
            value = attributes.get(attr_name, "")
            line.append(str(value))
        self.logfile.write(self.sep.join(line) + "\n")
        self.logfile.flush()

    def callback(self, timed_binding):
        """Process simulation events and log them with attributes from tokens."""
        (binding, time, event) = timed_binding
        
        if event.get_id().endswith("<start_event>"):
            # For start events, binding[0][1].value is the new case_id (string), coming from the timer place.
            case_id = binding[0][1].value  # e.g., "order_placed0"

            # After fire(...), tokens are already produced on the event's outgoing places.
            attributes = None
            found = False

            # Search all outgoing places for the newly produced case token
            for out_place in event.outgoing:
                # Each place has a .marking of SimToken objects
                for tok in out_place.marking:
                    # Case tokens have the shape: (case_id, (attributes, rework_counts))
                    val = tok.value
                    if isinstance(val, tuple) and len(val) >= 2 and val[0] == case_id:
                        # Extract attributes; value[1] is (attributes, rework_counts)
                        # If your model sometimes has no rework_counts, keep a safe fallback.
                        try:
                            attrs = val[1][0]  # expected (attributes, rework_counts)
                        except Exception:
                            # fallback if value[1] is already the attributes dict
                            attrs = val[1]

                        attributes = attrs
                        self.case_attributes[case_id] = attributes
                        found = True
                        break
                if found:
                    break

            if not found:
                # Helpful message that doesn’t assume any specific place name
                raise ValueError(f"Start-event case token for case_id '{case_id}' not found on any outgoing place of event '{event.get_id()}'")

            # Log the start event (no resource, instantaneous for start)
            event_name = event.get_id()[:event.get_id().index("<")]
            self.log_event(case_id, event_name, "", self.displace(time), self.displace(time), attributes=attributes)


        elif event.get_id().endswith("<task:start>"):
            case_token = binding[0][1].value  # (case_id, (attributes, rework_counts))
            case_id = case_token[0]  # e.g., "application_received0"
            task = event.get_id()[:event.get_id().index("<")]
            self.task_start_times[(case_id, task)] = time
            # Attributes should already be set from start event, but can verify if needed

        elif event.get_id().endswith("<task:complete>"):
            busy_token = binding[0][1].value  # ((case_id, (attributes, rework_counts)), resource)
            case_id = busy_token[0][0]  # e.g., "application_received0"
            task = event.get_id()[:event.get_id().index("<")]
            resource = busy_token[1]
            if (case_id, task) in self.task_start_times:
                start_time = self.displace(self.task_start_times[(case_id, task)])
                completion_time = self.displace(time)
                attributes = self.case_attributes[case_id]
                self.log_event(case_id, task, resource, start_time, completion_time, attributes=attributes)
                del self.task_start_times[(case_id, task)]

        elif event.get_id().endswith("<intermediate_event>") or event.get_id().endswith("<end_event>"):
            case_token = binding[0][1].value  # (case_id, (attributes, rework_counts))
            case_id = case_token[0]  # e.g., "application_received0"
            event_name = event.get_id()[:event.get_id().index("<")]
            attributes = self.case_attributes[case_id]
            self.log_event(case_id, event_name, "", self.displace(time), self.displace(time), attributes=attributes)

    def close(self):
        """Close the log file."""
        self.logfile.close()