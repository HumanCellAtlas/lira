## Create a new kubernetes listener deployment

### Requirements:
1. Install and set-up [gcloud](https://cloud.google.com/sdk/)
2. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/): `gcloud components install kubectl`
3. Install and set-up the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html)
4. Install [jq](https://stedolan.github.io/jq/)

### Setup:
1. Create a new gcloud project for the deployment
2. Run the `listener-deployment-setup.sh` script to create subscriptions to the HCA data storage service and 
   generate a `config.json` file for a lira instance deployed by the Broad Institute mint team. The `config.json` file can
   be created manually following the `listener-config.json.ctmpl` template if a different configuration is required.
3. Obtain tls certificates and put them in the same directory as `config.json`. See[HumanCellAtlas/secondary-analysis/certs/README.md](https://github.com/HumanCellAtlas/secondary-analysis/blob/master/certs/README.md)
4. Run the `listener-deployment.sh` script to create a kubernetes deployment on Google Compute Engine.

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
