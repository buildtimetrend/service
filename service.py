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
import json
import cgi
import cherrypy
from buildtimetrend.travis import TravisData
from buildtimetrend.settings import Settings
from buildtimetrend.tools import get_logger
from buildtimetrend.tools import set_loglevel
from buildtimetrend.keenio import log_build_keen
from buildtimetrend.keenio import keen_is_writable


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

        # set loglevel
        set_loglevel("INFO")
        self.logger = get_logger()

    @cherrypy.expose
    def index(self):
        '''
        Index page
        '''
        return "Coming soon, " \
               "<a href='https://github.com/buildtimetrend/service'>" \
               "Buildtime Trend as a Service</a>."

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

        # load parameters from the Travis notification payload
        self.load_travis_payload(payload)

        # process url (GET) parameters
        if repo is not None:
            self.logger.info("Build repo : %s", repo)
            self.settings.set_project_name(repo)

        if build is not None:
            self.logger.info("Build number : %s", str(build))
            self.settings.add_setting('build', build)

        # process travis build
        return self.process_travis_buildlog()

    def process_travis_buildlog(self):
        '''
        Check parameters, load build data from Travis CI,
        process it and send to Keen.io for storage.
        '''
        repo = self.settings.get_project_name()
        if repo is None:
            self.logger.warning("Repo is not set")
            return "Repo is not set, use repo=user/repo"

        # check if repo is allowed
        allowed_repo = ["buildtimetrend", "ruleant"]
        if not any(x in repo for x in allowed_repo):
            message = "The supplied repo is not allowed : %s"
            self.logger.warning(message, repo)
            return message % cgi.escape(repo)

        build = self.settings.get_setting('build')
        if build is None:
            self.logger.warning("Build number is not set")
            return "Build number is not set, use build=build_id"

        travis_data = TravisData(repo, build)

        # retrieve build data using Travis CI API
        self.logger.info("Retrieve build #%s data of %s from Travis CI",
                    build, repo)
        travis_data.get_build_data()

        # process all build jobs
        travis_data.process_build_jobs()

        if not keen_is_writable():
            return "Keen IO write key not set, no data was sent"

        # send build job data to Keen.io
        for build_job in travis_data.build_jobs:
            self.logger.info("Send build job #%s data to Keen.io", build_job)
            log_build_keen(travis_data.build_jobs[build_job])

        message = "Succesfully retrieved build #%s data of %s from Travis CI" \
                  " and sent to Keen.io"
        self.logger.info(message, build, repo)
        return message % (cgi.escape(build), cgi.escape(repo))

    def load_travis_payload(self, payload):
        '''
        Load payload from Travis notification
        '''
        self.logger.info("Check Travis headers : %r", cherrypy.request.headers)

        if payload is None:
            return

        json_payload = json.loads(payload)
        self.logger.info("Travis Payload : %r.", json_payload)

        # get repo name from payload
        if ("repository" in json_payload
                and "owner_name" in json_payload["repository"]
                and "name" in json_payload["repository"]):

            repo = "%s/%s" % \
                (json_payload["repository"]["owner_name"],
                 json_payload["repository"]["name"])

            self.logger.info("Build repo : %s", repo)
            self.settings.set_project_name(repo)

        # get build number from payload
        if "number" in json_payload:
            self.logger.info("Build number : %s", str(json_payload["number"]))
            self.settings.add_setting('build', json_payload['number'])


if __name__ == "__main__":
    # configure cherrypy webserver host and port
    # inspired by https://github.com/craigkerstiens/cherrypy-helloworld
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', '5000')),
        'tools.json_in.on': True,
        'tools.json_in.force': False,
    })
    cherrypy.quickstart(TravisParser())
