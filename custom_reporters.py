from datetime import datetime, timedelta
from random import uniform, choice
from simpn.reporters import Reporter, TimeUnit

class EnhancedEventLogReporter(Reporter):
    """
    An enhanced event log reporter that logs events with additional case attributes.
    Attributes are configurable via a config dictionary and generated when a case starts.
    
    :param filename: The name of the file to store the event log.
    :param config: A dictionary containing configuration, including optional 'case_attributes'.
    :param timeunit: The TimeUnit of simulation time (default: MINUTES).
    :param initial_time: A datetime value for the simulation start (default: 2020-01-01).
    :param time_format: A datetime formatting string (default: "%Y-%m-%d %H:%M:%S.%f").
    :param separator: The separator to use in the log (default: ",").
    """
    def __init__(self, filename, config=None, timeunit=TimeUnit.MINUTES, 
                 initial_time=datetime(2020, 1, 1), time_format="%Y-%m-%d %H:%M:%S.%f", separator=","):
        # Initialize basic attributes
        self.task_start_times = {}  # Store task start times
        self.timeunit = timeunit
        self.initial_time = initial_time
        self.time_format = time_format
        self.sep = separator
        self.logfile = open(filename, "wt")

        # Handle case attributes from config
        self.case_attributes_config = config.get("case_attributes", {}) if config else {}
        self.attribute_names = list(self.case_attributes_config.keys())
        self.case_attributes = {}  # Store attributes per case_id

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

    def log_event(self, case_id, task, resource, start_time, completion_time):
        """Log an event with case attributes."""
        line = [
            str(case_id),
            task,
            str(resource),
            start_time.strftime(self.time_format),
            completion_time.strftime(self.time_format)
        ]
        # Append attribute values for this case
        attributes = self.case_attributes.get(case_id, {})
        for attr_name in self.attribute_names:
            value = attributes.get(attr_name, "")
            line.append(str(value))
        self.logfile.write(self.sep.join(line) + "\n")
        self.logfile.flush()

    def callback(self, timed_binding):
        """Process simulation events and log them with attributes."""
        (binding, time, event) = timed_binding
        
        if event.get_id().endswith("<start_event>"):
            # For start event, case_id is the identifier from invar
            case_id = binding[0][1].value  # e.g., "application_received0"
            # Generate attributes for this case
            self.case_attributes[case_id] = {}
            for attr_name, attr_config in self.case_attributes_config.items():
                attr_type = attr_config["type"]
                if attr_type == "numerical":
                    value = uniform(attr_config["min"], attr_config["max"])
                elif attr_type == "string":
                    value = choice(attr_config["values"])
                elif attr_type == "boolean":
                    value = choice([True, False])
                else:
                    raise ValueError(f"Unsupported attribute type: {attr_type}")
                self.case_attributes[case_id][attr_name] = value
            # Log the start event
            event_name = event.get_id()[:event.get_id().index("<")]
            self.log_event(case_id, event_name, "", self.displace(time), self.displace(time))

        elif event.get_id().endswith("<task:start>"):
            case_token = binding[0][1].value  # (identifier, (case_id, rework_counts))
            case_id = case_token[0]  # identifier, e.g., "application_received0"
            task = event.get_id()[:event.get_id().index("<")]
            self.task_start_times[(case_id, task)] = time

        elif event.get_id().endswith("<task:complete>"):
            busy_token = binding[0][1].value  # ((identifier, (case_id, rework_counts)), resource)
            case_token = busy_token[0]  # (identifier, (case_id, rework_counts))
            case_id = case_token[0]  # identifier, e.g., "application_received0"
            task = event.get_id()[:event.get_id().index("<")]
            resource = busy_token[1]
            if (case_id, task) in self.task_start_times:
                start_time = self.displace(self.task_start_times[(case_id, task)])
                completion_time = self.displace(time)
                self.log_event(case_id, task, resource, start_time, completion_time)
                del self.task_start_times[(case_id, task)]

        elif event.get_id().endswith("<intermediate_event>") or event.get_id().endswith("<end_event>"):
            case_token = binding[0][1].value  # (identifier, (case_id, rework_counts))
            case_id = case_token[0]  # identifier, e.g., "application_received0"
            event_name = event.get_id()[:event.get_id().index("<")]
            self.log_event(case_id, event_name, "", self.displace(time), self.displace(time))

    def close(self):
        """Close the log file."""
        self.logfile.close()