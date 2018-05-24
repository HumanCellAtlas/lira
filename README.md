# Lira
foo
| Slack Channel | Container | Linux-Python2.7 |
|:-------:|:---------:|:---------:|
| [![](https://img.shields.io/badge/slack-%23secondary--analysis-5BBC66.svg)](https://humancellatlas.slack.com/messages/secondary-analysis/) | [![Docker Repository on Quay](https://quay.io/repository/humancellatlas/secondary-analysis-lira/status "Docker Repository on Quay")](https://quay.io/repository/humancellatlas/secondary-analysis-lira) | [![Build Status](https://travis-ci.org/HumanCellAtlas/lira.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/lira) |

Submits workflows to [Cromwell](https://github.com/broadinstitute/cromwell) in response to notifications.

Notifications contain a bundle id and version to identify a data bundle in the [Data Storage System](https://github.com/HumanCellAtlas/data-store). Notifications also contain a subscription id.

When Lira receives a notification at its `/notifications` endpoint, it uses the subscription id to determine what type of workflow to submit, and uses the bundle id and version as inputs to that workflow.

[Design specs for the Secondary Analysis Service ("Green Box")](https://docs.google.com/document/d/1_VgySxINPbUsI0w-Gr4fV4DrHRSwdbCMf7b5sCB18uQ/edit?usp=sharing)

## Building and running

You can run Lira in docker or a Python virtual environment.

### Using docker
1. [Install Docker](https://docs.docker.com/engine/installation/#supported-platforms)
2. Git clone this repository
3. Create a `config.json` file (contains wdl configs and cromwell credentials). See an example at lira/test/data/config.json.
4. Build the docker container: `bash build_docker.sh test`
5. Run the docker container: `bash run_docker.sh test /path/to/config.json [PORT]`

### Virtual environment
To run without docker, create a virtual environment.

If you don't have pip installed, [install it first](https://pip.pypa.io/en/stable/installing/).

Then install virtualenv with `pip install virtualenv`.

Create a virtual environment for running Lira:
```
virtualenv test-env
source test-env/bin/activate
pip install -r requirements.txt
```

There are two ways to run Lira in a virtual environment.

#### gunicorn
For production use, start Lira with:
```
bash start_lira.sh [PORT]
```
which defaults to port 8080 if port is not provided.
This will run Lira in gunicorn, a production-grade server.

However, you may want to put Lira behind a proxy like nginx or behind a load balancer.
This can mitigate problems with slow clients that can cause availability issues
when gunicorn is run on its own.

### Flask development server
If you would like to run Lira using the Flask development server, perhaps to help debug issues,
you can do so with:
```
python -m lira.lira
```

Note that the Flask development server does not scale well and has security vulnerabilities
that make it unsuitable for production use.

### Shutting down

You can stop Lira and exit the virtual environment by:
```
Ctrl+C
deactivate
```

## Run unit tests
There are two ways to do this, with and without Docker.

### Docker
You can run the unit tests using the docker image by running:
```
cd lira/test
bash test.sh
```

### Virtualenv
To run unit tests without building the docker image, you should create a virtual environment as described in the "Building and running" section.

Then, from the root of the lira repo, do:
```
python -m unittest discover -v
```

## Testing notifications locally
To send a test notification to Lira:  
1. Set the auth token: `auth=notification_token`  
2. Send the notification: `curl -X POST -H "Content-type: application/json" "http://localhost:8080/notifications?auth=${notification_token}" -d @lira/test/notification.json`

**Note:** The `subscription_id` in `notification.json` determines which workflow will be launched to process the data contained in the bundle.

To see information about the workflow that was launched by the test notification:
- Status: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/status
- Metadata: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/metadata
- Timing: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/timing 
