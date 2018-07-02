### Set-up

1. Install requirements to run the scripts with `pip install -r requirements.txt`
2. Create a `scripts/config.sh` file that contains all of the inputs defined in `scripts/config-template.sh`
   and replace the placeholder values with real values

### Creating a subscription
To create a subscription, run `bash subscription-create.sh v3_queries/smartseq2-query.json` and pass in the path to the file containing the query to register.

### Viewing list of subscriptions
To list out all subscriptions, run `bash subscription-list.sh`

### Deleting a subscription
To delete a subscription, run `bash subscription-delete.sh uuid` and pass in the uuid of the subscription.
