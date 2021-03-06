# Lira

[![Travis (.org) branch](https://img.shields.io/travis/HumanCellAtlas/lira/master.svg?label=Unit%20Test%20on%20Travis%20CI%20&style=flat-square&logo=Travis)](https://travis-ci.org/HumanCellAtlas/lira)
[![Docker Repository on Quay](https://quay.io/repository/humancellatlas/secondary-analysis-lira/status "Docker Repository on Quay")](https://quay.io/repository/humancellatlas/secondary-analysis-lira)
[![GitHub release](https://img.shields.io/github/release/HumanCellAtlas/lira.svg?label=Latest%20Release&style=flat-square&colorB=green)](https://github.com/HumanCellAtlas/lira/releases)
[![Snyk Vulnerabilities for GitHub Repo (Specific Manifest)](https://img.shields.io/snyk/vulnerabilities/github/HumanCellAtlas/lira/requirements.txt.svg?label=Snyk%20Vulnerabilities&logo=Snyk&style=flat-square)](https://snyk.io/test/github/HumanCellAtlas/lira?targetFile=requirements.txt)

![Github](https://img.shields.io/badge/python-2.7%20%7C%203.6-green.svg?style=flat-square&logo=python&colorB=blue)
![GitHub](https://img.shields.io/github/license/HumanCellAtlas/lira.svg?style=flat-square&colorB=blue)
[![Code style: black](https://img.shields.io/badge/Code%20Style-black-000000.svg?style=flat-square)](https://github.com/ambv/black)
[![Github](https://img.shields.io/badge/Slack%20Channel-%23hca--dcp--analysis--community-green.svg?style=flat-square&colorB=blue)](https://humancellatlas.slack.com/messages/analysis-community/)

Lira submits workflows to
[Cromwell](https://github.com/broadinstitute/cromwell)
in response to notifications.

Notifications contain a bundle id and version
to identify a data bundle
in the [Data Storage System](https://github.com/HumanCellAtlas/data-store).
Notifications also contain a subscription id.

When Lira receives a notification
at its `/notifications` endpoint,
it uses the subscription id
to determine what type of workflow to submit,
and uses the bundle id and version
as inputs to that workflow.

[Design specs for the Secondary Analysis Service ("Green Box")](https://docs.google.com/document/d/1_VgySxINPbUsI0w-Gr4fV4DrHRSwdbCMf7b5sCB18uQ/edit?usp=sharing)

## Development

### Code Style

The Lira code base is complying with the PEP-8
and using [Black](https://github.com/ambv/black)
to format our code,
in order to avoid "nitpicky" comments
during the code review process
so we spend more time discussing about the logic,
not code styles.

In order to enable the auto-formatting
in the development process,
you have to spend a few seconds setting up the `pre-commit`
the first time you clone the repo.
It's highly recommended that you install the packages
within a [`virtualenv`](https://virtualenv.pypa.io/en/latest/userguide/).

1. Install `pre-commit` by running:
   `pip install pre-commit`
   (or simply run `pip install -r requirements.txt`).
2. Run `pre-commit install` to install the git hook.

Once you successfully install the `pre-commit` hook to this repo,
the Black linter/formatter will be automatically triggered
and run on this repo.
Please make sure you followed the above steps,
otherwise your commits might fail at the linting test!

_If you really want to manually trigger
the linters and formatters on your code,
make sure `Black` and `flake8` are installed
in your Python environment and run `flake8 DIR1 DIR2`
and `black DIR1 DIR2 --skip-string-normalization` respectively._

### Building and running

You can run Lira in docker or a Python virtual environment.

#### Using docker

1. [Install Docker](https://docs.docker.com/engine/installation/#supported-platforms)

2. Git clone this repository

3. Create a `config.json` file
   (contains wdl configs and cromwell credentials).
   See an example at lira/test/data/config.json.

4. Build the docker container: `bash build_docker.sh test`

5. Run the docker container as shown below.

   ``` shell
   bash run_docker.sh test /absolute/path/to/config.json
   ```

Shut `lira` down by running `docker stop lira`
from another shell session.

#### Virtual environment

To run without docker, create a virtual environment.

If you don't have pip installed,
[install it first](https://pip.pypa.io/en/stable/installing/).

Run this to export the `lira_config` environment variable.

``` shell
export lira_config=/absolute/path/to/config.json
```

If `config.json` has `"use_caas" : true,`
then also run this
to export a `caas_key` into the environment.

``` shell
export caas_key=/absolute/path/to/caas_key.json
```

where `caas_key.json` contains the service account key
for the CAAS Cromwell instance.
Remember to remove the file when finished with it.

Then install virtualenv with `pip install virtualenv`.

Use `deactivate` to exit from a virtual environment.
If that doesn't work, try `Ctrl+C` first
and then `deactivate`.

Create a virtual environment for running Lira:

``` shell
virtualenv test-env
source test-env/bin/activate
pip install -r requirements.txt
```

There are two ways to run Lira in a virtual environment.

##### gunicorn

For production use, start Lira with:

``` shell
bash start_lira.sh [PORT]
```

which defaults to port 8080 if port is not provided.
This will run Lira in gunicorn,
a production-grade server.

However,
you may want to put Lira behind a proxy like nginx
or behind a load balancer.
This can mitigate problems with slow clients
that can cause availability issues
when gunicorn is run on its own.

#### Flask development server

If you would like to run Lira using the Flask development server,
perhaps to help debug issues,
you can do so with:

``` shell
python -m lira.lira
```

Note that the Flask development server does not scale well
and has security vulnerabilities
that make it unsuitable for production use.

#### Shutting down

You can stop Lira and exit the virtual environment by:

``` shell
Ctrl+C
deactivate
```

### Run unit tests

There are two ways to do this,
with Docker or with Virtualenv.

#### Docker

You can run the unit tests using the docker image by running:

``` shell
cd lira/test
bash test.sh
```

#### Virtualenv
To run unit tests without building the docker image,
you should create a virtual environment
as described in the "Building and running" section.

Then, from the root of the lira repo, do:

``` shell
python -m unittest discover -v
```

### Testing notifications locally

To send a test notification to Lira:

1. Set the auth token: `auth=notification_token`
2. Send the notification:
   `curl -X POST -H "Content-type: application/json" "http://localhost:8080/notifications?auth=${notification_token}" -d @lira/test/notification.json`

**Note:**
The `subscription_id` in `notification.json`
determines which workflow will be launched
to process the data contained in the bundle.

To see information about the workflow
that was launched by the test notification:

- Status: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/status
- Metadata: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/metadata
- Timing: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/timing

## Deployment

The [secondary-analysis-deploy](https://github.com/HumanCellAtlas/secondary-analysis-deploy) repository contains scripts to deploy this service via Jenkins and GitLab to a GKE cluster.
