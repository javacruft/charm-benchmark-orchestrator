#!/usr/bin/env python3
# Copyright 2021 James Page
# See LICENSE file for licensing details.

import base64
import logging
import yaml

from ops.charm import(
    RelationChangedEvent,
    RelationBrokenEvent,
)
from ops.main import main
from ops.model import ActiveStatus

from governor.base import GovernorBase

from worker import (
    BenchmarkWorker,
    BenchmarkValidationError
)

logger = logging.getLogger(__name__)

# TODO
# relation to grafana/dashboards
# relation to grafana/api


class BenchmarkOrchestratorCharm(GovernorBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.benchmark_action, self._on_benchmark_action)
        self.framework.observe(
            self.on.metric_storage_relation_changed, self._on_metric_source_changed
        )
        self.framework.observe(
            self.on.metric_storage_relation_broken, self._on_metric_source_broken
        )
        self.state.set_default(datasource=None)

    def _on_config_changed(self, _) -> None:
        """Configure the benchmark charm"""
        pass

    def _on_benchmark_action(self, event) -> None:
        """Execute a benchmark against a Juju model"""
        if all((self.state.datasource,)):
            try:
                # NOTE:
                # configuration is a yaml file that has to be provide
                # base64 encoded due to lack of a 'file' type for
                # action parameters
                configuration = yaml.load(
                    base64.b64decode(event.params["configuration"])
                )
            except TypeError as e:
                message = f"Unable to load configuration file: {e}"
                logger.error(message)
                event.fail(message)
                return

            for name, benchmark_test in configuration.items():
                benchmark = BenchmarkWorker(
                    self.state.datasource,
                    self.juju,
                    benchmark_test,
                )
                try:
                    logger.info(f"Validating benchmark '{name}'")
                    benchmark.validate()
                except BenchmarkValidationError as e:
                    message = f"Enable to validate benchmark: {e}"
                    logger.error(message)
                    event.fail(message)
                    return

                logger.info(f"Executing benchmark '{name}'")
                benchmark.execute()
                # TODO - think about how to return URI for results to user
        else:
            event.fail("Unable to execute benchmark due to missing datasource")

    def _on_metric_storage_changed(self, event: RelationChangedEvent) -> None:
        """Assess state of metric storage relation and configure datasource"""
        unit_data = event.relation.data[event.unit]
        datasource = {
            "type": unit_data.get('type'),
            "url": unit_data.get('type'),
            "description": unit_data.get('description'),
        }
        credentials = {
            "username": unit_data.get('username'),
            "password": unit_data.get('password'),
        }
        if all(credentials.values()):
            datasource.update(credentials)
        if unit_data.get('database'):
            datasource['database'] = unit_data.get('database')
        if all(datasource.values()):
            self.state.datasource = datasource
        else:
            self.state.datasource = None

    def _on_metric_source_broken(self, event: RelationBrokenEvent) -> None:
        """Clear any state associated with the metric storage relation"""
        self.state.datasource = None


if __name__ == "__main__":
    main(BenchmarkOrchestratorCharm)
