# targeting_accuracy_manager module
# Module holds the class => TargetingAccuracyManager - manages the Targeting Accuracy Report Process
# Class responsible for overall program management
#
from datetime import datetime, timedelta, date
import time
import logging
import os
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count
from copy import deepcopy
# import json
import jira_manager
import qubole_manager
from targeting_accuracy_query import TargetingAccuracyQuery


today_date = (datetime.now() - timedelta(hours=7)).strftime('%Y%m%d')


class TargetingAccuracyManager(object):
    def __init__(self, config_params):
        self.jira_url = config_params['jira_url']
        self.jira_token = config_params['jira_token']
        self.jira_pars = jira_manager.JiraManager(self.jira_url, self.jira_token)
        self.jql_agencies = config_params['jql_agencies']
        self.jql_status = config_params['jql_status']
        self.jql_issuetype = config_params['jql_issuetype']
        self.qubole_token = config_params['qubole_token']
        self.cluster_label = config_params['cluster_label']
        self.ta_pct = config_params['ta_pct']
        self.log_dict = {}
        self.issues = []
        self.issue = None
        self.tickets = []
        self.logger = logging.log
        self.day_adjust = 0
        self.message = ""
        # Set report start and end dates to be previous Friday through Thursday
        self.report_start_date = datetime.strftime((datetime.today() - timedelta(days=self.date_adjust() + 6)),
                                                   "%Y%m%d")
        self.report_end_date = datetime.strftime((datetime.today() - timedelta(days=self.date_adjust())), "%Y%m%d")

    # Manages the process for finding tickets, launching the subprocess routine to run tickets concurrently
    #
    def process_manager(self):
        # Pulls desired tickets running jql
        self.issues = self.jira_pars.find_issues(self.jql_issuetype, self.jql_status, self.jql_agencies)

        # Verifies that issues were found that match the search criteria and logs count and a list of all issues then
        # pulls issue information, finally creates ticket object to hold a simplified version of the issue data
        if self.issues:
            pixel_count = 0
            for issue in self.issues:
                # Request the relevant ticket information for query
                (issue.start_date, issue.end_date, issue.pixels, issue.profile_ids) = \
                    self.jira_pars.report_information_pull(issue.key)
                pixel_count = pixel_count + len(issue.pixels)
                ticket = Ticket(issue)
                self.tickets.append(ticket)
            self.logger(20, str(len(self.issues)) + " ticket(s) were found with a total of " + str(pixel_count) +
                        " pixel(s).")
            self.logger(20, str([issue.key for issue in self.issues]) + "\n")
            self.ticket_concurrency_manager(self.tickets)
        else:
            self.logger(30, "There were no tickets found with the required criteria to report on.")

        self.jira_pars.kill_session()

    # Manages the process for ticket level concurrency processing, calls report generator function, enters all the info
    # level log entries to the master log file
    #
    def ticket_concurrency_manager(self, tickets):
        self.logger(20, "\nBeginning the ticket level concurrent processing.\n")
        # Reset the logging level to "WARNING" to filter out Qubole logging message deluge.
        logging.getLogger().setLevel(logging.WARNING)
        # Launches a thread for each of the found tickets
        ticket_pool = ThreadPool(cpu_count())
        try:
            ticket_pool.map(self.report_generator, tickets)
            ticket_pool.close()
            ticket_pool.join()
        except Exception as e:
            self.message = ("Ticket Level Concurrency run failed => {}".format(e))
            self.logger(40, self.message)
        else:
            # Reset the logging level to "INFO" to allow the addition of ticket and pixel level results
            logging.getLogger().setLevel(logging.INFO)
            self.logger(20, "\nFinished the ticket level concurrent processing.\n")
            self.log_write(self.log_dict)
            # Comment out the json file create/write below for production, used for log file off-line formatting
            # with open('log.json', 'w') as fp:
                # json.dump(self.log_dict, fp)

    # Checks campaign start and end dates, calls ticket data check
    #
    def report_generator(self, ticket):
        # This will circumvent the date checking for dev purposes on jira-dev, comment out for production
        # tdc_results = self.ticket_data_check(ticket)
        # return tdc_results

        # Ensures that the campaign is 'Live' by date checking
        if ticket.start_date <= self.report_end_date <= ticket.end_date:
            tdc_results = self.ticket_data_check(ticket)
            return tdc_results
        else:
            self.logger(30, "This ticket does not match the report-date criteria: " + ticket.key)

    # Verifies that ticket data - pixels and profile_ids exist and are proportionate, then creates sub-ticket objects
    # for each of the pixel numbers on the ticket, these are then progressed to the pixel_concurrency_manager module,
    # if only one pixel number on ticket, the ticket progresses directly to the query manager, if there is a problem
    # with ticket data a comment alert is posted to the ticket by calling the comments_manager
    #
    def ticket_data_check(self, ticket):
        if ticket.pixels and ticket.profile_ids and len(ticket.pixels) == len(ticket.profile_ids):
            if len(ticket.pixels) > 1:
                tickets = []
                n = 0
                for pixel in ticket.pixels:
                    sub_ticket = deepcopy(ticket)
                    sub_ticket.pixels = []
                    sub_ticket.profile_ids = []
                    sub_ticket.pixels.append(pixel)
                    sub_ticket.profile_ids.append(ticket.profile_ids[n])
                    tickets.append(sub_ticket)
                    n += 1
                pcm_results = self.pixel_concurrency_manager(tickets)
                return pcm_results
            else:
                qm_results = self.query_manager(ticket)
                return qm_results
        else:
            self.logger(30, "This ticket is missing data required for report generation: " + ticket.key)
            self.comments_manager(ticket, None)

    # For tickets with multiple pixel numbers, calls the query manager function for each pixel on multi-pixel tickets
    #
    def pixel_concurrency_manager(self, tickets):
        # Launches a thread for each of the pixels
        pixel_pool = ThreadPool(cpu_count())
        try:
            pixel_results = pixel_pool.map(self.query_manager, tickets)
            pixel_pool.close()
            pixel_pool.join()
        except Exception as e:
            self.message = ("Pixel Level Concurrency run failed => {}".format(e))
            self.logger(40, self.message)
        else:
            return pixel_results

    # Runs a weekly report and returns results
    #
    def query_manager(self, ticket):
        # Checks that the required ticket information exists, else bypasses Qubole
        if ticket.pixels and ticket.profile_ids:
            ticket.query = TargetingAccuracyQuery()
            qubole = qubole_manager.QuboleManager((ticket.key, "".join(ticket.pixels[0])), self.qubole_token,
                                                  self.cluster_label, ticket.query.weekly_query(ticket.pixels,
                                                  ticket.profile_ids, self.report_start_date, self.report_end_date))
            query_result = qubole.get_results()
            self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append(ticket.pixels)
            self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append(ticket.profile_ids)
            self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append(query_result)
            self.comments_manager(ticket, query_result)
            return query_result

    # Confirms output of query, posts results to Jira ticket, if required => post alerts for low TA% or no results
    #
    def comments_manager(self, ticket, result):
        if result:
            self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append("The reporting period is " +
                                                                                     self.report_start_date +
                                                                                     " through "
                                                                                     + self.report_end_date)
            self.jira_pars.add_report_comment(ticket.key, ticket.pixels, result, self.report_start_date,
                                              self.report_end_date)
            self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append("The query results have been "
                                                                                     "added as a comment to Jira "
                                                                                     "Ticket: " + str(ticket.key))
            if float(result[4]) < self.ta_pct:
                self.jira_pars.add_ta_alert_comment(ticket.key, ticket.pixels, str(self.ta_pct))
                self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append("A targeting accuracy alert "
                                                                                         "has been added as a comment "
                                                                                         "to Jira Ticket: "
                                                                                         + str(ticket.key))
        else:
            self.jira_pars.add_ticket_data_alert_comment(ticket.key)
            self.log_dict.setdefault(str((ticket.key, ticket.pixels[0])), []).append("A ticket alert has been added "
                                                                                     "as a comment to Jira Ticket: "
                                                                                     + str(ticket.key))

    # Returns a number enabling day of week adjustment for query run based on which weekend day the program is executed,
    # throws exception if execution is attempted on a non-weekend day (Monday - Thursday), exits program
    #
    def date_adjust(self):
        try:
            # Checks which day of the week the actual report is being run, assigns an integer: Fri=4, Sat=5, Sun=6
            # => for testing purposes change the integer at the end to adjust the run day to a weekend day, 0 for prod
            run_day = datetime.weekday(datetime.today())+0
            # Assigns timedelta adjustment for the reporting dates, enabling run schedule on any weekend day (Fri-Sun)
            adjust_list = [(4, 1), (5, 2), (6, 3)]
            self.day_adjust = [element[1] for element in adjust_list if element[0] == run_day].pop()
            return self.day_adjust

        except Exception as e:
            self.message = ("Today is '" + date.today().strftime('%A') +
                            "' - this program should only be executed on a Friday, Saturday or Sunday: => {}".format(e))
        self.logger(40, self.message)
        exit()

    # Writes the contents of a log dictionary to the master log file in an easy-to-read ordered fashion
    #
    def log_write(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.logger(20, '\n\t\t\t\t\tTicket Number => ' + eval(k)[0])
                self.logger(20, '     => Pixel: ' + "".join(v[0]))
                if len(v[1]) is 1:
                    self.logger(20, '     => Profile IDs: ' + "".join(v[1]))
                else:
                    self.logger(20, '     => Profile IDs: ' + ", ".join(v[1]))
                self.logger(20, '     => Query Results: ' + ", ".join(v[2]))
                self.logger(20, '     => Ticket Comments: ')
                for i in range(3, len(v)):
                    self.logger(20, '        ' + str(v[i]))

    # Checks the log directory for all files and removes those after a specified number of days
    #
    def purge_files(self, purge_days, purge_dir):
        try:
            self.logger(20, "\n\t\t\tPurge [" + str(purge_days) + "] days old files from [" + purge_dir + "] directory")
            now = time.time()
            for file_purge in os.listdir(purge_dir):
                f_obs_path = os.path.join(purge_dir, file_purge)
                if os.stat(f_obs_path).st_mtime < now - int(purge_days) * 86400 and f_obs_path.split(".")[-1] == "log":
                    self.logger(20, "Purging File [" + f_obs_path + "] with timestamp [" +
                                str(time.strptime(time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.localtime(os.stat(f_obs_path).st_mtime)), "%Y-%m-%d %H:%M:%S")) + "]")
                    os.remove(f_obs_path)

        except Exception as e:
            self.logger(40, str(e))


# Small class to hold a simplified version of the Jira issues for less program overhead
#
class Ticket(object):
    def __init__(self, issue):
        self.key = issue.key
        self.pixels = issue.pixels
        self.profile_ids = issue.profile_ids
        self.start_date = issue.start_date
        self.end_date = issue.end_date
