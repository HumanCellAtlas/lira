## Create a new kubernetes lira deployment

### Requirements:
1. Install and set-up [gcloud](https://cloud.google.com/sdk/)
2. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/): `gcloud components install kubectl`
3. Install and set-up the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html)
4. Install [jq](https://stedolan.github.io/jq/)

### Setup:
1. Create a new gcloud project for the deployment
2. Run the `lira-deployment-setup.sh` script to create subscriptions to the HCA data storage service and 
   generate a `config.json` file for a lira instance deployed by the Broad Institute mint team. The `config.json` file can
   be created manually following the `lira-config.json.ctmpl` template if a different configuration is required.
3. Obtain tls certificates and put them in the same directory as `config.json`. See[HumanCellAtlas/secondary-analysis/certs/README.md](https://github.com/HumanCellAtlas/secondary-analysis/blob/master/certs/README.md)
4. Run the `lira-deployment.sh` script to create a kubernetes deployment on Google Compute Engine.

## Update existing deployment

Switch to the correct environment:
1. Get cluster credentials: `gcloud container clusters --project [project] --zone [zone] get-credentials lira`
2. Find the context name for the environment you want: `kubectl config get-contexts`
3. Switch context: `kubectl config use-context [name]` where `name` is the context name, e.g. gke_broad-dsde-mint-dev_us-central1-b_lira. Or `kubectl config set-context [name]` if you haven't tried to use this particular context before. It's possible you will need to do `kubectl config delete-cluster [name]` to clear out stale local config with a wrong IP address for a cluster and then `gcloud container clusters get-credentials lira` to refresh the local config in ~/.kube/config.

Deploy new code:
1. Build docker image: `bash build_docker.sh [env] [tag]`
2. Push docker image to gcloud: `gcloud docker -- push <image_url>`
3. Update `lira-deployment.yaml` image with the pushed docker image
4. Set lira config secret `bash populate-lira-config-secret.sh`
5. Update deployment: `kubectl apply -f lira-deployment.yaml --record`

Deploy and use new tls secret:
To obtain a new certificate, see [HumanCellAtlas/secondary-analysis/certs/README.md](https://github.com/HumanCellAtlas/secondary-analysis/blob/master/certs/README.md).
Once you've obtained the new certificate, follow the instructions below.
1. `bash populate-tls-secret.sh hca-tls-secret /path/to/local/certs`. The script will append the date and time to the secret name you provide.
2. Edit lira-ingress.yaml to use new secret
3. `kubectl apply -f lira-ingress.yaml`.
4. In your browser, try navigating to https://pipelines.[env].data.humancellatlas.org/health and then checking the certificate expiry date (click on the lock in the address bar in Chrome). If the ingress doesn't start using the new certificate you might need to add or modify an annotation in the ingress yaml, then `kubectl apply -f lira-ingress.yaml` to force it to refresh. (This can be any annotation you like --it's sole purpose is to get GKE to notice that the yaml file has changed and requires updating the load balancer). You can do `kubectl describe ingress lira` to get detailed status.

Check the status of new deployment:
1. Get all pods: `kubectl get pods`
2. Check pod's logs: `kubectl describe pod ${pod_name}`
3. Check pod application’s logs: `kubectl logs ${pod_name}`
