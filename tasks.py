# vim: set expandtab sw=4 ts=4:
"""
Celery Tasks.

Copyright (C) 2014-2016 Dieter Adriaenssens <ruleant@users.sourceforge.net>

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

from celery_worker import APP
import cgi
from buildtimetrend import logger
from buildtimetrend.travis import TravisData
from buildtimetrend.keenio import send_build_data_service
from buildtimetrend.service import check_process_parameters


@APP.task(
    bind=True,
    ignore_result=True,
    max_retries=5,
    default_retry_delay=30 * 60  # 30 minutes in seconds
)
def process_travis_buildlog(self, repo, build):
    """
    Process Travis CI buildlog.

    Check parameters, load build data from Travis CI,
    process it and send to Keen.io for storage.
    """
    repo = str(repo)
    build = str(build)

    try:
        result = check_process_parameters(repo, build)
    except Exception as msg:
        if self.request.called_directly:
            return msg
        else:
            # When checking if build exists fails, retry later
            # Keen.io API might be down
            raise self.retry()

    if result is not None:
        logger.warning(result)
        return result

    travis_data = TravisData(repo, build)

    # retrieve build data using Travis CI API
    message = "Retrieving build #%s data of %s from Travis CI"
    logger.info(message, build, repo)
    ret_msg = message % (cgi.escape(build), cgi.escape(repo))
    if not travis_data.get_build_data():
        if self.request.called_directly:
            ret_msg += "\nError retrieving build data."
            return ret_msg
        else:
            # retry if retrieving build data failed.
            raise self.retry()

    # process all build jobs and
    # send build job data to Keen.io
    for build_job in travis_data.process_build_jobs():
        build_job_id = build_job.properties.get_items()["job"]
        message = "Send build job #%s data to Keen.io"
        logger.warning(message, build_job_id)
        ret_msg += "\n" + message % cgi.escape(build_job_id)
        send_build_data_service(build_job)

    # check if collection is empty
    if travis_data.build_jobs:
        message = "Successfully retrieved build #%s data of %s" \
            " from Travis CI and sent to Keen.io"
    else:
        message = "No data found for build #%s of %s"
    logger.warning(message, build, repo)
    ret_msg += "\n" + message % (cgi.escape(build), cgi.escape(repo))
    return ret_msg
