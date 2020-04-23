import flywheel
import logging
import warnings
import argparse
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from fw_heudiconv.cli import tabulate
from fw_heudiconv.cli.export import get_nested


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('flaudit')


def get_sessions(client, project_label, subject_labels=None, session_labels=None):
    """Query the flywheel client for a project name
    This function uses the flywheel API to find the first match of a project
    name. The name must be exact so make sure to type it as is on the
    website/GUI.
    Parameters
    ---------
    client
        The flywheel Client class object.
    project_label
        The name of the project to search for.
    subject_labels
        List of subject IDs
    session_labels
        List of session IDs
    Returns
    ---------
    sessions
        A list of session objects
    """
    logger.info("Querying Flywheel server...")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        project_obj = client.projects.find_first(
            'label="{}"'.format(project_label))
        assert project_obj, "Project not found! Maybe check spelling...?"
        logger.debug('Found project: %s (%s)',
                     project_obj['label'], project_obj.id)

    sessions = client.get_project_sessions(project_obj.id)
    # filters
    if subject_labels:
        sessions = [s for s in sessions if s.subject['label']
                    in subject_labels]
    if session_labels:
        sessions = [s for s in sessions if s.label in session_labels]

    sessions = [client.get(s.id) for s in sessions]
    return sessions


def gather_jobs(sessions_list, verbose):
    '''
    Creates a dataframe summarising the gear jobs that have run on the list of sessions
    '''
    logger.info("Collecting gear run information...")
    df = pd.DataFrame()
    for sess in tqdm(sessions_list):

        if len(sess.analyses) < 1:

            # basic_row = {
            #     'job_id': None,
            #     'subject': sess.subject.label,
            #     'session': sess.label,
            #     'gear_name': None,
            #     'gear_version': None,
            #     'run_label': None,
            #     'run_datetime': None,
            #     'run_runtime_mins': None,
            #     'run_status': None
            # }
            #
            # final = pd.DataFrame(basic_row, index=[0])
            #
            # df = pd.concat([df, final])
            continue
        else:
            for al in sess.analyses:

                # for each analysis, get the basic runtime information

                basic_row = {
                    'job_id': al.id,
                    'subject': sess.subject.label,
                    'session': sess.label,
                    'gear_name': al.gear_info['name'],
                    'gear_version': al.gear_info['version'],
                    'run_label': al.label,
                    'run_datetime': al.job['created'],
                    'run_runtime_ms': al.job.profile['elapsed_time_ms'],
                    'run_status': al.job.state
                }

                # create a pandas row
                final = pd.DataFrame(basic_row, index=[0])

                if verbose:

                    # also collect the config and arrange as a long table

                    config = al.job.config['config']

                    if config:
                        for k, v in config.items():
                            if v == "":
                                config[k] = np.nan

                    inputs = al.job.inputs

                    if inputs:
                        vals = list(inputs.values())[0]
                        vals['Inputs_Option'] = list(inputs.keys())[0]
                        inputs = vals
                    else:
                        inputs = {
                            'type': np.nan,
                            'id': np.nan,
                            'name': np.nan,
                            'Inputs_Option': np.nan
                        }

                    config_cols = pd.DataFrame(list(config.items()), columns=[
                                               'Config_Option', 'Config_Value'])
                    inputs_cols = pd.DataFrame(inputs,  index=[0])
                    inputs_cols.rename(columns={
                                       'type': 'Inputs_Attached_To', 'id': 'Inputs_ID', 'name': 'Inputs_Name'}, inplace=True)

                    final = pd.concat(
                        [final, inputs_cols, config_cols], axis=1)

                df = pd.concat([df, final])
                df.loc[:, ~df.columns.str.contains(
                    "Config")] = df.loc[:, ~df.columns.str.contains("Config")].ffill()

    return(df)


def get_bids_from_acq(client, id):

    acq = client.get(id)
    sess_lab = client.get(acq['parents']['session']).label

    niftis = [x for x in acq.files if x.type in ['nifti', 'bval', 'bvec']]

    if not niftis:
        return None
    else:

        rows = []

        for nii in niftis:

            rows.append(get_nested(nii, 'info', 'BIDS'))

        return sess_lab, rows


def gather_bids_for_seqs(client, df):

    bids_df = pd.DataFrame(
        # columns = [
        #'series_id', 'Task', 'Run', 'error_message', 'Ce', 'Filename',
        #'Filename', 'ignore', 'Acq', 'valid', 'template',
        #'Rec', 'Path', 'Folder', 'Echo', 'Modality', 'Dir', 'Mod'
        # ]
    )

    df2 = df.copy()

    for index, row in tqdm(df.iterrows()):
        # print(row['series_id'])
        sess_lab, bids = get_bids_from_acq(client, row['series_id'])
        bids = [x for x in bids if x is not None and x != 'NA']

        if bids:

            bids_df_temp = pd.DataFrame(bids)
            bids_df_temp['series_id'] = row['series_id']
            bids_df_temp['session_id'] = sess_lab

            bids_df = pd.concat([bids_df, bids_df_temp], sort=False)

    return bids_df


def get_session_label(client, col):

    result = []
    for i in col:
        obj = client.get(i).parents.session
        result.append(client.get(obj).label)
    return result


def gather_seqInfo(client, project_label, subject_labels=None, session_labels=None, dry_run=False, unique=False):
    '''
    Runs fw-heudiconv-tabulate to attach sequence information to the gear jobs query
    Inputs:
        args (from argparse)
    '''

    df = tabulate.tabulate_bids(client, project_label, subject_labels=subject_labels,
                                session_labels=session_labels, dry_run=False, unique=False)

    #df_out = gather_bids_for_seqs(client, df)
    df['session_id'] = get_session_label(client, df.series_id)

    return df


def pull_attachments_from_object(obj):

    attachments = obj.files
    data = {
        'Name': [],
        'Type': [],
        'MIMEType': [],
        'Size_kb': []
    }

    for f in attachments:

        data['Name'].append(f['name'])
        data['Type'].append(f['type'])
        data['MIMEType'].append(f['mimetype'])
        data['Size_kb'].append(f['size'])

    return pd.DataFrame(data)


def gather_attachments(client, project_label, project_level=True, subject_level=True, session_level=True, acquisition_level=True, include_images=False):
    '''Loop over Flywheel data and consolidate all objects' attachments
    ---------
    client
        The flywheel Client class object.
    project_label
        The name of the project to search for.
    *_level
        boolean; search attachments at this level
    images
        boolean; include images in the search
    Returns
    ---------
    sessions
        A list of session objects
    '''

    assert any([project_level, subject_level, session_level,
                acquisition_level]), "No attachment levels requested."

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        project_obj = client.projects.find_first(
            'label="{}"'.format(project_label))
        assert project_obj, "Project not found! Maybe check spelling...?"
        logger.debug('Found project: %s (%s)',
                     project_obj['label'], project_obj.id)

    attachments = pd.DataFrame()

    if project_level:

        df = pull_attachments_from_object(project_obj)
        df['Origin_Level'] = "Project"
        df['Origin_Label'] = project_obj.label
        df['Origin_ID'] = project_obj.id

        attachments = pd.concat([attachments, df])

    if subject_level:

        subjects = [client.get(x.id) for x in project_obj.subjects()]

        assert subjects, "No subjects found!"

        for sub in subjects:

            df = pull_attachments_from_object(sub)
            df['Origin_Level'] = "Subject"
            df['Origin_Label'] = sub.label
            df['Origin_ID'] = sub.id

            attachments = pd.concat([attachments, df])

    if session_level:

        sessions = [client.get(x.id)
                    for x in client.get_project_sessions(project_obj.id)]

        assert sessions, "No sessions found!"

        for sess in sessions:

            df = pull_attachments_from_object(sess)
            df['Origin_Level'] = "Session"
            df['Origin_Label'] = sess.label
            df['Origin_ID'] = sess.id

            attachments = pd.concat([attachments, df])

    if acquisition_level:

        sessions = client.get_project_sessions(project_obj.id)

        assert sessions, "No sessions found!"

        for sess in sessions:

            acquisitions = sess.acquisitions()

            for acq in acquisitions:

                df = pull_attachments_from_object(acq)
                df['Origin_Level'] = "Acquisition"
                df['Origin_Label'] = acq.label
                df['Origin_ID'] = acq.id

                if not include_images:
                    df = df[(df['Type'] != 'nifti') & (df['Type'] != 'dicom')]

                attachments = pd.concat([attachments, df])

    return attachments


def get_parser():

    parser = argparse.ArgumentParser(
        description="FLAUDIT: Flywheel Audit")
    parser.add_argument(
        "--project",
        help="The project in Flywheel",
        required=True
    )
    parser.add_argument(
        "--subject",
        help="The subject(s)",
        nargs="+",
        default=None,
        type=str
    )
    parser.add_argument(
        "--session",
        help="The session(s)",
        nargs="+",
        default=None,
        type=str
    )
    parser.add_argument(
        "--destination",
        help="Path to destination directory",
        default=".",
        type=str
    )
    parser.add_argument(
        "--api-key",
        help="API Key",
        action='store',
        default=None
    )
    parser.add_argument(
        "--verbose",
        help="Print ongoing messages of progress",
        action='store_true',
        default=False
    )

    return parser


def main():

    #logger.info("{:=^70}\n".format(": fw-heudiconv exporter starting up :"))
    parser = get_parser()
    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if args.api_key:
            fw = flywheel.Client(args.api_key)
        else:
            fw = flywheel.Client()
    assert fw, "Your Flywheel CLI credentials aren't set!"

    destination = args.destination

    if not os.path.exists(destination):
        logger.info("Creating destination directory...")
        os.makedirs(args.destination)

    logger.info("Gathering sessions...")
    sessions = get_sessions(client=fw,
                            project_label=args.project,
                            session_labels=args.session,
                            subject_labels=args.subject)

    logger.info("Gathering sequences...")
    seqinfo = gather_seqInfo(client=fw,
                             project_label=args.project,
                             session_labels=args.session,
                             subject_labels=args.subject
                             )

    logger.info("Gathering BIDS data...")
    bids = gather_bids_for_seqs(client=fw, df=seqinfo)

    logger.info("Gathering jobs...")
    jobs = gather_jobs(sessions_list=sessions, verbose=True)

    logger.info("Gathering attachments...")
    attachments = gather_attachments(client=fw, project_label=args.project)

    logger.info("Writing output data...")
    seqinfo.to_csv("{}/seqinfo.csv".format(args.destination), index=False)
    bids.to_csv("{}/bids.csv".format(args.destination), index=False)
    jobs.to_csv("{}/jobs.csv".format(args.destination), index=False)
    attachments.to_csv(
        "{}/attachments.csv".format(args.destination), index=False)

    logger.info("Done!")
    #logger.info("{:=^70}".format(": Exiting fw-heudiconv exporter :"))


if __name__ == '__main__':
    main()
