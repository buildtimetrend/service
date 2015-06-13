# vim: set expandtab sw=4 ts=4:
"""
Unit tests for Service

Copyright (C) 2014-2015 Dieter Adriaenssens <ruleant@users.sourceforge.net>

This file is part of buildtimetrend/service
<https://github.com/buildtimetrend/service/>

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

import os
from tasks import is_worker_enabled
from buildtimetrend.settings import Settings
import unittest


class TestTasks(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.settings = Settings()

    def setUp(self):
        # reinit settings singleton
        if self.settings is not None:
            self.settings.__init__()

    def test_is_worker_enabled(self):
        # should return false when task queue url is not defined
        self.assertFalse(is_worker_enabled())

        # set and load test env vars
        os.environ["BTT_AMQP_URL"] = "amqp://"
        self.settings.load_env_vars_task_queue()

        # should return false when task queue url is not defined
        self.assertTrue(is_worker_enabled())

        # remove env var
        del os.environ["BTT_AMQP_URL"]
