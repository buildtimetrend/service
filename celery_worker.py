# vim: set expandtab sw=4 ts=4:
"""
Setup Celery Tasks Queue worker.

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

from celery import Celery
from buildtimetrend.settings import Settings
from buildtimetrend import logger
from buildtimetrend.tools import check_dict
import constants


def is_worker_enabled():
    """Check if a task queue is configured."""
    task_queue = Settings().get_setting("task_queue")
    # use double not to force boolean evaluation
    return check_dict(task_queue, key_list=["broker_url", "backend"]) and \
        not (not task_queue["broker_url"]) and \
        not (not task_queue["backend"])


def create_worker_app():
    """Create worker app."""
    # load settings
    settings = Settings()
    settings.load_settings(config_file=constants.CONFIG_FILE)
    settings.set_client(constants.CLIENT_NAME, constants.CLIENT_VERSION)

    if is_worker_enabled():
        task_queue = settings.get_setting("task_queue")
        worker_app = Celery(
            'tasks',
            backend=task_queue["backend"],
            broker=task_queue["broker_url"]
        )

        # configure worker
        worker_app.conf.update(
            CELERY_TASK_SERIALIZER = 'json',
            CELERY_ACCEPT_CONTENT = ['json']
        )

        if worker_app is None:
            logger.error("Error connection to task queue")
        else:
            logger.info(
                "Connected to task queue : %s", task_queue["broker_url"]
            )
    else:
        worker_app = Celery()
        logger.warning(
            "Task queue is not defined,"
            " check README.md to configure task queue"
        )

    return worker_app

APP = create_worker_app()

if __name__ == '__main__':
    if is_worker_enabled():
        APP.start()
    else:
        quit()
