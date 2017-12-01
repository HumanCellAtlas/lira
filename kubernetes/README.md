## Create a new kubernetes listener deployment

### Requirements:
1. Install [gcloud](https://cloud.google.com/sdk/)
2. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/): `gcloud components install kubectl`
3. `gcloud auth login`
4. `gcloud config set project [project]`

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
1. Get cluster credentials: `gcloud container clusters --project [project] --zone [zone] get-credentials listener`
2. Find the context name for the environment you want: `kubectl config get-contexts`
3. Set the context: `kubectl config set-context [name]` where `name` is the context name, e.g. gke_broad-dsde-mint-dev_us-central1-b_listener

Deploy new code:
1. Build docker image: `bash build_docker.sh [env] [tag]`
2. Push docker image to gcloud: `gcloud docker -- push <image_url>`
3. Update `listener-deployment.yaml` image with the pushed docker image
4. Set listener config secret `bash populate-listener-config-secret.sh`
5. Update deployment: `kubectl apply -f listener-deployment.yaml --record`

Deploy and use new tls secret:
To obtain a new certificate, see [HumanCellAtlas/secondary-analysis/certs/README.md](https://github.com/HumanCellAtlas/secondary-analysis/blob/master/certs/README.md).
Once you've obtained the new certificate, follow the instructions below.
1. `bash populate-tls-secret.sh hca-tls-secret-yyyy-mm-dd /path/to/local/certs`
2. Edit listener-ingress.yaml to use new secret
3. `kubectl apply -f listener-ingress.yaml`
4. Test: `curl https://pipelines.[env].data.humancellatlas.org` and `kubectl describe ingress listener` for detailed status. Expect to get 502 errors for ~15 minutes while things update.

Check the status of new deployment:
1. Get all pods: `kubectl get pods`
2. Check pod's logs: `kubectl describe pod ${pod_name}`
3. Check pod application’s logs: `kubectl logs ${pod_name}`
