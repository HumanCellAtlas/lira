# secondary-analysis

[![](https://img.shields.io/badge/slack-%23secondary--analysis-5BBC66.svg)](https://humancellatlas.slack.com/messages/secondary-analysis/)

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

### Testing notifications locally
To send a test notification to the listener:  
1. Set the auth token: `auth=notification_token`  
2. Send the notification: `curl -X POST -H "Content-type: application/json" "http://localhost:8080/notifications?auth=${notification_token}" -d @test/notification.json`

**Note:** The `subscription_id` in `notification.json` determines which workflow will be launched to process the data contained in the bundle.

To see information about the workflow that was launched by the test notification:
- Status: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/status
- Metadata: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/metadata
- Timing: https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1/<workflow_id>/timing 
