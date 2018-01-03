# secondary-analysis

| Slack Channel | Container | Linux-Python2.7 |
|:-------:|:---------:|:---------:|
| [![](https://img.shields.io/badge/slack-%23secondary--analysis-5BBC66.svg)](https://humancellatlas.slack.com/messages/secondary-analysis/) | [![Docker Repository on Quay](https://quay.io/repository/humancellatlas/secondary-analysis-lira/status "Docker Repository on Quay")](https://quay.io/repository/humancellatlas/secondary-analysis-lira) | [![Build Status](https://travis-ci.org/HumanCellAtlas/lira.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/lira) |

Prototype Secondary Analysis Service (Green Box) for the Human Cell Atlas. 

Whenever a bundle is uploaded to the storage service (Blue Box), if it matches a query registered with the listener it will send a notification to the listener's `/notifications` endpoint. 
When the listener receives a notification, it processes data in that bundle using the workflow defined in `config.json` that has a matching `subscription_id`. 
Currently, the listener launches either a smartseq2 or 10x count workflow to produce a bam and gene expression table. The analysis outputs are then uploaded to the storage service.

[Design specs and prototypes for secondary analyses ("green box")](https://docs.google.com/document/d/1_VgySxINPbUsI0w-Gr4fV4DrHRSwdbCMf7b5sCB18uQ/edit?usp=sharing)

### Installation and Setup for Local Development
1. [Install Docker](https://docs.docker.com/engine/installation/#supported-platforms)
2. Git clone this repository
3. Add `config.json` (contains wdl configs and cromwell credentials) and `bucket-reader-key.json` (contains google cloud storage keys) to `/private/etc/secondary-analysis/`
4. Build the docker container: `bash build_docker.sh dev test`
5. Run the docker container: `bash run_docker.sh dev test`

### Run unit tests
There are two ways to do this, with and without Docker.

To run unit tests without building the docker image, you should create a virtual environment with the requirements for Lira:

```
virtualenv test-env
source test-env/bin/activate
pip install -r requirements.txt
```

Then, from the root of the lira repo, do:
```
python -m unittest discover -v
```
This will run all of Lira's unit tests.

You can also run the unit tests from inside the docker image, if you don't want to create a virtualenv.
You can do this by running:
```
cd lira/test
bash test.sh
```

### Testing notifications locally
To send a test notification to the listener:  
1. Set the auth token: `auth=notification_token`  
2. Send the notification: `curl -X POST -H "Content-type: application/json" "http://localhost:8080/notifications?auth=${notification_token}" -d @lira/test/notification.json`

**Note:** The `subscription_id` in `notification.json` determines which workflow will be launched to process the data contained in the bundle.

To see information about the workflow that was launched by the test notification:
- Status: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/status
- Metadata: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/metadata
- Timing: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/timing 
