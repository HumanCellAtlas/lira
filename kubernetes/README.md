## Create a new kubernetes listener deployment

### Requirements:
- Install [gcloud](https://cloud.google.com/sdk/)
- Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/): `gcloud components install kubectl`

### Setup:
1. Create gcloud project for the new deployment (Each deployment corresponds to a separate gcloud project. e.g. the staging deployment uses `broad-dsde-mint-staging`)
2. Create listener cluster `gcloud container clusters create listener`
3. Create the directory /etc/secondary-analysis locally and add `config.json` and `bucket-reader-key.json`
4. Upload the wdl, zip and json files needed by the listener to a bucket in the new project and edit `config.json` to refer to those paths
5. Set listener config secret `bash populate-listener-config-secret.sh`
6. Add `fullchain.pem` and `privkey.pem` to /etc/secondary-analysis/
7. Set tls secret: `bash populate-tls-secret.sh`
8. Build docker image: `bash build_docker.sh [env] [tag]` where `env` is the environment to deploy to and `tag` is a tag for the docker image
9. Push docker image to gcloud: `gcloud docker -- push <image_url>`
10. Update `listener-deployment.yaml` image with the pushed docker image
11. Create deployment: `kubectl create -f listener-deployment.yaml --record --save-config`
12. Create service: `kubectl create -f listener-service.yaml --record --save-config`
13. Create ingress: `kubectl create -f listener-ingress.yaml --record --save-config`
14. Create static ip address: `gcloud compute addresses create listener --global`
15. In the Google Cloud Platform console, go to the Network Services/Cloud DNS page and add an "A" record named "listener101.mint-[env].broadinstitute.org" that points to the static ip address
16. In AWS, go to route53, click on hosted zones, then data.humancellatlas.org. Add or modify a CNAME record named
    pipelines.[env].data.humancellatlas.org and set the value to listener101.mint-[env].broadinstitute.org.
    For prod this should be pipelines.data.humancellatlas.org.

## Update existing deployment

Switch to the correct environment:  
1. Get cluster credentials: `gcloud container clusters --[project] [env] get-credentials listener`
2. Find the context name for the environment you want: `kubectl config get-contexts`
3. Set the context: `kubectl config set-context [name]` where `name` is the context name, e.g. gke_broad-dsde-mint-dev_us-central1-b_listener

Deploy new code:
1. Build docker image: `bash build_docker.sh [env] [tag]`
2. Push docker image to gcloud: `gcloud docker -- push <image_url>`
3. Update `listener-deployment.yaml` image with the pushed docker image
4. Set listener config secret `bash populate-listener-config-secret.sh`
5. Update deployment: `kubectl apply -f listener-deployment.yaml --record`
