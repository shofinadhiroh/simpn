from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
import simpn.prototypes as prototype
from simpn.reporters import EventLogReporter, ProcessReporter
import json

# Instantiate a simulation problem
agency = SimProblem()

# Define variables (queues) for the process flow
waiting = agency.add_var("waiting")
to_pre_approval = agency.add_var("to_pre_approval")
to_loan_approval = agency.add_var("to_loan_approval")
to_approve = agency.add_var("to_approve")
completed = agency.add_var("completed")

# Define resources
staff = agency.add_var("staff")
staff.put("s1")  # Staff member 1

manager = agency.add_var("manager")
manager.put("m1")

# Define interarrival time for applications (mean 10 minutes)
def interarrival_time():
    return exp(5)*60

# 1. Start Event: Receive Application
prototype.BPMNStartEvent(agency, [], [waiting], "receive_application", interarrival_time)

# 2. Intermediate Event: Review Application (no delay)
prototype.BPMNIntermediateEvent(
    agency, 
    [waiting], 
    [to_pre_approval], 
    "review_application", 
    lambda c: [SimToken(c, delay=0)]
)

# 3. Task: Pre Approval Check (requires staff, mean processing time 20 minutes)
def pre_approval_check(c, r):
    return [SimToken((c, r), delay=uniform(60, 75))]

prototype.BPMNTask(
    agency, 
    [to_pre_approval, staff], 
    [to_loan_approval, staff], 
    "pre_approval_check", 
    pre_approval_check
)

# 4. Intermediate Event: Loan Approval (no delay)
prototype.BPMNIntermediateEvent(
    agency, 
    [to_loan_approval], 
    [to_approve], 
    "loan_approval", 
    lambda c: [SimToken(c, delay=0)]
)

# 5. Task: Approve Application (requires staff, mean processing time 15 minutes)
def approve_application(c, r):
    return [SimToken((c, r), delay=uniform(30, 45))]

prototype.BPMNTask(
    agency, 
    [to_approve, manager], 
    [completed, manager], 
    "approve_application", 
    approve_application
)

# 6. End Event: Conclude the process
prototype.BPMNEndEvent(agency, [completed], [], "end")

# Run the simulation
reporter = EventLogReporter("test.csv")
agency.simulate(300*60, reporter)  # 10 days in minutes
reporter.close()