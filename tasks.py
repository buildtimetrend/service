# vim: set expandtab sw=4 ts=4:
"""
Celery Tasks Queue.

Copyright (C) 2014-2015 Dieter Adriaenssens <ruleant@users.sourceforge.net>

This file is part of buildtimetrend/python-service
<https://github.com/buildtimetrend/python-service/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import cgi
from celery import Celery
from buildtimetrend.settings import Settings
from buildtimetrend import logger
from buildtimetrend.travis import TravisData
from buildtimetrend.keenio import send_build_data_service
from buildtimetrend.service import check_process_parameters
from buildtimetrend.tools import check_dict
import constants

# load settings
settings = Settings()
settings.load_settings(config_file=constants.CONFIG_FILE)
settings.set_client(constants.CLIENT_NAME, constants.CLIENT_VERSION)

def is_worker_enabled():
    """Check if a task queue is configured and a worker is available."""
    return check_dict(
        settings.get_setting("task_queue"),
        key_list=["broker_url", "backend"]
    )

if is_worker_enabled():
    task_queue = settings.get_setting("task_queue")
    app = Celery(
        'tasks',
        backend=task_queue["backend"],
        broker=task_queue["broker_url"]
    )

    if app is None:
        logger.error("Error connection to task queue")
    else:
        logger.info("Connected to task queue : %s", task_queue["broker_url"])
else:
    logger.error("Task queue is not defined, check README.md to configure task queue")
    quit()


@app.task(ignore_result=True)
def process_travis_buildlog(repo, build):
    """
    Process Travis CI buildlog.

    Check parameters, load build data from Travis CI,
    process it and send to Keen.io for storage.
    """
    result = check_process_parameters(repo, build)
    if result is not None:
        logger.warning(result)
        return

    travis_data = TravisData(repo, build)

    # retrieve build data using Travis CI API
    message = "Retrieving build #%s data of %s from Travis CI"
    logger.info(message, build, repo)
    message += "\n"
    print message % (cgi.escape(build), cgi.escape(repo))
    travis_data.get_build_data()

    # process all build jobs and
    # send build job data to Keen.io
    for build_job in travis_data.process_build_jobs():
        build_job_id = build_job.properties.get_items()["job"]
        message = "Send build job #%s data to Keen.io"
        logger.info(message, build_job_id)
        message += "\n"
        print message % cgi.escape(build_job_id)
        send_build_data_service(build_job)

    if len(travis_data.build_jobs) == 0:
        message = "No data found for build #%s of %s"
    else:
        message = "Successfully retrieved build #%s data of %s" \
            " from Travis CI and sent to Keen.io"
    logger.info(message, build, repo)
    print message % (cgi.escape(build), cgi.escape(repo))
