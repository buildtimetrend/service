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
    def setUp(self):
        self.settings = Settings()

    def test_is_repo_allowed(self):
        # error is thrown when called without parameters
        self.assertRaises(TypeError, is_repo_allowed)

        # error is thrown when called with an invalid parameter
        self.assertFalse(is_repo_allowed(None))

        # repo is allowed by default
        self.assertTrue(is_repo_allowed("name/repo"))
