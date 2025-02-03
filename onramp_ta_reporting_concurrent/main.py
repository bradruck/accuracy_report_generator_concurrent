# Campaign Management - Targeting Accuracy Reporting for Onramp

# Description -
# The Targeting Accuracy Report is a requirement for tracking the effectiveness of the Onramp Campaign effort for
# the Campaign Management group. The Report is run on a weekly basis, over the weekend, and encompasses a reporting
# period that includes the previous week (Thursday through Friday). The automation is deployed and scheduled on
# singularity and begins by conducting a JIRA search for specified tickets that fit the prescribed reporting criteria.
# The applicable tickets are mined for information required for the report generation, this information is used to
# populate multiple Hive queries that are run concurrently on Qubole.  The report results are returned and posted as a
# comment to the JIRA ticket.
#
# Application Information -
# Required modules: main.py,
#                   targeting_accuracy_manager.py,
#                   jira_manager.py,
#                   qubole_manager.py,
#                   targeting_accuracy_query.py,
#                   config.ini
# Deployed Loc:     //prd-use1a-pr-34-ci-operations-01/home/bradley.ruck/Projects/campaign_management_ta_reporting/
# ActiveBatch:      //prd-09-abjs-01 (V11)/'Jobs, Folders & Plans'/Operations/Report/CM_TA_Reporting/CM_Once_a_Week
# Source Code:      gitlab.oracledatacloud.com/odc-operations/CM_TargetingAccuracy_Concurrent/
# LogFile Location: zfs1/Operations_mounted/CampaignManagement/TargetingAccuracyReportLogs/
#
# Contact Information -
# Primary Users:    Campaign Management - Onramp Campaigns
# Lead Customer:    James Minor (james.minor@oracle.com)
# Lead Developer:   Bradley Ruck (bradley.ruck@oracle.com)
# Date Launched:    March, 2018
# Date Updated:     August, 2018


# main module
# Responsible for reading in the basic configurations settings, creating the log file, and creating and launching
# the Targeting Accuracy Manager, finally it launches the purge_files method to remove log files that are older than
# a prescribed retention period
#
from datetime import datetime, timedelta
import os
import sys
import logging
import configparser
from targeting_accuracy_manager import TargetingAccuracyManager


# Sets the log file's name date to ‘Sunday’ of the run weekend in the format of %Y%m%d, this to enable multiple run
# attempts over the weekend, but once successful, no further runs are permitted because of 'if not log file' check below
#
def logfile_name_date_set():
    # Sets the day of week for log file name to targeted day, function determines if it is the current or past week.
    targeted_dayofweek = 4  # Friday, this setting will always produce a run period in the current week.
    current_dayofweek = datetime.now().weekday()  # Today
    if targeted_dayofweek <= current_dayofweek:
        # Target is in the current week
        run_date = datetime.strftime(datetime.now() - timedelta(current_dayofweek - targeted_dayofweek), "%Y%m%d")
    else:
        # Target is in the previous week
        run_date = datetime.strftime(datetime.now() - timedelta(weeks=1) + timedelta(targeted_dayofweek -
                                                                                     current_dayofweek), "%Y%m%d")
    return run_date


# Define a console logger for development purposes
#
def console_logger():
    # define Handler that writes DEBUG or higher messages to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a simple format for console use
    formatter = logging.Formatter('%(levelname)-7s: %(name)-30s: %(threadName)-12s: %(message)s')
    console.setFormatter(formatter)
    # add the Handler to the root logger
    logging.getLogger('').addHandler(console)


def main(con_opt='n'):
    today_date = (datetime.now() - timedelta(hours=6)).strftime('%Y%m%d')

    # Get config files
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Create a dictionary of configuration parameters
    config_params = {
        "jira_url":         config.get('Jira', 'url'),
        "jira_token":       tuple(config.get('Jira', 'authorization').split(',')),
        "jql_agencies":     config.get('Jira', 'agency'),
        "jql_status":       config.get('Jira', 'status'),
        "jql_issuetype":    config.get('Jira', 'issuetype'),
        "qubole_token":     config.get('Qubole', 'bradruck-prod-operations-consumer'),
        "cluster_label":    config.get('Qubole', 'cluster-label'),
        "ta_pct":           float(config.get('Project Details', 'targeting accuracy pct'))
    }

    # Logfile path to point to the Operations_mounted drive on zfs1
    purge_days = config.get('LogFile', 'retention_days')
    log_file_path = config.get('LogFile', 'path')

    # Creates a log file name
    logfile_name = log_file_path + config.get('Project Details', 'app_name') + '_' + logfile_name_date_set() + '.log'

    # Check to see if log file already exits for the day to avoid duplicate execution
    if not os.path.isfile(logfile_name):
        try:
            # Creates a log file on the ZFS1 Operations_mounted drive
            logging.basicConfig(filename=logfile_name,
                                level=logging.INFO,
                                format='%(asctime)s: %(levelname)s: %(message)s',
                                datefmt='%m/%d/%Y %H:%M:%S')
        except IOError as e:
            # Writes to stderr file if log file creation unsuccessful
            sys.stderr.write("\nAccess to ZFS1 is an issue, cannot create log file: {}".format(e))
            exit(1)
        else:
            # checks for console logger option, default value set to 'n' to not run in production
            if con_opt and con_opt in ['y', 'Y']:
                console_logger()

            logging.log(20, "Process Start - Targeting Accuracy Reporting, Campaign Management - Digital Campaigns - " +
                        today_date + "\n")
            # Create TAM Object and launch Report Generator
            cm_onramp_campaign = TargetingAccuracyManager(config_params)
            cm_onramp_campaign.process_manager()

            # Search logfile directory for old log files to purge
            cm_onramp_campaign.purge_files(purge_days, log_file_path)
    else:
        # Writes to stderr file if log file already exists
        sys.stderr.write("\nA log file already exists by that name, it appears the weekly run was completed.")


if __name__ == '__main__':
    # prompt user for use of console logging -> for use in development not production
    ans = input("\nWould you like to enable a console logger for this run?\n Please enter y or n:\t")
    print()
    main(ans)
