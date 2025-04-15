from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp, uniform, choice
#from simpn.reporters import EventLogReporter
from custom_reporters import EnhancedEventLogReporter
from simpn.prototypes import BPMNStartEvent, BPMNTask, BPMNEndEvent
import json
from rework import setup_rework, setup_long_rework
from case_attributes import start_behavior

# Instantiate the simulation problem
loan_process = SimProblem()

# Define places (variables) for the process
waiting = loan_process.add_var("waiting")           # Applications waiting to be reviewed.
review_done = loan_process.add_var("review_done")     # Applications that have been reviewed.
credit_done = loan_process.add_var("credit_done")     # Applications that have passed the offer creation.
email_sent = loan_process.add_var("email_sent")
called = loan_process.add_var("called")
decision_informed = loan_process.add_var("decision_informed")

# Define resources.
loan_officer = loan_process.add_var("loan_officer")
loan_officer.put("officer1")        # One loan officer for review.

credit_analyst = loan_process.add_var("credit_analyst")
credit_analyst.put("analyst1")      # One credit analyst for offer creation.

# New resource for the final tasks.
notifier = loan_process.add_var("notifier")
notifier.put("notifier1")           # Always available notifier resource.

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

# Task: Create Offer (formerly credit_check)
def create_offer_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [review_done, credit_analyst],   # Consumes a reviewed application and the credit analyst.
    [credit_done, credit_analyst],   # Outputs the application after offer creation and returns the analyst.
    "create_offer",
    create_offer_start
)

# Choice Event: Decide whether to approve or reject (50% chance each)
def choose_decision(token):
    if choice([True, False]):
        return [SimToken(token), None]  # Approved branch.
    else:
        return [None, SimToken(token)]  # Rejected branch.

loan_process.add_event(
    [credit_done],
    [email_sent, called],
    choose_decision,
    name="choose_decision"
)

def send_email_start(c, r):
    return [SimToken((c, r), delay=0)]

BPMNTask(
    loan_process,
    [email_sent, notifier],
    [decision_informed, notifier],
    "send_email",
    send_email_start
)

# Task: Application Rejected Task
def call_start(c, r):
    return [SimToken((c, r), delay=0)]

BPMNTask(
    loan_process,
    [called, notifier],
    [decision_informed, notifier],
    "call",
    call_start
)

# End Event: Application Approved (formerly inform_decision)
BPMNEndEvent(loan_process, [decision_informed], [], "application_approved")

#setup_rework(loan_process, config)
setup_long_rework(loan_process, config)

# Run the simulation with the enhanced reporter
#reporter = EventLogReporter("choice2.csv")
reporter = EnhancedEventLogReporter("choice2.csv", config=config, sim_problem=loan_process)
loan_process.simulate(24*60, reporter)  # 10 days in minutes
reporter.close()