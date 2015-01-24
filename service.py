#!/usr/bin/env python
# vim: set expandtab sw=4 ts=4:
'''
Retrieve Travis CI build data and log to Keen.io

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
'''

import os
import cgi
import cherrypy
from buildtimetrend.travis import process_notification_payload
from buildtimetrend.travis import check_authorization
from buildtimetrend.travis import TravisData
from buildtimetrend.settings import Settings
from buildtimetrend.tools import get_logger
from buildtimetrend.tools import get_repo_slug
from buildtimetrend.tools import check_file
from buildtimetrend.tools import file_is_newer
from buildtimetrend.keenio import check_time_interval
from buildtimetrend.keenio import log_build_keen
from buildtimetrend.keenio import keen_is_writable
from buildtimetrend.keenio import get_avg_buildtime
from buildtimetrend.keenio import get_total_builds
from buildtimetrend.keenio import get_pct_passed_build_jobs
from buildtimetrend.keenio import get_result_color
from buildtimetrend.keenio import get_total_build_jobs
from buildtimetrend.keenio import get_latest_buildtime
from buildtimetrend.keenio import generate_dashboard_config_file


SERVICE_WEBSITE_LINK = "<a href='https://github.com/buildtimetrend/service'>" \
                       "Buildtime Trend as a Service</a>"
TRAVIS_URL = '/travis'
ASSETS_URL = '/assets'
DASHBOARD_URL = '/dashboard'
BADGE_URL = '/badge'
STATIC_DIR = os.path.join(os.path.abspath('.'), 'static')
DASHBOARD_DIR = os.path.join(STATIC_DIR, 'dashboard')
ASSETS_DIR = os.path.join(DASHBOARD_DIR, 'assets')
FAVICON_PATH = os.path.join(ASSETS_DIR, 'images', 'favicon.ico')
ROBOTS_PATH = os.path.join(STATIC_DIR, 'robots.txt')


class Dashboard(object):
    '''
    Hosts Buildtime Trend Dashboard
    '''
    def __init__(self):
        self.settings = Settings()
        self.logger = get_logger()

        self.file_projects = os.path.join(DASHBOARD_DIR, u"projects.html")
        self.file_projects_service = os.path.join(
            DASHBOARD_DIR, u"projects_service.html"
        )
        self.file_index = os.path.join(DASHBOARD_DIR, u"index.html")
        self.file_index_service = os.path.join(
            DASHBOARD_DIR, u"index_service.html"
        )

    @cherrypy.expose
    def index(self):
        '''
        Index page with overview of hosted projects
        '''
        # Create project overview for Buildtime Trend as a Service :
        # if it doesn't exist, or if it is older than the file from
        # which it is generated
        if self.modify_index(self.file_projects, self.file_projects_service):
            return open(self.file_projects_service)
        else:
            raise cherrypy.HTTPError(404, "File not found")

    def dashboard(self):
        '''
        Dashboard page
        '''
        # Create dashboard index for Buildtime Trend as a Service :
        # if it doesn't exist, or if it is older than the file from
        # which it is generated
        if self.modify_index(self.file_index, self.file_index_service):
            return open(self.file_index_service)
        else:
            raise cherrypy.HTTPError(404, "File not found")

    @cherrypy.expose
    def default(self, repo_owner=None, repo_name=None, page=""):
        '''
        Default page, returns index page or config file,
        redirects index page in all other cases.

        Parameters :
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        - page : requested page (index.html or config.js)
        '''
        if page == "index.html" or repo_owner is None and repo_name is None:
            # display index page
            return self.dashboard()
        elif page == "config.js":
            # display config file
            return self.config_js(repo_owner, repo_name)
        else:
            # redirect to index page, if no other page matches
            if repo_owner is None or repo_name is None:
                url = DASHBOARD_URL
            else:
                repo_slug = get_repo_slug(repo_owner, repo_name)
                url = "%s/%s/index.html" % \
                    (DASHBOARD_URL, cgi.escape(repo_slug))

            # rewrite url
            raise cherrypy.HTTPRedirect(url)

    @cherrypy.expose
    def config_js(self, repo_owner=None, repo_name=None):
        '''
        Config file for dashboard

        Parameters :
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        '''
        # set sample config file path
        self.settings.add_setting(
            'dashboard_sample_configfile',
            os.path.join(DASHBOARD_DIR, u"config_sample.js")
        )

        repo = get_repo_slug(repo_owner, repo_name)
        if repo is None:
            repo = ""

        # set config file path
        config_dir = os.path.join('/tmp', repo)
        config_file = os.path.join(config_dir, u"config.js")
        self.settings.add_setting('dashboard_configfile', config_file)

        # generate config file
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        if generate_dashboard_config_file(repo):
            # return config file
            return open(config_file)
        else:
            raise cherrypy.HTTPError(404, "Configfile could not be generated")

    def modify_index(self, file_original, file_modified):
        '''
        Create index file for Buildtime Trend as a Service :
        adjust paths to 'assets'

        Parameters:
        - file_original : Path of the original file
        - file_modified : Path of the modified file hosted on the service
        '''
        if not file_is_newer(file_modified, file_original):
            with open(file_original, 'rb') as infile, \
                    open(file_modified, 'w') as outfile:
                for line in infile:
                    line = line.replace("assets", ASSETS_URL)
                    outfile.write(line)

        if check_file(file_modified):
            self.logger.info(
                "Created index service file : %s",
                file_modified
            )
            return True
        else:
            return False


class Badges(object):
    '''
    Generates shield badges
    '''

    def __init__(self):
        '''
        Initialise class, by loading a config file and setting loglevel
        '''
        self.settings = Settings()

        # get logger
        self.logger = get_logger()

    @cherrypy.expose
    def default(self, repo_owner=None, repo_name=None, badge_type="avg",
              interval=None):
        '''
        Generates a shield badge
        '''
        # parameter check
        repo = get_repo_slug(repo_owner, repo_name)
        badge_type = str(badge_type).lower()
        interval = check_time_interval(interval)["name"]

        badge_subject = "buildtime"
        badge_status = "trend"
        badge_colour = "blue"
        format_string = "{:.1f}s"

        if repo is not None and is_repo_allowed(repo) is None:
            if badge_type == "latest":
                # get last duration
                value = get_latest_buildtime(repo)
            elif badge_type == "jobs":
                badge_subject = "%s_(%s)" % (badge_type, interval)
                value = get_total_build_jobs(repo, interval)
                format_string = "{:d}"
            elif badge_type == "builds":
                badge_subject = "%s_(%s)" % (badge_type, interval)
                value = get_total_builds(repo, interval)
                format_string = "{:d}"
            elif badge_type == "passed":
                badge_subject = "%s_(%s)" % (badge_type, interval)
                value = get_pct_passed_build_jobs(repo, interval)
                badge_colour = get_result_color(value, 100, 75)
                format_string = "{:d}%"
            else:
                # calculate average
                badge_subject = "%s_(%s)" % (badge_subject, interval)
                value = get_avg_buildtime(repo, interval)

            # valid duration is 0 or greater int or float
            if type(value) in (float, int) and value >= 0:
                badge_status = format_string.format(value)
            else:
                badge_status = "unknown"
                badge_colour = "lightgrey"

            self.logger.info(
                "Badge type %s (interval : %s) for %s, value : %s",
                badge_type, interval, repo, badge_status)

        # Redirect to shields.io API to generate badge
        raise cherrypy.HTTPRedirect(
            "https://img.shields.io/badge/%s-%s-%s.svg" %
            (badge_subject, badge_status, badge_colour)
        )


class Root(object):
    '''
    Retrieve timing data from Travis CI, parse it and store it in Keen.io
    '''

    def __init__(self):
        '''
        Initialise class, by loading a config file and setting loglevel
        '''
        self.settings = Settings()
        self.settings.load_settings(config_file="config_service.yml")

        cherrypy.config.update({'error_page.404': self.error_page_404})

        # get logger
        self.logger = get_logger()

    @cherrypy.expose
    def index(self):
        '''
        Index page
        '''
        return "Coming soon : %s" % SERVICE_WEBSITE_LINK

    def error_page_404(self, status, message, traceback, version):
        '''
        Page 404
        '''
        self.logger.error("Cherrypy %s : Error loading page (%s) : %s\n"
                          "Traceback : %s",
                          version, status, message, traceback)
        return "This page doesn't exist, please check usage on " \
               "the %s website." % SERVICE_WEBSITE_LINK


class TravisParser(object):
    '''
    Retrieve timing data from Travis CI, parse it and store it in Keen.io
    '''

    def __init__(self):
        '''
        Initialise class, by loading a config file and setting loglevel
        '''
        self.settings = Settings()

        # get logger
        self.logger = get_logger()

    @cherrypy.expose
    def default(self, repo=None, build=None, payload=None):
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
        msg_is_repo_allowed = is_repo_allowed(repo)
        if msg_is_repo_allowed is not None:
            return msg_is_repo_allowed

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

def is_repo_allowed(repo):
    '''
    Check if repo is allowed
    List of allowed repos is set by setting 'allowed_repo',
    if not defined, the repo is not checked,
    'allowed_repo' can have multiple values, if any of them matches
    a substring of the repo, the repo is allowed.

    Parameters:
    -repo : repo name
    '''
    logger = get_logger()

    if repo is None:
        message = "Repo is not defined"
        logger.warning(message)
        return message

    allowed_repo = Settings().get_setting("allowed_repo")
    if allowed_repo is not None and \
            not any(x in repo for x in allowed_repo):
        message = "The supplied repo is not allowed : %s"
        logger.warning(message, repo)
        return message % cgi.escape(repo)

    return None

if __name__ == "__main__":
    # configure cherrypy webserver host and port
    # inspired by https://github.com/craigkerstiens/cherrypy-helloworld
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', '5000')),
    })

    ROOT_CONFIG = {
        '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': FAVICON_PATH
        },
        '/robots.txt': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': ROBOTS_PATH
        },
        ASSETS_URL: {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': ASSETS_DIR
        }
    }

    # assign handlers to entry paths
    cherrypy.tree.mount(Root(), '/', ROOT_CONFIG)
    cherrypy.tree.mount(Dashboard(), DASHBOARD_URL)
    cherrypy.tree.mount(Badges(), BADGE_URL)
    cherrypy.tree.mount(TravisParser(), TRAVIS_URL)

    # start server
    if hasattr(cherrypy.engine, 'block'):
        # 3.1 syntax
        cherrypy.engine.start()
        cherrypy.engine.block()
    else:
        # 3.0 syntax
        cherrypy.server.quickstart()
        cherrypy.engine.start()
