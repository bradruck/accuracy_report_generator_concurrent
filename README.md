**Description -**

The Targeting Accuracy Report is a requirement for tracking the effectiveness of the Onramp Campaign effort for
the Campaign Management group. The Report is run on a weekly basis, over the weekend, and encompasses a reporting
period that includes the previous week (Thursday through Friday). The automation is deployed and scheduled on
singularity and begins by conducting a JIRA search for specified tickets that fit the prescribed reporting criteria.
The applicable tickets are mined for information required for the report generation, this information is used to
populate multiple Hive queries that are run concurrently on Qubole.  The report results are returned and posted as a
comment to the JIRA ticket.

**Application Information -**

Required modules: <ul>
                  <li>main.py,
                  <li>targeting_accuracy_manager.py,
                  <li>jira_manager.py,
                  <li>qubole_manager.py,
                  <li>targeting_accuracy_query.py,
                  <li>config.ini
                  </ul>
                  
Deployed Loc:     <ul>
                  <li>//prd-use1a-pr-34-ci-operations-01/home/bradley.ruck/Projects/campaign_management_ta_reporting/
                  </ul>
                  
ActiveBatch:      <ul>
                  <li>//prd-09-abjs-01 (V11)/'Jobs, Folders & Plans'/Operations/Report/CM_TA_Reporting/CM_Once_a_Week
                  </ul>

Source Code:      <ul>
                  <li>gitlab.oracledatacloud.com/odc-operations/CM_TargetingAccuracy_Concurrent/
                  </ul>

LogFile Location: <ul>
                  <li>zfs1/Operations_mounted/CampaignManagement/TargetingAccuracyReportLogs/
                  </ul>

**Contact Information -**

Primary Users:    <ul>
                  <li>Campaign Management
                  </ul>

Lead Customer:    <ul>
                  <li>
                  </ul>

Lead Developer:   <ul>
                  <li>Bradley Ruck (bradley.ruck@oracle.com)
                  </ul>

Date Launched:    <ul>
                  <li>March, 2018
                  </ul>
                  
Date Updated:     <ul>
                  <li>August, 2018
                  </ul>
