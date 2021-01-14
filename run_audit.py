#! /opt/conda/bin/python
import json
import flywheel
import os
import sys
import logging

# logging stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('flaudit')
logger.info("{:=^70}\n".format(": flaudit gear manager starting up :"))

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
        logger.error("Gear can only be run from the project level!")
        sys.exit(0)

    project_container = fw.get(parent_container.id)
    project_label = project_container.label

    template = config.get('Template', '')

    call1 = "python /flywheel/v0/flaudit/cli/gather_data.py --project {} --destination /flywheel/v0/output/".format(project_label.replace(" ", "\ "))
    logger.info("Attempting to gather data with call:\n\t" + call1)
    call1 = call1 + " --api-key " + api_key
    os.system(call1)

    call2 = "R -e \"rmarkdown::render(input = '/flywheel/v0/flaudit/R/AuditReport.Rmd', output_dir = '/flywheel/v0/output/', params = list(project_name = '{}', attachments_csv = '/flywheel/v0/output/attachments.csv', seqinfo_csv = '/flywheel/v0/output/seqinfo.csv', jobs_csv = '/flywheel/v0/output/jobs.csv', bids_csv = '/flywheel/v0/output/bids.csv', template = '{}'))\"".format(project_label, template)
    logger.info("Building audit report with call:\n\t" + call2)
    os.system(call2)

    logger.info("{:=^70}\n".format(": Done! :"))
