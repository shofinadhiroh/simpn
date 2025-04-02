from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp, uniform, choice
#from simpn.reporters import EventLogReporter
from custom_reporters import EnhancedEventLogReporter
from simpn.prototypes import BPMNStartEvent, BPMNTask, BPMNEndEvent
import json
from rework import setup_rework, setup_long_rework

# Instantiate the simulation problem
loan_process = SimProblem()

# Define places (variables) for the process
waiting = loan_process.add_var("waiting")           # Applications waiting to be reviewed.
review_done = loan_process.add_var("review_done")     # Applications that have been reviewed.
credit_done = loan_process.add_var("credit_done")     # Applications that have passed credit check.
decision_approved = loan_process.add_var("decision_approved")
decision_rejected = loan_process.add_var("decision_rejected")

# Define resources.
loan_officer = loan_process.add_var("loan_officer")
loan_officer.put("officer1")        # One loan officer for review.

credit_analyst = loan_process.add_var("credit_analyst")
credit_analyst.put("analyst1")      # One credit analyst for credit check.

with open('config.json', 'r') as f:
    config = json.load(f)

# Define start behavior to generate case attributes
def start_behavior():
    attributes = {}
    for attr_name, attr_config in config.get("case_attributes", {}).items():
        attr_type = attr_config["type"]
        if attr_type == "numerical":
            value = uniform(attr_config["min"], attr_config["max"])
        elif attr_type == "string":
            value = choice(attr_config["values"])
        elif attr_type == "boolean":
            value = choice([True, False])
        else:
            raise ValueError(f"Unsupported attribute type: {attr_type}")
        attributes[attr_name] = value
    # Token format: (attributes, rework_counts)
    return [SimToken((attributes, {}))]

# Start Event: Application Received
BPMNStartEvent(
    loan_process,
    [],            # No input place.
    [waiting],     # New application token goes into the waiting queue.
    "application_received",
    lambda: exp(1/20),
    behavior=start_behavior
)

# Task: Review Application
def review_application_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [waiting, loan_officer],         # Consumes an application and the loan officer.
    [review_done, loan_officer],     # Outputs the reviewed application and returns the loan officer.
    "review_application",
    review_application_start
)

def credit_check_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [review_done, credit_analyst],   # Consumes a reviewed application and the credit analyst.
    [credit_done, credit_analyst],   # Outputs the application after credit check and returns the analyst.
    "credit_check",
    credit_check_start
)

# Choice Event: Decide whether to approve or reject (50% chance each)
def choose_decision(token):
    if choice([True, False]):
        return [SimToken(token), None]  # Approved branch.
    else:
        return [None, SimToken(token)]  # Rejected branch.

loan_process.add_event(
    [credit_done],
    [decision_approved, decision_rejected],
    choose_decision,
    name="choose_decision"
)

# End Events for the decision branches.
BPMNEndEvent(loan_process, [decision_approved], [], "application_approved")
BPMNEndEvent(loan_process, [decision_rejected], [], "application_rejected")

setup_rework(loan_process, config)
setup_long_rework(loan_process, config)

# Run the simulation with the enhanced reporter
#reporter = EventLogReporter("choice.csv")
reporter = EnhancedEventLogReporter("choice.csv", config=config)
loan_process.simulate(24*60, reporter)  # 10 days in minutes
reporter.close()