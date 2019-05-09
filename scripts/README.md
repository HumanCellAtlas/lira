## Subscription queries

The communication between the [HCA DCP Data Store Service](https://github.com/HumanCellAtlas/data-store) and Lira is 
relying on the subsciptions. This folder contains the necessary scripts to create/list/delete subscriptions in Data Store
Service for Lira:

- `DCPAuthClient.py`: handles the authentication with HCA DCP Data Store, requires Python 3.x to run.
- `subscribe.py`: is the core client script for working with subscriptions, requires Python 3.x to run.
- `v*_queries` and `jmespath_queries`: are the directories that host subscription queries.
- `subscription-*.sh`: are the helper scripts that help simplify working with subscriptions.
- `config-template.sh`: needs to be filled out if you want to use the helper scripts.


### Set-up

1. It is recommended to have a Python3 virtual environment set up so the dependencies won't get messed up. Usually you will need to do something like `virtualenv -p python3 ${NAME_YOUR_VIRTUAL_ENV}` and then `source path/to/${NAME_YOUR_VIRTUAL_ENV}/bin/activate`. For more information, check the official [docs](https://virtualenv.pypa.io/en/latest/userguide/#usage)

2. Install all of the dependencies with `pip install -r requirements.txt` from within this directory.

3. (optional) In order to leverage the helper shell scripts that make the process much easier, you will need to create a `config.sh` file, by filling out the `config-template.sh` that contains all of the required inputs, you should use real values and secrets at this step so **take care of this file and don't commit it!**. For convenience, you might want to have one `config-ENV.sh` files per environment.


### Work with the subscriptions

Once you finish the set-up steps, you can start to work with the subscriptions. The following examples will assume you are make subscriptions for the SmartSeq2 pipeline, but they should be generalized enough to be applied to any other pipelines.

#### Create a subscription

To create a new subscription, run:

```shell
bash subscription-create.sh config-dev.sh jmespath_queries/smartseq2.jmespath jmespath_queries/metadata_attachments.json
``` 

here we assume:
- `config-dev.sh` is the config file you created following the `config-template.sh` for your `dev` environment to subscribe to `dev` Data Store.
- `jmespath_queries/smartseq2.jmespath` is the query for Data Store to determine whether it should notify Lira when a new bundle is indexed on their side.
- `jmespath_queries/metadata_attachments.json` is a call-back based attachment file specifying all of the necessary meta fields for a bundle that Lira requires from Data Store to submit a workflow.

#### List all subscriptions

To list out all subscriptions for a given environment, run: 

```shell
bash subscriptions-get.sh config-dev.sh
```

#### Delete a subscription

To delete a subscription, run:

```shell
bash subscription-delete.sh config-dev.sh bfc5eeba-8a3d-4ce7-8905-4ae314f8e210
```
where the last variable is a valid subscription UUID that you got with `subscription-get.sh`.

#### Subscribe with ElasticSearch queries

The Data Store Service is going to deprecate supporting ElasticSearch soon in the future, so the helper scripts in this directory by default are using `jmespath` queries. You can still create ElasticSearch-query based subscriptions by going into the `subscription-*.sh` scripts and replace all of the `--subscription_type=jmespath` with `--subscription_type=elasticsearch`.

#### Use the Python client directly

It's worthy mentioning that you can always use the Python client `subscribe.py` directly to manipulate with the subscriptions, type `python subscribe.py -h` and `python subscribe.py create -h` to see the help messages.
