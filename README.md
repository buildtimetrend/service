Buildtime Trend as a Service
============================

Visualise what's trending in your build process

[![Build Status](https://travis-ci.org/buildtimetrend/service.svg?branch=master)](https://travis-ci.org/buildtimetrend/service)
[![Code Health](https://landscape.io/github/buildtimetrend/service/master/landscape.svg)](https://landscape.io/github/buildtimetrend/service/master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/buildtimetrend/service/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/buildtimetrend/service/?branch=master)
[![Stack Share](http://img.shields.io/badge/tech-stack-0690fa.svg)](http://stackshare.io/ruleant/buildtime-trend)

This project contains the files that offer Buildtime Trend as a service. The [Buildtime Trend library](https://github.com/buildtimetrend/python-lib) powers this service.

Usage
-----

The service is available on Heroku : http://buildtimetrend-service.herokuapp.com/

- `/` : index page
- `/badge` : generates a shield badge
  - usage : `/badge/repo_owner/repo_name/badge_type/interval`
  - parameters :
    - `repo_owner` : name of the Github repo owner, fe. `buildtimetrend`
    - `repo_name` : name of the Github repo, fe. `service`
    - `badge_type` : type of badge, options :
      - `latest` : buildtime of last build job
      - `avg` : average buildtime of buildjobs in period set by `interval` (default)
      - `jobs` : number of build jobs in period set by `interval`
      - `builds` : number of builds in period set by `interval`
    - `interval` : time interval, options : `week` (default), `month`, `year` 
  - examples :
    - latest build duration : `/badge/buildtimetrend/service/latest` ![Latest build duration](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/latest)
    - average buildtime of last week : `/badge/buildtimetrend/service/avg/week` ![Average buildtime (week)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/avg/week)
    - average buildtime of last month : `/badge/buildtimetrend/service/avg/month` ![Average buildtime (month)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/avg/month)
    - average buildtime of last year : `/buildtimetrend/service/avg/year` ![Average buildtime (year)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/avg/year)
    - number of build jobs last week : `/badge/buildtimetrend/service/jobs/week` ![Build jobs (week)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/jobs/week)
    - number of build jobs last month : `/badge/buildtimetrend/service/jobs/month` ![Build jobs (month)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/jobs/month)
    - number of build jobs last year : `/buildtimetrend/service/jobs/year` ![Build jobs (year)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/jobs/year)
    - number of builds last week : `/badge/buildtimetrend/service/builds/week` ![Builds (week)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/builds/week)
    - number of builds last month : `/badge/buildtimetrend/service/builds/month` ![Builds (month)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/builds/month)
    - number of builds last year : `/buildtimetrend/service/builds/year` ![Builds (year)](https://buildtimetrend-service.herokuapp.com/badge/buildtimetrend/service/builds/year)

- `/travis` : loads a Travis CI build log file, processes it and sends the data to Keen.io
  - parameters :
    - `repo` : name of the Github repo, fe. `buildtimetrend/python-lib`
    - `build` : Travis CI build ID
    - `payload` : Travis CI notification payload, more info in the [Travis CI documentation](http://docs.travis-ci.com/user/notifications/#Webhook-notification)

To trigger the service at the end of a Travis CI build, add this to your `.travis.yml` file :

    notifications:
      webhooks:
        # trigger Buildtime Trend Service to parse Travis CI log and send result to Keen.io
        - http://buildtimetrend-service.herokuapp.com/travis

When Buildtime Trend Service is triggered by a Travis CI notification, it will get the necessary parameters (repo name and build number) from the `payload` that is passed by Travis CI. This will trigger loading and parsing the Travis CI log of the corresponding build, the analysed data is stored in the Keen.io database.

Config file
-----------

Add a configfile named `config_service.yml` based on `config_sample.yml` to configure the way the service behaves.

- `allowed_repo` : defines which repos are allowed by the service. If the `allowed_repo` setting is not defined, all repos are allowed. If substring matches the repo name, it is allowed, so fe. `my_name` will allow `my_name/my_first_repo` and `my_name/another_repo`. A complete repo name is allowed as well.
Multiple entries are allowed, fe. :

```
buildtimetrend:
  allowed_repo:
    - "my_name" # allowing all repo names that contain my_name
    - "another_name/some_repo" # allows this specific repo
```

- `travis_account_token` : define to enable checking Travis CI notification Authorization header. More info on Travis CI Webhook Authorization and where to find the Account token : http://docs.travis-ci.com/user/notifications/#Authorization-for-Webhooks
Remark : the account token should be the one of the user who created the repo on Travis CI.

It can also be defined with the `TRAVIS_ACCOUNT_TOKEN` environment variable.

- `loglevel` : defines loglevel, possible values : `DEBUG`, `INFO`, `WARNING` (default), `ERROR`
It can also be defined with the `BTT_LOGLEVEL` environment variable.

Dependencies
------------

- `buildtimetrend` : [Buildtime Trend library](https://github.com/buildtimetrend/python-lib)
- `cherrypy` : [CherrPy](http://www.cherrypy.org/) A Minimalist Python Web Framework, making the API available as a web service

Bugs and feature requests
-------------------------

Please report bugs and add feature requests in the Github [issue tracker](https://github.com/buildtimetrend/python-lib/issues).


Credits
-------

For an overview of who contributed to create Buildtime trend, see [Credits](https://github.com/buildtimetrend/python-lib/wiki/Credits).

Contact
-------

Website : http://buildtimetrend.github.io/python-client

Follow us on [Twitter](https://twitter.com/buildtime_trend), [Github](https://github.com/ruleant/buildtime-trend) and [OpenHub](https://www.openhub.net/p/buildtime-trend).


License
-------

Copyright (C) 2014 Dieter Adriaenssens <ruleant@users.sourceforge.net>

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
