#!/usr/bin/env python
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging

import azure.functions as func
from onefuzztypes.enums import ScalesetState

from ..onefuzzlib.dashboard import get_event
from ..onefuzzlib.pools import Scaleset


def process_scaleset(scaleset: Scaleset) -> None:
    logging.debug("checking scaleset for updates: %s", scaleset.scaleset_id)

    if scaleset.state == ScalesetState.resize:
        scaleset.resize()

    # if the scaleset is touched during cleanup, don't continue to process it
    if scaleset.cleanup_nodes():
        logging.debug("scaleset needed cleanup: %s", scaleset.scaleset_id)
        return

    if (
        scaleset.state in ScalesetState.needs_work()
        and scaleset.state != ScalesetState.resize
    ):
        logging.info(
            "exec scaleset state: %s - %s",
            scaleset.scaleset_id,
            scaleset.state,
        )

        if hasattr(scaleset, scaleset.state.name):
            getattr(scaleset, scaleset.state.name)()
        return


def main(mytimer: func.TimerRequest, dashboard: func.Out[str]) -> None:  # noqa: F841
    scalesets = Scaleset.search()
    for scaleset in scalesets:
        process_scaleset(scaleset)

    event = get_event()
    if event:
        dashboard.set(event)
