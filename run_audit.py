#!/usr/bin/env python

import json
import flywheel
import os
import sys

print("here")
print(flywheel)
print(sys.version)
print(dir(os))
with flywheel.GearContext() as context:

    # from the gear context, get the config settings
    config = context.config

    api_key = context.get_input('api_key')['key']
    fw = flywheel.Client(api_key)  # log in to flywheel

    # get the analysis object this gear run will be in
    analysis_id = context.destination['id']
    analysis_container = fw.get(analysis_id)

    parent_container = analysis_container.parent

    if parent_container.type != "project":
        print("Gear can only be run from the project level!")
        sys.exit(0)

    project_container = fw.get(parent_container.id)
    project_label = project_container.label

    workflow = context.get_input_path('workflow')

    call1 = "python /flywheel/v0/flaudit/cli/gather_data.py --project {} --destination /flywheel/v0/output/ --api-key {}".format(
        project_label.replace(" ", "\ "), api_key)
    print("Attempting to gather data with call:")
    print(call1)
    os.system(call1)

    call2 = "R -e \"rmarkdown::render(input = '/flywheel/v0/R/AuditReport.Rmd', output_dir = '/flywheel/v0/output/', params = list(project_name = '{}', attachments_csv = '/flywheel/v0/output/attachments.csv', seqinfo_csv = '/flywheel/v0/output/seqinfo.csv', jobs_csv = '/flywheel/v0/output/jobs.csv', bids_csv = '/flywheel/v0/output/bids.csv', workflow_json = '{}'))\"".format(project_label, workflow)
    print("Building audit report with call:")
    print(call2)
    os.system(call2)

    print("Done!")
