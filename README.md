# Project discontinued, will be archived!

Buildtime Trend as a Service
============================

Visualise what's trending in your build process

[![Buildtime Trend as a Service](http://img.shields.io/badge/release-v0.3-blue.svg)](https://github.com/buildtimetrend/service/releases/latest)
[![Buildtime Trend as a Service (dev)](http://img.shields.io/badge/dev-v0.4.dev-blue.svg)](https://github.com/buildtimetrend/service/zipball/master)

[![Build Status](https://travis-ci.org/buildtimetrend/service.svg?branch=master)](https://travis-ci.org/buildtimetrend/service)
[![Code Health](https://landscape.io/github/buildtimetrend/service/master/landscape.svg)](https://landscape.io/github/buildtimetrend/service/master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/buildtimetrend/service/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/buildtimetrend/service/?branch=master)
[![Codacy Badge](https://www.codacy.com/project/badge/4ff71ed6b542493ab6f407f4c37aeb01)](https://www.codacy.com/public/ruleant/service)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/88a900bee57a41ec82a3fd75e8e2bb0a/badge.svg)](https://www.quantifiedcode.com/app/project/88a900bee57a41ec82a3fd75e8e2bb0a)
[![Stack Share](http://img.shields.io/badge/tech-stack-0690fa.svg)](http://stackshare.io/ruleant/buildtime-trend)

[![Buildtime trend](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/latest)](https://buildtimetrend-dev.herokuapp.com/dashboard/buildtimetrend/service/index.html)
[![Total builds](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/builds/month)](https://buildtimetrend-dev.herokuapp.com/dashboard/buildtimetrend/service/index.html)
[![Percentage passed build jobs](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/passed/month)](https://buildtimetrend-dev.herokuapp.com/dashboard/buildtimetrend/service/index.html)
[![Days since last failed build job](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/last_fail)](https://buildtimetrend-dev.herokuapp.com/dashboard/buildtimetrend/service/index.html)

This project contains the files that offer Buildtime Trend as a service. The [Buildtime Trend library](https://github.com/buildtimetrend/python-lib) powers this service.

## Usage

### Use the service available on Heroku

- production : https://buildtimetrend.herokuapp.com/ (Currently discontinued)
    
    Learn how to [setup your own service](https://github.com/buildtimetrend/python-lib/wiki/Running-service-on-Heroku) on Heroku.

- development : https://buildtimetrend-dev.herokuapp.com/

    Used for development, expect frequent changes, accepts only a limited number of projects.
    [Contact us](#Contact) if you'd like to test the development version. It's recommended to use the production version.

### Clone the project and deploy it to Heroku

See [instructions on the wiki](https://github.com/buildtimetrend/python-lib/wiki/Running-service-on-Heroku) on how to configure the service on Heroku.

### Run it on your own server

- Launch a CherryPy instance hosting the service :

```bash
python service.py
```

> **Remark :** By default it will attach to port 5000, use environment variable `PORT` to override this.

More [configuration options](#config-file) are available.

- To enable a worker to handle the task queue (optional) :

```bash
utils/start_worker.sh
```

A Celery compatible task queue service is required to use the task queue, see the `task_queue` config parameter in the [configuration options](#config-file) section.

## Components

- [Index page](#index-page)
- [Dashboard](#dashboard)
- [Service usage statistics](#service-usage-statistics)
- [Shield badges](#shield-badges)
- [Process Travis CI build log](#process-travis-ci-build-log)

### Index page
- path : `/`

### Dashboard

Display a dashboard with Buildtime Trend charts

- path : `/dashboard`
- usage : `/dashboard/repo_owner/repo_name?refresh=<refresh_rate>&timeframe=<timeframe_setting>`
- parameters :
  - `repo_owner` : name of the Github repo owner, fe. `buildtimetrend`
  - `repo_name` : name of the Github repo, fe. `service`
  - `refresh` (optional) : enables auto-refreshing the dashboard charts. 0 = disabled (default), a positive integer is the number of minutes after which the charts are refreshed, a value of 10 will refresh the charts every 10 minutes. The refresh rate should at least be equal to maximum age of the Query cache, if it is less, the cache max age value will be used (typically, 10 min).
  - `timeframe` (optional) : the default timeframe can be set with this url parameter. Possible values : `day`, `week`, `month`, `year`. If it is not defined the default timeframe is used (`week`)
  - `filter_*` : set the default filter value. When this url parameter is defined, the corresponding filter dropdown will be set to this value and it will be applied to the queries of all charts and metrics. Available filters :
    - `filter_build_matrix` : Build matrix environment settings, usually a combination of language, language version and operating system : fe. `python 2.7 linux`
    - `filter_build_result` : Build job result, possible values : `passed`, `errored`, `failed`, ...
    - `filter_build_trigger` : What triggered the build job, possible values : `pull_request`, `push` (git push)
    - `filter_branch` : Repository branch that was build : fe. `master`


> **Remark :** When visiting `/dashboard` (without parameters), an overview of all hosted projects is displayed.

### Service usage statistics

Display a dashboard with Buildtime Trend service usage statistics

- path : `/stats`
- usage : `/stats?timeframe=<timeframe_setting>`
- parameters :
  - `timeframe` (optional) : the default timeframe can be set with this url parameter. Possible values : `day`, `week`, `month`, `year`. If it is not defined the default timeframe is used (`week`)

### Shield badges

Generate a shield badges

- path : `/badge`
- usage : `/badge/repo_owner/repo_name/badge_type/interval`
- parameters :
  - `repo_owner` : name of the Github repo owner, fe. `buildtimetrend`
  - `repo_name` : name of the Github repo, fe. `service`
  - `badge_type` : type of badge, options :
    - `latest` : buildtime of last build job
    - `avg` : average buildtime of buildjobs in period set by `interval` (default)
    - `jobs` : number of build jobs in period set by `interval`
    - `builds` : number of builds in period set by `interval`
    - `passed` : percentage of successful build jobs during `interval`
    - `last_fail` : days since last failed build job
  - `interval` : time interval, options :
    - `week` (default) : events of last week (last 7 days)
    - `month` : events of last month (last 30 days)
    - `year` : events of last year (last 52 weeks)

#### Badge examples
- ![Latest build duration](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/latest) : `/badge/buildtimetrend/service/latest`
- ![Average buildtime (week)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/avg/week) : `/badge/buildtimetrend/service/avg/week`
- ![Average buildtime (month)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/avg/month) : `/badge/buildtimetrend/service/avg/month`
- ![Average buildtime (year)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/avg/year) : `/buildtimetrend/service/avg/year`
- ![Build jobs (week)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/jobs/week) : `/badge/buildtimetrend/service/jobs/week`
- ![Build jobs (month)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/jobs/month) : `/badge/buildtimetrend/service/jobs/month`
- ![Build jobs (year)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/jobs/year) : `/buildtimetrend/service/jobs/year`
- ![Builds (week)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/builds/week) : `/badge/buildtimetrend/service/builds/week`
- ![Builds (month)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/builds/month) : `/badge/buildtimetrend/service/builds/month`
- ![Builds (year)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/builds/year) : `/buildtimetrend/service/builds/year`
- ![% passed build jobs (week)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/passed/week) : `/badge/buildtimetrend/service/passed/week`
- ![% passed build jobs (month)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/passed/month) : `/badge/buildtimetrend/service/passed/month`
- ![% passed build jobs (year)](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/passed/year) : `/badge/buildtimetrend/service/passed/year`
- ![days since last failed build job](https://buildtimetrend-dev.herokuapp.com/badge/buildtimetrend/service/last_fail) : `/badge/buildtimetrend/service/last_fail`

### Process Travis CI build log

Loads a Travis CI build log file, processes it and sends the data to Keen.io.

- path : `/travis`
- usage : `/travis/<repo_owner>/<repo_name>/<first_build>/<last_build>`
- parameters :
  - `repo_owner` : name of the Github repo owner, fe. `buildtimetrend`
  - `repo_name` : name of the Github repo, fe. `service`
  - `first_build` : Travis CI build number of the first build to be processed
  - `last_build` : (optional) Travis CI build number of the last build to be processed

If `last_build` is not defined, only a single build will be processed, namely the one defined by `first_build`.
If `last_build` is defined, it turns into batch mode : multiple builds will be processed : all builds from `first_build` to and including `last_build` will be scheduled to be processed.
To limit the load on the worker, a delay is added to every next build. F.e. build #1 will be executed immediately, build #2 after x seconds, build #3 after x\*2 seconds, build #n after x\*(n-1) seconds.
By default the delay is 3 seconds, but this can be configured with the `multi_import`.`delay` setting in `config_service.yml` or `BTT_MULTI_DELAY` env variable.
The maximum number of builds that can be imported at once in batch mode is by default limited to 100. This can be configured with the `multi_import`.`max_builds` setting in `config_service.yml` or `BTT_MULTI_MAX_BUILDS` env variable.

OR

  - `payload` : Travis CI notification payload, more info in the [Travis CI documentation](http://docs.travis-ci.com/user/notifications/#Webhook-notification)

To trigger the service at the end of a Travis CI build, add this to your `.travis.yml` file:

```yaml
    notifications:
      webhooks:
        # trigger Buildtime Trend Service to parse Travis CI log and send result to Keen.io
        - https://buildtimetrend.herokuapp.com/travis
```

When Buildtime Trend Service is triggered by a Travis CI notification, it will get the necessary parameters (repo name and build number) from the `payload` that is passed by Travis CI. This will trigger loading and parsing the Travis CI log of the corresponding build, the analysed data is stored in the Keen.io database.


Config file
-----------

Add a configfile named `config_service.yml` based on `config_sample.yml` to configure the way the service behaves.

- `denied_repo` : defines which repos are not allowed by the service. If the `denied_repo` setting is not defined, all repos are allowed (unless `allowed_repo` is defined, see below). If a substring matches the repo name, it is denied, so fe. `my_name` will disallow `my_name/my_first_repo` and `my_name/another_repo`. A complete repo name is valid as well.

> **Remark :** Setting `denied_repo` takes precedence over `allowed_repo`, if a repo name matches a rule in `denied_repo` setting, the repo will be denied, even if it matches a rule in `allowed_repo`.
Multiple entries are allowed, fe. :

```yaml
buildtimetrend:
  denied_repo:
    - "my_name" # denying all repo names that contain my_name
    - "another_name/some_repo" # denies this specific repo
```

- `allowed_repo` : defines which repos are allowed by the service. If the `allowed_repo` setting is not defined, all repos are allowed (unless denied by the `denied_repo` setting). If substring matches the repo name, it is allowed, so fe. `my_name` will allow `my_name/my_first_repo` and `my_name/another_repo`. A complete repo name is allowed as well.

> **Remark :** Setting `denied_repo` takes precedence over `allowed_repo`, if a repo name matches a rule in `denied_repo` setting, the repo will be denied, even if it matches a rule in `allowed_repo`.
Multiple entries are allowed, fe. :

```yaml
buildtimetrend:
  allowed_repo:
    - "my_name" # allowing all repo names that contain my_name
    - "another_name/some_repo" # allows this specific repo
```

- `travis_account_token` : define to enable checking Travis CI notification Authorization header. More info on Travis CI Webhook Authorization and where to find the Account token : http://docs.travis-ci.com/user/notifications/#Authorization-for-Webhooks

> **Remark :** the account token should be the one of the user who created the repo on Travis CI.

It can also be defined with the `TRAVIS_ACCOUNT_TOKEN` environment variable.

- `loglevel` : defines loglevel, possible values : `DEBUG`, `INFO`, `WARNING` (default), `ERROR`
It can also be defined with the `BTT_LOGLEVEL` environment variable.

- `task_queue` : configures using a task queue, powered by Celery, to process background tasks by a worker. Celery supports different kinds of backend task queues, which can be configured :

```yaml
buildtimetrend:
    task_queue:
        backend: "" # backend type fe. amqp, redis, ...
        broker_url: "" # backend instance url, format : transport://userid:password@hostname:port/virtual_host
```
If `task_queue` is defined, this will be enable using a worker to execute heavy tasks. To disable using a worker, remove the `task_queue` directive from the config file.

The `broker_url` can also be defined with several environment variables :
- `BTT_AMQP_URL` : set a AMQP based task queue instance. (fe. amqp://localhost/)
- `BTT_REDIS_URL` : set a Redis based task queue instance. (fe. redis://localhost/)
- `RABBITMQ_BIGWIG_URL` : environment variable set when creating a [RabbitMQ Bigwig instance on Heroku](https://elements.heroku.com/addons/rabbitmq-bigwig)
- `CLOUDAMQP_URL` : environment variable set when creating a [Cloud AMQP RabbitMQ instance on Heroku](https://elements.heroku.com/addons/cloudamqp)
- `REDISGREEN_URL` : environment variable set when creating a [Redis Green instance on Heroku](https://elements.heroku.com/addons/redisgreen)

The environment variables are checked in this order, the first one that is defined, will be used.
The backend type (amqp, redis, ...) associated with the environment variable will be set automatically.

- `multi_import` : configures batch mode when importing build timing data.

```yaml
buildtimetrend:
    multi_import:
        max_builds: 100 # maximum number of builds allowed in one batch
        delay: 3 # number of seconds between the start of each build
```
Setting `max_builds` is 100 by default, and can also be set with the `BTT_MULTI_MAX_BUILDS` environment variable.
Setting `delay` is 3 seconds by default, and can also be set with the `BTT_MULTI_DELAY` environment variable.

- `data_detail` : level of detail when storing build job data, possible values :
  - "minimal" : only get build(job) data, with total time, no detailed (sub)stages data is stored
  - "basic" : `minimal` + substages grouped into stages (for future use : currently equals `minimal`)
  - "full": `basic` + substages and stages details are stored (default)
  - "extended" : `full` + also store data of custom timestamps (for future use : currently equals `full`)

It can also be defined with the `BTT_DATA_DETAIL` environment variable.

- `repo_data_detail` : level of detail when storing build job data, but defined per repository. See `data_detail` for possible values. If a setting matches the repository name, the corresponding setting is used. Substrings are allowed, if a substring is part of a repo name, the corresponding setting is used. If no (sub)string matches a repo, the default setting `data_detail` is used.

Be carefull with substrings, if a repository name matches more than one entry, only the first one that matches will be used (not necessarily in the order as listed in the config file)

Don't use '-' to prepend the different repositories

```yaml
buildtimetrend:
  repo_data_detail:
    "my_name": "minimal" # sets `data_detail` to `minimal` for all repo names that contain my_name
    "another_name/some_repo": "basic # set `data_detail` to `basic` for this repositiry
```

Dependencies
------------

- `buildtimetrend` : [Buildtime Trend library](https://github.com/buildtimetrend/python-lib)
- `cherrypy` : [CherrPy](http://www.cherrypy.org/) A Minimalist Python Web Framework, making the API available as a web service
- `celery` : [Celery](http://www.celeryproject.org/) : Distributed Task Queue

See `requirements.txt` for package names and versions.

Bugs and feature requests
-------------------------

Please report bugs and add feature requests in the Github [issue tracker](https://github.com/buildtimetrend/python-lib/issues).

Contribute
----------

If you want to contribute to make Buildtime Trend even better, check out the [contribution](https://github.com/buildtimetrend/python-lib/wiki/Contribute) page.
We are looking for testers, developers, designers, ... and what more. [Contact us](#contact) if you want to help out.

Donations
---------

You can support the project by making a [donation](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=LG9M6QTBS9LKL). The donations will help pay for the hosting and support further development.

Credits
-------

For an overview of who contributed to create Buildtime trend, see [Credits](https://github.com/buildtimetrend/python-lib/wiki/Credits).

Contact
-------

Website : https://buildtimetrend.github.io/service

Mailinglist : [Buildtime Trend Community](https://groups.google.com/d/forum/buildtimetrend-dev)

Follow us on [Twitter](https://twitter.com/buildtime_trend), [Github](https://github.com/buildtimetrend) and [OpenHub](https://www.openhub.net/p/buildtime-trend).


License
-------

Copyright (C) 2014-2016 Dieter Adriaenssens <ruleant@users.sourceforge.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
