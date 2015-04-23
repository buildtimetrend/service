# vim: set expandtab sw=4 ts=4:
#
# Unit tests for Service
#
# Copyright (C) 2014-2015 Dieter Adriaenssens <ruleant@users.sourceforge.net>
#
# This file is part of buildtimetrend/service
# <https://github.com/buildtimetrend/service/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from service import is_repo_allowed
from buildtimetrend.settings import Settings
import unittest


class TestService(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.settings = Settings()

    def setUp(self):
        # reinit settings singleton
        if self.settings is not None:
            self.settings.__init__()

    def test_is_repo_allowed(self):
        # error is thrown when called without parameters
        self.assertRaises(TypeError, is_repo_allowed)

        # error is thrown when called with an invalid parameter
        self.assertFalse(is_repo_allowed(None))

        # repo is allowed by default
        self.assertTrue(is_repo_allowed("name/repo"))

    def test_is_repo_allowed_set_denied(self):
        # test denied repo
        self.settings.add_setting("denied_repo", {"test1"})

        self.assertTrue(is_repo_allowed("name/repo"))
        self.assertFalse(is_repo_allowed("name/test1"))
        self.assertTrue(is_repo_allowed("name/test2"))

    def test_is_repo_allowed_set_denied_multi(self):
        # test multiple denied repos
        self.settings.add_setting("denied_repo", {"test1", "test2"})

        self.assertTrue(is_repo_allowed("name/repo"))
        self.assertFalse(is_repo_allowed("name/test1"))
        self.assertFalse(is_repo_allowed("name/test2"))

    def test_is_repo_allowed_set_allowed(self):
        # test allowed repo
        self.settings.add_setting("allowed_repo", {"test1"})

        self.assertFalse(is_repo_allowed("name/repo"))
        self.assertTrue(is_repo_allowed("name/test1"))
        self.assertFalse(is_repo_allowed("name/test2"))
        
    def test_is_repo_allowed_set_allowed_multi(self):
        # test multiple allowed repos
        self.settings.add_setting("allowed_repo", {"test1", "test2"})

        self.assertFalse(is_repo_allowed("name/repo"))
        self.assertTrue(is_repo_allowed("name/test1"))
        self.assertTrue(is_repo_allowed("name/test2"))

    def test_is_repo_allowed_set_denied_allowed(self):
        # set denied repo
        self.settings.add_setting("denied_repo", {"test1"})
        # set allowed repo
        self.settings.add_setting("allowed_repo", {"name"})

        self.assertTrue(is_repo_allowed("name/repo"))
        self.assertFalse(is_repo_allowed("name/test1"))
        self.assertTrue(is_repo_allowed("name/test2"))
        self.assertFalse(is_repo_allowed("owner/repo"))
