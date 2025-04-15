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
approved = loan_process.add_var("approved")    

# New places for the parallel tasks
document_queue = loan_process.add_var("document_queue")    # Token for verify_document task.
risk_queue     = loan_process.add_var("risk_queue")        # Token for assess_risk task.
verify_done    = loan_process.add_var("verify_done")       # Completion of document verification.
risk_done      = loan_process.add_var("risk_done")         # Completion of risk assessment.
join_done      = loan_process.add_var("join_done")         # Token after joining parallel tasks.

# Define resources.
loan_officer = loan_process.add_var("loan_officer")
loan_officer.put("officer1")        # One loan officer for review.

credit_analyst = loan_process.add_var("credit_analyst")
credit_analyst.put("analyst1")      # One credit analyst for credit check.

document_verifier = loan_process.add_var("document_verifier")
document_verifier.put("verifier1")

risk_assessor = loan_process.add_var("risk_assessor")
risk_assessor.put("assessor1")

loan_manager = loan_process.add_var("loan_manager")
loan_manager.put("manager1")        # One loan manager for approval.

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

# Parallel Split: Split token from credit_done into two branches.
loan_process.add_event(
    [credit_done],
    [document_queue, risk_queue],
    lambda c: [SimToken(c), SimToken(c)],
    name="parallel_split"
)

# Task: Verify Document (Parallel Task 1)
def verify_document_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [document_queue, document_verifier],
    [verify_done, document_verifier],
    "verify_document",
    verify_document_start
)

# Task: Assess Risk (Parallel Task 2)
def assess_risk_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [risk_queue, risk_assessor],
    [risk_done, risk_assessor],
    "assess_risk",
    assess_risk_start
)

# Parallel Join: Synchronize tokens from verify_document and assess_risk.
loan_process.add_event(
    [verify_done, risk_done],
    [join_done],
    lambda c1, c2: [SimToken(c1)],
    name="parallel_join",
    guard=lambda c1, c2: c1 == c2
)

# Task: Loan Approval (after the parallel tasks have joined)
def loan_approval_start(c, r):
    return [SimToken((c, r), delay=exp(1/9))]

BPMNTask(
    loan_process,
    [join_done, loan_manager],
    [approved, loan_manager],
    "loan_approval",
    loan_approval_start
)

# End Event
BPMNEndEvent(loan_process, [approved], [], "application_approved")

#setup_rework(loan_process, config)
setup_long_rework(loan_process, config)

# Run the simulation with the enhanced reporter
#reporter = EventLogReporter("parallel.csv")
reporter = EnhancedEventLogReporter("parallel.csv", config=config, sim_problem=loan_process)
loan_process.simulate(24*60, reporter)  # 10 days in minutes
reporter.close()