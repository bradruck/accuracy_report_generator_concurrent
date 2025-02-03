# qubole_manager module
# Module holds the class => QuboleManager - manages Qubole search interface
# Class responsible for all Qubole related interactions including query launch and results retrieval
#
from qds_sdk.commands import *
import logging
import io
from contextlib import redirect_stdout


class QuboleManager(object):
    def __init__(self, name, qubole_token, cluster_label, query):
        self.name = name
        self.qubole_token = qubole_token
        self.cluster_label = cluster_label
        self.query = query
        self.message = ""
        self.logger = logging.log

    # Launches query, collects,converts and returns results
    #
    def get_results(self):
        Qubole.configure(api_token=self.qubole_token)
        try:
            # Launches the qubole query
            resp = self.launch_query()

        except Exception as e:
            self.message = ("Query run failed => {}".format(e))
            self.logger(40, self.message)

        else:
            output = io.BytesIO()
            with redirect_stdout(output):
                resp.get_results(fp=output, inline=True)
                output.seek(0)
                results = (output.read()).decode("utf-8").strip().split('\t')
            return results

    # Launches query and checks periodically for completion
    #
    def launch_query(self):
        done = False
        attempt = 1
        while not done and attempt <= 3:
            resp = HiveCommand.create(query=self.query, retry=3, label=self.cluster_label, name=", ".join(self.name))
            final_status = self.watch_status(resp.id)
            done = HiveCommand.is_success(final_status)
            attempt += 1
            if done:
                return resp

    # Monitors the Hive query status, returns when finished
    #
    @ staticmethod
    def watch_status(job_id):
        cmd = HiveCommand.find(job_id)
        while not HiveCommand.is_done(cmd.status):
            time.sleep(Qubole.poll_interval)
            cmd = HiveCommand.find(job_id)
        return cmd.status
