#!/usr/bin/env python
# vim: set expandtab sw=4 ts=4:
'''
Retrieve Travis CI build data and log to Keen.io

Copyright (C) 2014 Dieter Adriaenssens <ruleant@users.sourceforge.net>

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
'''

import os
import cgi
import cherrypy
from buildtimetrend.travis import process_notification_payload
from buildtimetrend.travis import check_authorization
from buildtimetrend.travis import TravisData
from buildtimetrend.settings import Settings
from buildtimetrend.tools import get_logger
from buildtimetrend.tools import set_loglevel
from buildtimetrend.keenio import log_build_keen
from buildtimetrend.keenio import keen_is_writable


SERVICE_WEBSITE_LINK = "<a href='https://github.com/buildtimetrend/service'>" \
                       "Buildtime Trend as a Service</a>"


class TravisParser(object):
    '''
    Retrieve timing data from Travis CI, parse it and store it in Keen.io
    '''

    def __init__(self):
        '''
        Initialise class, by loading a config file and setting loglevel
        '''
        self.settings = Settings()
        self.settings.load_config_file("config_service.yml")
        self.settings.load_env_vars()

        cherrypy.config.update({'error_page.404': self.error_page_404})

        # get logger
        self.logger = get_logger()

    @cherrypy.expose
    def index(self):
        '''
        Index page
        '''
        return "Coming soon : %s" % SERVICE_WEBSITE_LINK

    @cherrypy.expose
    def travis(self, repo=None, build=None, payload=None):
        '''
        Visiting this page triggers loading and processing the build log
        and data of a travis CI build process.
        Parameters:
        repo : git repo name (fe. user/repo)
        build : build number
        '''
        # reset settings
        self.settings.set_project_name(None)
        self.settings.add_setting('build', None)

        self.logger.info("Check Travis headers : %r", cherrypy.request.headers)

        # load parameters from the Travis notification payload
        if self.check_travis_notification():
            process_notification_payload(payload)

        # process url (GET) parameters
        if repo is not None:
            self.logger.info("Build repo : %s", repo)
            self.settings.set_project_name(repo)

        if build is not None:
            self.logger.info("Build number : %s", str(build))
            self.settings.add_setting('build', build)

        # process travis build
        return self.process_travis_buildlog()

    def error_page_404(self, status, message, traceback, version):
        '''
        Page 404
        '''
        self.logger.error("Cherrypy %s : Error loading page (%s) : %s\n"
                          "Traceback : %s",
                          version, status, message, traceback)
        return "This page doesn't exist, please check usage on " \
               "the %s website." % SERVICE_WEBSITE_LINK

    def process_travis_buildlog(self):
        '''
        Check parameters, load build data from Travis CI,
        process it and send to Keen.io for storage.
        '''
        repo = self.settings.get_project_name()
        build = self.settings.get_setting('build')

        result = self.check_process_parameters(repo, build)
        if result is not None:
            return result

        travis_data = TravisData(repo, build)

        # retrieve build data using Travis CI API
        self.logger.info("Retrieve build #%s data of %s from Travis CI",
                         build, repo)
        travis_data.get_build_data()

        # process all build jobs
        travis_data.process_build_jobs()

        # send build job data to Keen.io
        for build_job in travis_data.build_jobs:
            self.logger.info("Send build job #%s data to Keen.io", build_job)
            log_build_keen(travis_data.build_jobs[build_job])

        message = "Successfully retrieved build #%s data of %s" \
                  " from Travis CI and sent to Keen.io"
        self.logger.info(message, build, repo)
        return message % (cgi.escape(build), cgi.escape(repo))

    def check_process_parameters(self, repo, build):
        '''
        Check parameters (repo and build)
        Returns error message, None when all parameters are fine.
        '''
        if repo is None:
            self.logger.warning("Repo is not set")
            return "Repo is not set, use repo=user/repo"

        # check if repo is allowed
        allowed_repo = self.settings.get_setting("allowed_repo")
        if allowed_repo is not None and \
                not any(x in repo for x in allowed_repo):
            message = "The supplied repo is not allowed : %s"
            self.logger.warning(message, repo)
            return message % cgi.escape(repo)

        build = self.settings.get_setting('build')
        if build is None:
            self.logger.warning("Build number is not set")
            return "Build number is not set, use build=build_id"

        if not keen_is_writable():
            return "Keen IO write key not set, no data was sent"

        return None

    def check_travis_notification(self):
        '''
        Load Authorization and Travis-Repo-Slug headers and check if
        the Authorization header is correct
        '''
        if "Authorization" not in cherrypy.request.headers:
            self.logger.debug("Authorization header is not set")
            return False

        if "Travis-Repo-Slug" not in cherrypy.request.headers:
            self.logger.debug("Travis-Repo-Slug header is not set")
            return False

        return check_authorization(
            cherrypy.request.headers["Travis-Repo-Slug"],
            cherrypy.request.headers["Authorization"]
        )


if __name__ == "__main__":
    # configure cherrypy webserver host and port
    # inspired by https://github.com/craigkerstiens/cherrypy-helloworld
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', '5000')),
    })
    cherrypy.quickstart(TravisParser())
