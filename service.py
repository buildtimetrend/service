#!/usr/bin/env python
# vim: set expandtab sw=4 ts=4:
"""
Buildtime Trend as a Service Cherrypy handlers.

Service components :
- /dashboard : display Buildtime Trend dashboard of hosted projects
- /stats     : display Buildtime Trend dashboard with service statistics
- /badge     : generate badges with metrics of project build data
- /travis    : retrieve and parse build data from Travis CI

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
import cgi
import cherrypy
import constants
from buildtimetrend.travis import process_notification_payload
from buildtimetrend.travis import check_authorization
from buildtimetrend.settings import Settings
from buildtimetrend import logger
from buildtimetrend.tools import get_repo_slug
from buildtimetrend.tools import check_file
from buildtimetrend.tools import file_is_newer
from buildtimetrend.keenio import check_time_interval
from buildtimetrend.keenio import get_avg_buildtime
from buildtimetrend.keenio import get_total_builds
from buildtimetrend.keenio import get_pct_passed_build_jobs
from buildtimetrend.keenio import get_result_color
from buildtimetrend.keenio import get_total_build_jobs
from buildtimetrend.keenio import get_latest_buildtime
from buildtimetrend.keenio import get_dashboard_config
from buildtimetrend.keenio import get_all_projects
from buildtimetrend.service import is_repo_allowed
from buildtimetrend.service import format_duration
from buildtimetrend.service import validate_travis_request
from celery_worker import is_worker_enabled
import tasks

SERVICE_WEBSITE_LINK = "<a href='https://buildtimetrend.github.io/service'>" \
                       "Buildtime Trend as a Service</a>"
TRAVIS_URL = '/travis'
ASSETS_URL = '/assets'
DASHBOARD_URL = '/dashboard'
STATS_URL = '/stats'
BADGE_URL = '/badge'
STATIC_DIR = os.path.join(os.path.abspath('.'), 'static')
DASHBOARD_DIR = os.path.join(STATIC_DIR, 'dashboard')
ASSETS_DIR = os.path.join(DASHBOARD_DIR, 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
FAVICON_PATH = os.path.join(IMAGES_DIR, 'favicon.ico')
APPLE_ICON_PATH = os.path.join(IMAGES_DIR, 'apple-touch-icon.png')
APPLE_ICON_PRECOMPOSED_PATH = os.path.join(IMAGES_DIR,
                                           'apple-touch-icon-precomposed.png')
ROBOTS_PATH = os.path.join(STATIC_DIR, 'robots.txt')


class Dashboard(object):

    """Buildtime Trend Dashboard handler."""

    def __init__(self):
        """Constructor."""
        self.settings = Settings()
        self.logger = logger

        self.file_projects = os.path.join(DASHBOARD_DIR, "projects.html")
        self.file_projects_service = os.path.join(
            DASHBOARD_DIR, "projects_service.html"
        )
        self.file_index = os.path.join(DASHBOARD_DIR, "index.html")
        self.file_index_service = os.path.join(
            DASHBOARD_DIR, "index_service.html"
        )

    @cherrypy.expose
    def index(self):
        """Index page with overview of hosted projects."""
        # Create project overview for Buildtime Trend as a Service :
        # if it doesn't exist, or if it is older than the file from
        # which it is generated
        if modify_index(self.file_projects, self.file_projects_service):
            return open(self.file_projects_service)
        else:
            raise cherrypy.HTTPError(404, "File not found")

    def dashboard(self):
        """Dashboard page."""
        # Create dashboard index for Buildtime Trend as a Service :
        # if it doesn't exist, or if it is older than the file from
        # which it is generated
        if modify_index(self.file_index, self.file_index_service):
            return open(self.file_index_service)
        else:
            raise cherrypy.HTTPError(404, "File not found")

    @cherrypy.expose
    def default(self, repo_owner=None, repo_name=None, page=""):
        """
        Default page.

        Returns index page or config file,
        redirects index page in all other cases.

        Parameters :
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        - page : requested page (index.html or config.js)
        """
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
        """
        Config file for dashboard.

        Parameters :
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        """
        # define extra settings
        extra = {
            'serviceUrl': ""  # use this service instance for badge generation
        }

        repo = get_repo_slug(repo_owner, repo_name)

        # Check if repo is allowed
        if repo is not None and not is_repo_allowed(repo):
            message = "Project '%s' is not allowed."
            self.logger.info(message, repo)
            extra['message'] = message % cgi.escape(repo)
            repo = None
        else:
            self.logger.info("Generated dashboard config for project %s", repo)

        # add project list
        extra.update(get_config_project_list())

        # return config file
        return get_dashboard_config(repo, extra)


class Stats(object):

    """Service stats page handler."""

    def __init__(self):
        """Constructor."""
        self.settings = Settings()
        self.logger = logger

        self.file_stats = os.path.join(DASHBOARD_DIR, "stats.html")
        self.file_stats_service = os.path.join(
            DASHBOARD_DIR, "stats_service.html"
        )

    @cherrypy.expose
    def index(self):
        """Server stats page."""
        # Create stats page for Buildtime Trend as a Service,
        # if it doesn't exist, or if it is older than the file from
        # which it is generated
        if modify_index(self.file_stats, self.file_stats_service):
            return open(self.file_stats_service)
        else:
            raise cherrypy.HTTPError(404, "File not found")

    @cherrypy.expose
    def config_js(self):
        """
        Config file for dashboard.

        Parameters :
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        """
        # define extra settings
        extra = {
            'projectName': "Service stats"
        }

        # add project list
        extra.update(get_config_project_list())

        # return config file
        return get_dashboard_config(None, extra)


class Badges(object):

    """Generate shield badges."""

    def __init__(self):
        """Initialise class."""
        self.settings = Settings()

        # get logger
        self.logger = logger

    @cherrypy.expose
    def default(self, repo_owner=None, repo_name=None, badge_type="avg",
                interval=None):
        """
        Generate a shield badge.

        Parameters :
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        - badge_type : type of badge, options :
          - latest : buildtime of last build job
          - avg : average buildtime of buildjobs in period set by `interval`
                  (default)
          - jobs : number of build jobs in period set by `interval`
          - builds : number of builds in period set by `interval`
          - passed : percentage of successful build jobs during `interval`
        - interval : time interval, options :
          - week (default) : events of last week (last 7 days)
          - month : events of last month (last 30 days)
          - year : events of last year (last 52 weeks)
        """
        # parameter check
        repo = get_repo_slug(repo_owner, repo_name)
        badge_type = str(badge_type).lower()
        interval = check_time_interval(interval)["name"]

        badge_subject = "buildtime"
        badge_status = "trend"
        badge_colour = "blue"
        format_string = "{:d}"

        if repo is not None and is_repo_allowed(repo):
            if badge_type == "latest":
                # get last duration
                value = get_latest_buildtime(repo)
                badge_status = format_duration(value)
            elif badge_type == "jobs":
                badge_subject = "%s_(%s)" % (badge_type, interval)
                value = get_total_build_jobs(repo, interval)
                format_string = "{:d}"
                badge_status = format_string.format(value)
            elif badge_type == "builds":
                badge_subject = "%s_(%s)" % (badge_type, interval)
                value = get_total_builds(repo, interval)
                format_string = "{:d}"
                badge_status = format_string.format(value)
            elif badge_type == "passed":
                badge_subject = "%s_(%s)" % (badge_type, interval)
                value = get_pct_passed_build_jobs(repo, interval)
                badge_colour = get_result_color(value, 100, 75)
                format_string = "{:d}%"
                badge_status = format_string.format(value)
            else:
                # calculate average
                badge_subject = "%s_(%s)" % (badge_subject, interval)
                value = get_avg_buildtime(repo, interval)
                badge_status = format_duration(value)

            # valid duration is 0 or greater int or float
            if not(type(value) in (float, int) and value >= 0):
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

    """Root handler."""

    def __init__(self):
        """
        Initialise class.

        Load config file and set loglevel, define error page handler
        """
        self.settings = Settings()
        self.settings.load_settings(config_file=constants.CONFIG_FILE)
        self.settings.set_client(
            constants.CLIENT_NAME,
            constants.CLIENT_VERSION
        )

        self.file_index = os.path.join(STATIC_DIR, "index.html")

        cherrypy.config.update({'error_page.404': self.error_page_404})

        # get logger
        self.logger = logger

    @cherrypy.expose
    def index(self):
        """Index page."""
        if check_file(self.file_index):
            return open(self.file_index)
        else:
            raise cherrypy.HTTPError(404, "File not found")

    def error_page_404(self, status, message, traceback, version):
        """Error Page (404)."""
        self.logger.error("Cherrypy %s : Error loading page (%s) : %s\n"
                          "Traceback : %s",
                          version, status, message, traceback)
        return "This page doesn't exist, please check usage on " \
               "the %s website." % SERVICE_WEBSITE_LINK


class TravisParser(object):

    """
    Travis CI build timing and build data parser.

    Retrieve timing data from Travis CI, parse it and store it in Keen.io.
    """

    def __init__(self):
        """Initialise class."""
        self.settings = Settings()

        # get logger
        self.logger = logger

    @cherrypy.expose
    def default(self, repo_owner=None, repo_name=None, build=None,
                payload=None):
        """
        Default handler.

        Visiting this page triggers loading and processing the build log
        and data of a travis CI build process.

        Parameters:
        - repo_owner : name of the Github repo owner, fe. `buildtimetrend`
        - repo_name : name of the Github repo, fe. `service`
        - build : build number
        """
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # reset settings
        self.settings.set_project_name(None)
        self.settings.add_setting('build', None)

        self.logger.debug(
            "Check Travis headers : %r",
            cherrypy.request.headers
        )

        repo = get_repo_slug(repo_owner, repo_name)

        # load parameters from the Travis notification payload
        if self.check_travis_notification():
            payload_params = process_notification_payload(payload)

            # assign payload parameters
            if repo is None and "repo" in payload_params:
                repo = payload_params["repo"]
            if build is None and "build" in payload_params:
                build = payload_params["build"]

        self.logger.warning(
            "Request to process build #%s of repo %s", str(build), str(repo)
        )

        return self.schedule_task(repo, build)

    def schedule_task(self, repo, build):
        """Check parameters and schedule task."""
        # check parameter validity, check returns error message
        # or None if parameters are valid
        params_valid = validate_travis_request(repo, build)
        if params_valid is not None:
            self.logger.warning(params_valid)
            return params_valid

        # process travis build
        if is_worker_enabled():
            task = tasks.process_travis_buildlog.delay(repo, build)
            return "Task scheduled to process build #%s of repo %s : %s" % \
                (cgi.escape(str(build)),
                 cgi.escape(str(repo)),
                 cgi.escape(str(task.id)))
        else:
            return tasks.process_travis_buildlog(repo, build)

    def check_travis_notification(self):
        """
        Check Travis CI notification request.

        Load Authorization and Travis-Repo-Slug headers and check if
        the Authorization header is correct
        """
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


def get_config_project_list():
    """
    Return a list of repoNames of projects hosted on this website.

    Create list of only allowed project repos
    and convert values from unicode to UTF8
    """
    allowed_projects = [
        x.encode('UTF8') for x in get_all_projects() if is_repo_allowed(x)
    ]

    if len(allowed_projects) > 0:
        return {'projectList': allowed_projects}
    else:
        return {}


def modify_index(file_original, file_modified):
    """
    Create index file for Buildtime Trend as a Service.

    It adjust paths to 'assets' :
    the relative path is change to an absolute path.

    Parameters:
    - file_original : Path of the original file
    - file_modified : Path of the modified file hosted on the service
    """
    if not file_is_newer(file_modified, file_original):
        with open(file_original, 'r') as infile, \
                open(file_modified, 'w') as outfile:
            for line in infile:
                line = line.replace("assets", ASSETS_URL)
                outfile.write(line)

    if check_file(file_modified):
        logger.info(
            "Created index service file : %s",
            file_modified
        )
        return True
    else:
        return False


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
        '/apple-touch-icon.png': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': APPLE_ICON_PATH
        },
        '/apple-touch-icon-precomposed.png': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': APPLE_ICON_PRECOMPOSED_PATH
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
    cherrypy.tree.mount(Stats(), STATS_URL)
    cherrypy.tree.mount(Badges(), BADGE_URL)
    cherrypy.tree.mount(TravisParser(), TRAVIS_URL)

    # start server
    cherrypy.engine.start()
    cherrypy.engine.block()
