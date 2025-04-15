from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp, uniform, choices
from custom_reporters import EnhancedEventLogReporter
from simpn.prototypes import BPMNStartEvent, BPMNTask, BPMNEndEvent
import json
from rework import setup_rework, setup_long_rework
from case_attributes import start_behavior

# Instantiate the simulation problem
loan_process = SimProblem()

# Define places (variables) for the process
waiting = loan_process.add_var("waiting")           # Applications waiting to be reviewed.
review_done = loan_process.add_var("review_done")   # Applications that have been reviewed.
credit_done = loan_process.add_var("credit_done")   # Applications that have passed credit check.
approved = loan_process.add_var("approved")    

# Define resources
loan_officer = loan_process.add_var("loan_officer")
loan_officer.put("officer1")        # One loan officer for review.

credit_analyst = loan_process.add_var("credit_analyst")
credit_analyst.put("analyst1")      # One credit analyst for credit check.

loan_manager = loan_process.add_var("loan_manager")
loan_manager.put("manager1")        # One loan manager for approval.

# Load configuration first to use in start_behavior
with open('config.json', 'r') as f:
    config = json.load(f)

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

def loan_approval_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [credit_done, loan_manager],     # Consumes an application after credit check and the loan manager.
    [approved, loan_manager],        # Outputs the approved application and returns the manager.
    "loan_approval",
    loan_approval_start
)

# End Event
BPMNEndEvent(loan_process, [approved], [], "application_approved")

#setup_rework(loan_process, config)
setup_long_rework(loan_process, config)

# Run the simulation with the enhanced reporter
reporter = EnhancedEventLogReporter("sequence.csv", config=config, sim_problem=loan_process)
loan_process.simulate(24*60, reporter)  # 10 days in minutes
reporter.close()