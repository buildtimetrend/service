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
import sys
import cgi
import cherrypy
from buildtimetrend.travis import TravisData
from buildtimetrend.settings import Settings
from buildtimetrend.keenio import log_build_keen
from buildtimetrend.keenio import keen_is_writable


class TravisParser(object):
    '''
    Retrieve timing data from Travis CI, parse it and store it in Keen.io
    '''

    @cherrypy.expose
    def index(self):
        return "Welcome to Buildtime Trend Service"

    @cherrypy.expose
    def travis(self, repo_slug=None, build=None):
        settings = Settings()
        settings.load_config_file("config_service.yml")

        if repo_slug is not None:
            settings.set_project_name(repo_slug);

        repo_slug = settings.get_project_name()
        if repo_slug is None:
            return "Repo is not set, use repo_slug=user/repo"

        # check if repo is allowed
        allowed_repo = ["buildtimetrend", "ruleant"]
        if not any(x in repo_slug for x in allowed_repo):
            return "The supplied repo is not allowed : %s" % cgi.escape(repo_slug)

        if build is not None:
            settings.add_setting('build', build);

        build = settings.get_setting('build')
        if build is None:
            return "Build number is not set, use build=build_id"

        travis_data = TravisData(repo_slug, build)

        # retrieve build data using Travis CI API
        print "Retrieve build #%s data of %s from Travis CI" % \
            (build, repo_slug)
        travis_data.get_build_data()

        # process all build jobs
        travis_data.process_build_jobs()

        if not keen_is_writable():
            return "Keen IO write key not set, no data was sent"

        # send build job data to Keen.io
        for build_job in travis_data.build_jobs:
            print "Send build job #%s data to Keen.io" % build_job
            log_build_keen(travis_data.build_jobs[build_job])

        return "Succesfully retrieved build #%s data of %s from Travis CI and sent to Keen.io" % \
            (cgi.escape(build), cgi.escape(repo_slug))
       

if __name__ == "__main__":
    # configure cherrypy webserver host and port
    # inspired by https://github.com/craigkerstiens/cherrypy-helloworld
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', '5000')),
    })
    cherrypy.quickstart(TravisParser())
