# jira_manager module
# Module holds the class => JiraManager - manages JIRA ticket interface
# Class responsible for all JIRA related interactions including ticket searching, data pull and comment posting
#
from jira import JIRA
import logging
from datetime import datetime, timedelta


class JiraManager(object):
    def __init__(self, url, jira_token):
        self.tickets = []
        self.jira = JIRA(url, basic_auth=jira_token)
        self.campaign_start_date = 0
        self.campaign_end_date = 0
        self.pixels = []
        self.profile_ids = []
        self.campaign_manager = ""
        self.logger = logging.log
        self.today_date = (datetime.now() - timedelta(hours=6)).strftime('%m/%d/%Y')
        self.ta_alert = "The Targeting Accuracy has fallen below - "
        self.ticket_data_alert = "There may be a problem with the ticket data, please check that both the " \
                                 "'Pixels' and 'Profile ID/s' fields have been populated and are proportionate."

    # Searches Jira for all tickets that match the query criteria
    #
    def find_issues(self, issue_types, status_types, agency_names):
        # Query to find qualified Jira Tickets
        jql_query = "project IN (CAM) AND issuetype IN " + issue_types + " AND status IN " + status_types + \
                    " AND agency IN " + agency_names + " AND labels in ('Individually_Fulfilled') " + \
                    " ORDER BY 'End Date' ASC"
        self.tickets = self.jira.search_issues(jql_query)
        return self.tickets

    # Retrieves the required data from ticket to run query
    #
    def report_information_pull(self, cam_id):
        ticket = self.jira.issue(cam_id)
        self.campaign_start_date = datetime.strptime(ticket.fields.customfield_10431, "%Y-%m-%d").strftime("%Y%m%d")
        self.campaign_end_date = datetime.strptime(ticket.fields.customfield_10418, "%Y-%m-%d").strftime("%Y%m%d")
        self.pixels = ticket.fields.customfield_11447.replace(' ', '').split(',')
        self.profile_ids = ticket.fields.customfield_12413.replace(' ', '').split('|')
        self.campaign_manager = str(ticket.fields.customfield_11486)
        return self.campaign_start_date, self.campaign_end_date, self.pixels, self.profile_ids

    # Add report results to ticket in the form of a comment
    #
    def add_report_comment(self, cam_id, pixel, query_results, report_start_date, report_end_date):
        ticket = self.jira.issue(cam_id)
        reporter = ticket.fields.reporter.key
        message = """|Reporting Dates|{start_date}  thru  {end_date}| 
                     |Pixel|{pixel_no}|
                     |x.TOTAL_IMPRESSIONS|{x_tot_imp}|
                     |y.ELIGIBLE_INDIVIDUALS|{y_elig_ind}|
                     |IND_MATCH_PERCENT|{ind_match_pct}%| 
                     |z.MATCHED_INDIVIDUALS|{z_match_ind}|
                     |Targeting Accuracy|{target_acc}%|"""\
                                                .format(reporter, start_date=report_start_date,
                                                                  end_date=report_end_date,
                                                                  pixel_no="".join(pixel),
                                                                  x_tot_imp="{0:,d}".format(int(query_results[0])),
                                                                  y_elig_ind="{0:,d}".format(int(query_results[1])),
                                                                  ind_match_pct=str(round(float(query_results[2]), 2)),
                                                                  z_match_ind="{0:,d}".format(int(query_results[3])),
                                                                  target_acc=str(round(float(query_results[4]), 2)))
        self.jira.add_comment(issue=ticket, body=message)

    # Add an alert to ticket in the form of a comment
    #
    def add_ticket_data_alert_comment(self, cam_id):
        campaign_manager = self.campaign_manager.lower().split(' ')
        ticket = self.jira.issue(cam_id)
        reporter = ticket.fields.reporter.key
        message = """[~{attention}]
                     {ticket_data_alert}""".format(reporter, attention=".".join(campaign_manager),
                                                             ticket_data_alert=self.ticket_data_alert)
        self.jira.add_comment(issue=ticket, body=message)

    # Add an alert to ticket for 'target accuracy' shortfall in the form of a comment
    #
    def add_ta_alert_comment(self, cam_id, pixel, ta_pct):
        campaign_manager = self.campaign_manager.lower().split(' ')
        ticket = self.jira.issue(cam_id)
        reporter = ticket.fields.reporter.key
        message = """[~{attention}]
                     Pixel: {pixel_no},
                     {ta_alert} {ta_pct}%""".format(reporter, attention=".".join(campaign_manager),
                                                              pixel_no="".join(pixel),
                                                              ta_alert=self.ta_alert,
                                                              ta_pct=str(ta_pct))
        self.jira.add_comment(issue=ticket, body=message)

    # Ends the current JIRA session
    #
    def kill_session(self):
        self.jira.kill_session()
