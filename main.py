from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp, uniform, random
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

from simpn.config_apply import apply_configuration

# ---------------------------------------------------
# 1) Instantiate the simulation problem
# ---------------------------------------------------
process = SimProblem()

# ---------------------------------------------------
# 2) Define places (queues)
# ---------------------------------------------------
waiting       = process.add_var("waiting")               # Initial arrivals
to_review     = process.add_var("to_review")             # Feeds review_application
review_done   = process.add_var("review_done")           # After review
missing_doc   = process.add_var("missing_doc")           # Cases that need doc
pass_credit   = process.add_var("pass_credit")           # Cases that proceed to credit
credit_done   = process.add_var("credit_done")           # After credit check
to_split      = process.add_var("to_split")              # For parallel branches
doc_queue     = process.add_var("doc_queue")             # Document verification
risk_queue    = process.add_var("risk_queue")            # Risk assessment
doc_done      = process.add_var("doc_done")              # After doc verification
risk_done     = process.add_var("risk_done")             # After risk assessment
join_done     = process.add_var("join_done")             # Merged parallel tasks
approved      = process.add_var("approved")              # Approved apps
rejected      = process.add_var("rejected")              # Rejected apps

# ---------------------------------------------------
# 3) Define resources
# ---------------------------------------------------
loan_officer   = process.add_var("loan_officer")
loan_officer.put("officer1")
loan_officer.put("officer2")
loan_officer.put("officer3")
loan_officer.put("officer4")
loan_officer.put("officer5")

credit_analyst = process.add_var("credit_analyst")
credit_analyst.put("analyst1")
credit_analyst.put("analyst2")
credit_analyst.put("analyst3")
credit_analyst.put("analyst4")
credit_analyst.put("analyst5")
credit_analyst.put("analyst6")
credit_analyst.put("analyst7")
credit_analyst.put("analyst8")
credit_analyst.put("analyst9")
credit_analyst.put("analyst10")

verifier = process.add_var("verifier")
verifier.put("verifier1")
verifier.put("verifier2")
verifier.put("verifier3")
verifier.put("verifier4")
verifier.put("verifier5")

risk_analyst = process.add_var("risk_analyst")
risk_analyst.put("risk1")
risk_analyst.put("risk2")
risk_analyst.put("risk3")
risk_analyst.put("risk4")
risk_analyst.put("risk5")
risk_analyst.put("risk6")
risk_analyst.put("risk7")
risk_analyst.put("risk8")
risk_analyst.put("risk9")
risk_analyst.put("risk10")

# ---------------------------------------------------
# 4) Start Event: Application Received (every 20 min)
# ---------------------------------------------------
prototype.BPMNStartEvent(
    process,
    [],
    [waiting],
    "application_received",
    lambda: exp(2)*60
)

# ---------------------------------------------------
# 5) Merge: from 'waiting' to 'to_review'
# ---------------------------------------------------
# We simply pass the token from waiting -> to_review
def pass_to_review(token):
    return [SimToken(token)]

process.add_event(
    [waiting],
    [to_review],
    pass_to_review,
    name="waiting_to_review"
)

# ---------------------------------------------------
# 6) Task: Review Application
# ---------------------------------------------------
# Performed by the loan officer (15–25 minutes).
def start_review(c, r):
    return [SimToken((c, r), delay=uniform(15, 25))]

prototype.BPMNTask(
    process,
    [to_review, loan_officer],
    [review_done, loan_officer],
    "review_application",
    start_review
)

def pass_to_credit(token):
    return [SimToken(token)]

process.add_event(
    [review_done], 
    [pass_credit],
    pass_to_credit, 
    name="waiting_to_credit")

# ---------------------------------------------------
# 9) Task: Credit Check
# ---------------------------------------------------
# Performed by the credit analyst (15–25 minutes).
def start_credit(c, r):
    return [SimToken((c, r), delay=uniform(55, 75))]

prototype.BPMNTask(
    process,
    [pass_credit, credit_analyst],
    [credit_done, credit_analyst],
    "credit_check",
    start_credit
)

# ---------------------------------------------------
# 10) Move from Credit Check to Parallel Split
# ---------------------------------------------------
def pass_along(token):
    return [SimToken(token)]

process.add_event(
    [credit_done],
    [to_split],
    pass_along,
    name="move_to_split"
)

# ---------------------------------------------------
# 11) Parallel Split: Document Verification + Risk Assessment
# ---------------------------------------------------
process.add_event(
    [to_split],
    [doc_queue, risk_queue],
    lambda c: [SimToken(c), SimToken(c)],
    name="parallel_split"
)

# ---------------------------------------------------
# 12) Document Verification (10–15 min)
# ---------------------------------------------------
def start_doc(c, r):
    return [SimToken((c, r), delay=uniform(10, 15))]

prototype.BPMNTask(
    process,
    [doc_queue, verifier],
    [doc_done, verifier],
    "document_verification",
    start_doc
)

# ---------------------------------------------------
# 13) Risk Assessment (10–15 min)
# ---------------------------------------------------
def start_risk(c, r):
    return [SimToken((c, r), delay=uniform(55, 75))]

prototype.BPMNTask(
    process,
    [risk_queue, risk_analyst],
    [risk_done, risk_analyst],
    "risk_assessment",
    start_risk
)

# ---------------------------------------------------
# 14) Join parallel branches
# ---------------------------------------------------
def join_tokens(t1, t2):
    return [SimToken(t1)]  # guard ensures t1==t2

process.add_event(
    [doc_done, risk_done],
    [join_done],
    join_tokens,
    name="parallel_join",
    guard=lambda t1, t2: t1 == t2
)

# ---------------------------------------------------
# 15) Final Decision: 70% approve, 30% reject
# ---------------------------------------------------
def final_choice(token):
    if random() < 0.7:
        return [SimToken(token), None]
    else:
        return [None, SimToken(token)]

process.add_event(
    [join_done],
    [approved, rejected],
    final_choice,
    name="final_choice"
)

# ---------------------------------------------------
# 16) End Events
# ---------------------------------------------------
prototype.BPMNEndEvent(process, [approved], [], "application_approved")
prototype.BPMNEndEvent(process, [rejected], [], "application_rejected")

# ---------------------------------------------------
# 17) Run the Simulation
# ---------------------------------------------------
#reporter = EventLogReporter("loan_sim.csv")
#process.simulate(30*1440, reporter)  # 24 hours = 1440 minutes
#reporter.close()

apply_configuration(process, "config.json")
