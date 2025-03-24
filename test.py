from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype
import json
from rework import setup_rework, setup_long_rework

# Instantiate the simulation problem
shop = SimProblem()

# Define places (variables) for the process
review_queue = shop.add_var("review queue")
to_decide = shop.add_var("to decide")
approval_queue = shop.add_var("approval queue")
done = shop.add_var("done")

# Define resources
loan_officer = shop.add_var("loan_officer")
loan_officer.put("officer1")
loan_officer.put("officer2")

loan_manager = shop.add_var("loan_manager")
loan_manager.put("manager1")
loan_manager.put("manager2")
loan_manager.put("manager3")

# Counter for unique case IDs
case_id_counter = 0

# Start Event: Application Received
def start_behavior():
    global case_id_counter
    case_id = case_id_counter
    case_id_counter += 1
    # Token format: (case_id, rework_counts) where rework_counts is a dict
    return [SimToken((case_id, {}))]

prototype.BPMNStartEvent(
    shop,
    [],
    [review_queue],
    "application_received",
    lambda: exp(1/20),
    behavior=start_behavior
)

# Define task start behaviors
def review_application_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

def pre_approval_check_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

def loan_approval_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

# Task: Review Application
prototype.BPMNTask(
    shop,
    [review_queue, loan_officer],
    [to_decide, loan_officer],
    "review_application",
    review_application_start
)

# Task: Pre Approval Check
prototype.BPMNTask(
    shop,
    [to_decide, loan_manager],
    [approval_queue, loan_manager],
    "pre_approval_check",
    pre_approval_check_start
)

# Task: Loan Approval
prototype.BPMNTask(
    shop,
    [approval_queue, loan_manager],
    [done, loan_manager],
    "loan_approval",
    loan_approval_start
)

# End Event
prototype.BPMNEndEvent(shop, [done], [], "application_approved")

# Load configuration and set up rework
with open('config.json', 'r') as f:
    config = json.load(f)
#setup_rework(shop, config)        # Self-loop rework
#setup_long_rework(shop, config)   # Long rework

# Run the simulation
reporter = EventLogReporter("output.csv")
shop.simulate(24*60, reporter)  # 96 hours in minutes
reporter.close()