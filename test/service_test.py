# vim: set expandtab sw=4 ts=4:
"""
Unit tests for Service

Copyright (C) 2014-2016 Dieter Adriaenssens <ruleant@users.sourceforge.net>

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

from service import get_config_project_list
from buildtimetrend.settings import Settings
import unittest
import mock


class TestService(unittest.TestCase):

    """Unit tests for Service methods"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixture."""
        cls.settings = Settings()

    def setUp(self):
        """Initialise test environment before each test."""
        # reinit settings singleton
        if self.settings is not None:
            self.settings.__init__()

    @mock.patch('service.get_all_projects', return_value=[])
    def test_get_config_project_list(self, get_all_projects_func):
        """Test get_config_project_list()"""
        # test with empty project list
        self.assertDictEqual({}, get_config_project_list())

        # test with project list with some items
        get_all_projects_func.return_value = [
            'ruleant/test',
            'ruleant/test1',
            'ruleant/test2'
        ]
        self.assertDictEqual(
            {'projectList': [
                'ruleant/test',
                'ruleant/test1',
                'ruleant/test2'
            ]}, get_config_project_list()
        )

        # test with limited list matching allowed repo name
        self.settings.add_setting("allowed_repo", {"test1"})
        self.assertDictEqual(
            {'projectList': ['ruleant/test1']}, get_config_project_list()
        )

        # test with no repo matching allowed repo name
        self.settings.add_setting("allowed_repo", {"something"})
        self.assertDictEqual({}, get_config_project_list())
