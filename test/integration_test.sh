#!/usr/bin/env bash

# This script carries out the following steps:
# 1. Clone Lira if needed
# 2. Get pipeline-tools version
# 3. Build or pull Lira image
# 4. Get pipeline versions
# 5. Render config.json
# 6. Start Lira
# 7. Send in notification
# 8. Poll Cromwell for completion
# 9. Stop Lira

# This script currently only works when run locally on a developer's machine,
# but is designed to be easy to adapt to running on a Jenkins or Travis VM.
#
# In addition to the parameters specified below, this script expects the following
# files to be available:
# -configtemplate.json, template for Lira config, will be rendered by this script
# -${env}_config.json: environment config json file (contains environment-specific Lira config)
# -${env}_secrets.json file (contains secrets for Lira)
# 
# The following parameters are required. 
# Versions can be a branch name, tag, or commit hash
#
# env
# The environment to use -- affects Cromwell url, buckets, Lira config.
# When running from a PR, this will always be int. When running locally,
# the developer can choose dev or int.
#
# mint_deployment_dir
# Local directory where deployment TSVs can be found. Later, we'll
# create a repo for this, and this script will be modified to look there.
#
# lira_mode and lira_version
# The lira_mode param can be "local", "image" or "github".
# If "local" is specified, a local copy of the Lira code is used and
# lira_version is ignored. If "image" is specified, this script will pull and run
# a particular version of the Lira docker image specified by lira_version.
# TODO: Modify so that if lira_mode == "image" and lira_version == "deployed",
# then the script will use the currently deployed image in env.
# Running in "github" mode is not fully implemented yet, but is intended to clone
# the Lira repo and check out a specific branch, tag, or commit to use, specified
# by lira_version.
#
# pipeline_tools_mode and pipeline_tools_version
# Currently, pipeline_tools_mode is ignored and pipeline_tools_version is extracted
# from the deployment TSV.
# TODO: Modify so that if mode is "local", then a local copy of the repo is used,
# with the path to the repo specified in pipeline_tools_version.
# TODO: Modify so that if mode is "github", then the script configures Lira to read the
# wrapper WDLS from GitHub and use version pipeline_tools_version. Also, if lira_mode
# is "local", then it will get built using that pipeline_tools_version. If pipeline_tools_version
# is "current", then the deployment TSV is consulted to find and use the currently deployed
# version of the wrapper WDLs.
#
# tenx_mode and tenx_version
# Mode is required to be "current" right now and tenx_version is ignored.
# The script will check the deployment TSV to find the currently deployed version of
# the 10x pipeline.
#
# ss2_mode and ss2_version
# Mode is required to be "current" right now and ss2_version is ignored.
# The script will check the deployment TSV to find the currently deployed version of
# the Smart-seq2 pipeline.

set -e

env=$1
mint_deployment_dir=$2
lira_mode=$3
lira_version=$4
pipeline_tools_mode=$5
pipeline_tools_version=$6
tenx_mode=$7
tenx_version=$8
ss2_mode=$9
ss2_version=${10}

work_dir=$(pwd)
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 1. Clone Lira if needed 
# TODO: Create a repo for integration_test.sh to go in, so that we
# can run in github mode. Currently we have to run in lira local mode.
lira_dir=$script_dir/../

# 2. Get pipeline-tools version
# TODO: Uncomment condition below once we have Lira reading wrapper WDLs from pipeline-tools repo
#if [ $pipeline_tools_mode == "github" ] && [ $pipeline_tools_version == "current" ]; then
  pipeline_tools_version=$(python $script_dir/current_deployed_pipeline_version.py \
                    --mint_deployment_dir $mint_deployment_dir \
                    --env $env \
                    --pipeline_name pipeline_tools)
  echo "pipeline_tools_version: $pipeline_tools_version"
#fi

# 3. Build or pull Lira image
if [ $lira_mode == "image" ]; then
  if [ $lira_version == "latest" ]; then
    lira_image_version=$(python $script_dir/get_latest_release.py HumanCellAtlas/secondary-analysis)
  else
    lira_image_version=$lira_version
  fi
  docker pull humancellatlas/secondary-analysis:$lira_image_version
elif [ $lira_mode == "local" ] || [ $lira_mode == "github" ]; then
  lira_image_version=$lira_version
  echo "Building Lira version: $lira_image_version"
  cd $lira_dir
  docker build -t humancellatlas/secondary-analysis:$lira_image_version .
  cd -
fi

# 4. Get deployed pipeline versions to use
# (TODO: Create mint-deployment repo and use it here)
if [ $tenx_mode == "current" ]; then
  tenx_version=$(python $script_dir/current_deployed_pipeline_version.py \
                    --mint_deployment_dir $mint_deployment_dir \
                    --env $env \
                    --pipeline_name 10x)
  echo "10x version: $tenx_version"
else
  "Only tenx_mode==current is supported"
fi
if [ $ss2_mode == "current" ]; then
  ss2_version=$(python $script_dir/current_deployed_pipeline_version.py \
                    --mint_deployment_dir $mint_deployment_dir \
                    --env $env \
                    --pipeline_name ss2)
  echo "ss2 version: $ss2_version"
else
  "Only ss2_mode==current is supported"
fi

# 5. Render config.json
# (TODO: Use Henry's script here)
# TODO: use config file from config repo
# dev_secrets.json will come from Vault eventually
echo "Rendering Lira config"
python $script_dir/render_lira_config.py \
    --template_file configtemplate.json \
    --env_config_file ${env}_config.json \
    --secrets_file ${env}_secrets.json \
    --10x_version $tenx_version \
    --ss2_version $ss2_version \
    --pipeline_tools_version $pipeline_tools_version > config.json

# 6. Start Lira
echo "Starting Lira docker image"
lira_image_id=$(docker run \
                -p 8080:8080 \
                -d \
                -e listener_config=/etc/secondary-analysis/config.json \
                -e GOOGLE_APPLICATION_CREDENTIALS=/etc/secondary-analysis/bucket-reader-key.json \
                -v $work_dir:/etc/secondary-analysis \
                humancellatlas/secondary-analysis:$lira_image_version)

# 7. Send in notifications
# TODO: Check in notifications to repo where integration_test.sh will live so they are accessible outside Lira repo
echo "Sending in notifications"
virtualenv integration-test-env
source integration-test-env/bin/activate
pip install requests
tenx_workflow_id=$(python $script_dir/send_notification.py \
                  --lira_url "http://localhost:8080/notifications" \
                  --secrets_file ${env}_secrets.json \
                  --notification $lira_dir/test/10x_notification_${env}.json)
ss2_workflow_id=$(python $script_dir/send_notification.py \
                  --lira_url "http://localhost:8080/notifications" \
                  --secrets_file ${env}_secrets.json \
                  --notification $lira_dir/test/ss2_notification_${env}.json)
echo "tenx_workflow_id: $tenx_workflow_id"
echo "ss2_workflow_id: $ss2_workflow_id"

# 8. Poll for completion
echo "Awaiting workflow completion"
python $script_dir/await_workflow_completion.py \
  --workflow_ids $ss2_workflow_id,$tenx_workflow_id \
  --workflow_names ss2,10x \
  --cromwell_url https://cromwell.mint-$env.broadinstitute.org \
  --secrets_file ${env}_secrets.json \
  --timeout_minutes 20

# 9. Stop listener
echo "Stopping Lira"
docker stop $lira_image_id
