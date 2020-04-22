#!/usr/bin/env python

import json
import flywheel
import os

# context = flywheel.GearContext()
# config = context.config                                   # from the gear context, get the config settings
# 
# fw = context.client # log in to flywheel
# 
# analysis_id = context.destination['id']                   # get the analysis object this gear run will be in
# analysis_container = fw.get(analysis_id)
# project_container = fw.get(analysis_container.parents['project'])
# session_container = fw.get(analysis_container.parent['id'])
# subject_container = fw.get(session_container.parents['subject'])

project_label = "gear_testing" # project_label = project_container.label

call1 = "python /flywheel/v0/flaudit/cli/gather_data.py --project {} --destination /flywheel/v0/output/".format(project_label.replace(" ", "\ "))
print(call1)

call2 = "R -e \"rmarkdown::render(input = '/flywheel/v0/R/AuditReport.Rmd', output_dir = '/flywheel/v0/output/', params = list(project_name = '{}', attachments_csv = '/flywheel/v0/output/attachments.csv', seqinfo_csv = '/flywheel/v0/output/seqinfo.csv', jobs_csv = '/flywheel/v0/output/jobs.csv', bids_csv = '/flywheel/v0/output/bids.csv', workflow_json = '/flywheel/v0/output/workflow.json'))\"".format(project_label)
print(call2)
