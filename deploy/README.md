# Kubernetes Deployment
Upgrading is featured first as this will be the more common action required in this setup

## Installing or Upgrading
Generally the only file which will need to be modified when updating a deployment will be the
config.sh.ctmpl. The section which is envisioned to change most often will be the environment 
variables located towards the top of this file. 

### Lira Deployments (deploy_lira.sh)
This script does the following:
01. Generates the Kubernetes service yaml
02. Deploys the Kubernetes service to the cluster
03. Generates a TLS cert keys (private, chain, cert and fullchain)
04. Adds the TLS cert keys to Vault
05. Renders the TLS cert files
06. Adds the rendered TLS cert to the Kubernetes configuration secret for the cluster
07. Renders the lira-ingress.yaml file
08. Deploys the rendered ingress file to the Kubernetes cluster 
09. Retrieving caas service account key from vault
10. Renders the Lira config file
11. Deploys the lira config file with the caas key to the Kubernetes cluster
12. Generates the lira deployment file
13. Deploys the lira-deployment.yaml file to the Kubernetes cluster


## New Deployments
In addition to the above scripts there are several other items which need to be set up to deploy lira for the first time:

### Create Service Accounts
This script does the following:
1. Sets the GCloud project to use
2. Creates the Service Account
3. Grants the service account the necessary permissions
4. Creates keys for the service account
5. Adds the service account key to Vault
6. Registers the service account in Firecloud
7. Registers the service account in SAM

### Create Logging Sink
This script does the following:
1. Creates the log sink

### Create Subscriptions
This script does the following:
1. Create bluebox service account & key
2. Add service account key to vault
3. Gets the lira secret from vault
4. Creates ss2 subscription
5. Creates 10x subscription

## Other useful scripts
### get_bearer_token.sh
This script returns the bearer token for a service account given the environment and the caas environment that you 
will be connecting to.