# Copyright 2021 Canonical Ltd
# See LICENSE file for licensing details.

import logging
import datetime

from prometheus_api_client.utils import parse_datetime

logger = logging.getLogger(__name__)

"""
  4k-random-readwrite:
    description: “4K random read/write workload test”
    test-duration: 1800 # duration in seconds
    ramp-interval: 90 # duration in seconds between addition of test clients
    batch-size: 20 # batch size in which clients will be added to the benchmark
    clients: 100 # total number of test clients to use for this test
    application: [model:]application # i.e woodpecker/magpie
    action: fio
    parameters:
        operation: randrw
        iodepth: 32
        block-size: 4k
"""


class BenchmarkValidationError(Exception):
    pass


class BenchmarkWorker(object):
    """Worker for execution of a specific benchmark test"""

    chunk_size = datetime.timedelta(seconds=60)

    def __init__(self, datasource: str, juju, test: dict):
        self.datasource = datasource
        self.juju = juju
        self.test = test
        self.action_pool = []

    def validate(self) -> None:
        """Validate that deployment environment can execute the test"""
        model_name = None
        app_name = None
        try:
            model_name, app_name = self.test["application"].split(":")
        except ValueError:
            app_name = self.test["application"]

        if model_name:
            try:
                self.juju.switch_model(model_name)
            except:
                raise BenchmarkValidationError(f"Unable to find model {model_name}")
        try:
            self.application = self.juju.get_application(app_name)
        except:
            raise BenchmarkValidationError(f"Unable to find application {app_name}")

        clients = int(self.test["clients"])
        if len(self.application.units) < clients:
            raise BenchmarkValidationError(
                f"Not enough units for {app_name} to execute test"
            )
        # TODO
        # check action exists and has required parameters

    def execute(self) -> None:
        """Execute the benchmark"""
        self.start_time = parse_datetime("now")
        # run_action will queue the action
        # need to check status untill all have completed
        self.application.units
        test_duration = int(self.test["test_duration"])
        batch_size = int(self.test["batch_size"])
        ramp_interval = int(self.test["ramp_interval"])
        clients = int(self.test["clients"])
        while clients > 0:
            # Submit batch_size of clients and append to
            # the action pool
            units = self.application.units
            self.action_pool.append(task)
            clients -= batch_size
            sleep(ramp_interval)

        self.end_time = parse_datetime("now")
        # TODO
        # generate test summary data
        # add annotations to grafana
        # snapshot dashboard(s) for tests and reference


# TODO
# Things to add to governor charm model
# juju_wrapper:execute_action - parallel execution and tracking across units?
