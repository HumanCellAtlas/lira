import connexion
import json
import logging
import io
import base64
import cromwell_tools.cromwell_api
import cromwell_tools.cromwell_auth
import cromwell_tools.utilities
from flask import current_app
from lira import lira_utils, bundle_inputs
from google.cloud import pubsub_v1


logger = logging.getLogger("{module_path}".format(module_path=__name__))


def post(body):
    """Receive notifications from the HCA Data Storage Service and add to a Google pub/sub topic."""
    # Check authentication
    lira_config = current_app.config
    if not lira_utils.is_authenticated(connexion.request, lira_config):
        raise connexion.ProblemException(
            status=401,
            title='Unauthorized',
            detail='Authentication failed',
            headers=lira_utils.LIRA_SERVER_HEADER,
        )

    logger.info("Notification received")
    logger.info(f"Received notification body: {body}")

    project_id = lira_config.google_project
    topic_name = lira_config.google_pubsub_topic
    publisher = pubsub_v1.PublisherClient.from_service_account_file(
        lira_config.caas_key
    )
    topic_path = publisher.topic_path(project_id, topic_name)
    message = json.dumps(body).encode("utf-8")
    future = publisher.publish(topic_path, message, origin=f"lira-{lira_config.env}")
    message_id = future.result(
        timeout=60
    )  # Wait 60s for a value to be returned, otherwise raise a timeout error
    logger.info(f"Message {message_id} added to topic {topic_name}")
    return lira_utils.response_with_server_header({"id": message_id}, 200)


def receive_messages(body):
    """Receive messages from Google pub/sub topic."""
    if not lira_utils._is_authenticated_pubsub(connexion.request):
        raise connexion.ProblemException(
            status=401,
            title='Unauthorized',
            detail='Authentication failed',
            headers=lira_utils.LIRA_SERVER_HEADER,
        )
    message = body["message"]
    logger.info(f"Received message from Google pub/sub: {message}")
    response = submit_workflow(message)
    return response


def submit_workflow(message):
    """ Process messages and submit on-hold workflow in Cromwell."""
    lira_config = current_app.config
    data = base64.b64decode(message['data'])
    body = json.loads(data)
    uuid, version, subscription_id = lira_utils.extract_uuid_version_subscription_id(
        body
    )

    # Find wdl config where the subscription_id matches the notification's subscription_id
    id_matches = [
        wdl for wdl in lira_config.wdls if wdl.subscription_id == subscription_id
    ]
    if len(id_matches) == 0:
        # Not raising an exception here because it will trigger another notification
        # and resending the message will not resolve this issue
        logger.error(f"No wdl config found for subscription {subscription_id}")
        return lira_utils.response_with_server_header({}, 200)

    wdl_config = id_matches[0]
    logger.info(f"Matched WDL config: {wdl_config}")
    logger.info(f"Preparing to launch {wdl_config.workflow_name} workflow in Cromwell")

    # Prepare inputs
    inputs = lira_utils.compose_inputs(
        wdl_config.workflow_name, uuid, version, lira_config
    )
    cromwell_inputs = json.dumps(inputs).encode('utf-8')

    # Prepare labels
    labels_from_notification = body.get(
        'labels'
    )  # Try to get the extra labels field if it's applicable
    attachments_from_notification = body.get(
        'attachments'
    )  # Try to get the extra attachments field if it's applicable

    try:
        workflow_hash_label = bundle_inputs.get_workflow_inputs_to_hash(
            wdl_config.workflow_name, uuid, version, lira_config.dss_url
        )
    except Exception as ex:
        if ex.code == 404:
            # Not raising an exception here because it will trigger another notification
            # and resending the message will not resolve this issue
            logger.error(f"Could not find bundle {uuid}.{version}")
            return lira_utils.response_with_server_header({}, 200)

    message_id_label = {'pubsub-message-id': message['message_id']}
    cromwell_labels = lira_utils.compose_labels(
        wdl_config.workflow_name,
        wdl_config.workflow_version,
        uuid,
        version,
        labels_from_notification,
        attachments_from_notification,
        workflow_hash_label,
        message_id_label
    )
    cromwell_labels_file = json.dumps(cromwell_labels).encode('utf-8')

    logger.debug(f"Added labels {cromwell_labels_file} to workflow")

    cromwell_submission = current_app.prepare_submission(
        wdl_config, lira_config.submit_wdl
    )
    logger.info(current_app.prepare_submission.cache_info())

    dry_run = getattr(lira_config, 'dry_run', False)
    kwargs = {}

    if dry_run:
        logger.warning("Not launching workflow because Lira is in dry_run mode")
        response_json = {'id': 'fake_id', 'status': 'fake_status'}
        status_code = 201
    else:
        if lira_config.use_caas:
            options = lira_utils.compose_caas_options(
                cromwell_submission.options_file, lira_config
            )
            options_file = json.dumps(options).encode('utf-8')

            auth = cromwell_tools.cromwell_auth.CromwellAuth.harmonize_credentials(
                url=lira_config.cromwell_url, service_account_key=lira_config.caas_key
            )
            kwargs['collection_name'] = lira_config.collection_name
        else:
            options_file = cromwell_submission.options_file
            auth = cromwell_tools.cromwell_auth.CromwellAuth.harmonize_credentials(
                url=lira_config.cromwell_url,
                username=lira_config.cromwell_user,
                password=lira_config.cromwell_password,
            )
        options_file = lira_utils.compose_config_options(options_file, lira_config)

        cromwell_response = cromwell_tools.cromwell_api.CromwellAPI.submit(
            auth=auth,
            wdl_file=io.BytesIO(cromwell_submission.wdl_file),
            inputs_files=[
                io.BytesIO(cromwell_inputs),
                io.BytesIO(cromwell_submission.wdl_static_inputs_file),
            ],
            options_file=io.BytesIO(options_file),
            dependencies=cromwell_tools.utilities.make_zip_in_memory(
                cromwell_submission.wdl_deps_dict
            ),
            label_file=io.BytesIO(cromwell_labels_file),
            on_hold=lira_config.submit_and_hold,
            validate_labels=False,  # switch off the validators provided by cromwell_tools
            **kwargs,
        )

        if cromwell_response.status_code > 201:
            logger.error(f"HTTP error content: {cromwell_response.text}")
            raise connexion.ProblemException(
                status=500,
                title="Internal Server Error",
                detail=f"Cromwell returned: {cromwell_response.text}",
                headers=lira_utils.LIRA_SERVER_HEADER,
            )
        else:
            response_json = cromwell_response.json()
            logger.info(
                f"Cromwell response: {response_json} {cromwell_response.status_code}"
            )
            status_code = 201
    return lira_utils.response_with_server_header(response_json, status_code)
