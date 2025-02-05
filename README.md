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
                  <li>
                  
ActiveBatch:      <ul>
                  <li>
                  </ul>

Source Code:      <ul>
                  <li>
                  </ul>

LogFile Location: <ul>
                  <li>
                  </ul>

**Contact Information -**

Primary Users:    <ul>
                  <li>
                  </ul>

Lead Customer:    <ul>
                  <li>
                  </ul>

Lead Developer:   <ul>
                  <li>Bradley Ruck
                  </ul>

Date Launched:    <ul>
                  <li>March, 2018
                  </ul>
                  
Date Updated:     <ul>
                  <li>August, 2018
                  </ul>
