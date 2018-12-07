#!/usr/bin/env bash

set -e

program_name=`basename $0`

# set defaults

# flag to determine if we keep ctmpls around after render
KEEP_CTMPL_FILES_FLAG=0
WORK_DIR=${WORK_DIR:-"/working"}

# log level
LOG_LEVEL=${LOG_LEVEL-"err"}

# consul config values
CONSUL_TEMPLATE_PATH="/usr/local/bin"
CONSUL_CONFIG="/etc/consul-template/config/config.json"

usage() {
    echo "${program_name} [-k] [-v VAULT_TOKEN] [-l LOG_LEVEL] [-w working_directory] file(s)"
}

error_out() {
    if [ $1 -ne 0 ]; then
        echo
        echo "${2}"
        exit $1
    fi
}

# Process options
#  -e ENVIRONMENT
#  -k keep files
#  -v VAULT_TOKEN
#  -p VAULT_TOKEN_PATH
#  -l LOG_LEVEL
#  -w working directory
while getopts :kl:v:w:p: FLAG; do
   case ${FLAG} in
        v)  VAULT_TOKEN="${OPTARG}"
            ;;
        p)  VAULT_TOKEN_PATH="${OPTARG}"
            ;;
        l)  LOG_LEVEL="${OPTARG}"
            ;;
        k)  KEEP_CTMPL_FILES_FLAG=1
            ;;
        w)  WORK_DIR="$OPTARG"
            ;;
   esac
done

# Get the vault token
get_vault_token(){
    echo "Getting Vault Token..."

    # Check if the vault token is not set or is an empty string.
    if [ -z "${VAULT_TOKEN}" ]; then

        # If the vault token is not set, check to see if it is in a file
        if [ -r "${VAULT_TOKEN_PATH}" ]; then
            VAULT_TOKEN="$(cat ${VAULT_TOKEN_PATH})"

        # If the vault token is not set and there is no vault token file, then exit
        else
            echo "No vault token found - Exiting..."
            exit 1
        fi
    fi
}

# Do a vault lookup and exit if token is invalid
verify_vault_token() {
    echo "Verifying vault token..."

    if ! (VAULT_TOKEN=${VAULT_TOKEN} && vault token-lookup >/dev/null 2>&1)
    then
        echo "Invalid token provided - Exiting..."
        exit 1
    fi

    export VAULT_TOKEN="${VAULT_TOKEN}"
}

clean_base64_file() {
    echo "Cleaning Base 64 file..."

    output=$1

    # check if output ends in .b64 by looking at second extension
    extension2="${output##*.}"

    # Get final file name and clean file by removing \n
    if [ "${extension2}" == "b64" ]
    then
        final_file="${output%.*}"

        echo "Base64 decoding ${output} to ${final_file}"

        # clean any blank lines from the ctmpl
        tr -d '\n' < ${output} | base64 -d  > ${final_file}

        test "${KEEP_CTMPL_FILES_FLAG}" -eq 0 && rm -f ${output}
    fi
}

render_file() {
    echo "Rendering file..."

    # assume rest of args are files
    for file in ${FILES_TO_RENDER}
    do
        echo "Processing ${file}..."

        # check if it is a file
        if [ ! -r "${file}" ]
        then
            # skip non-regular files
            echo "ERROR: specified file is not a regular file: (${file}) - Exiting"
            exit 1
        fi

        # filename without .ctmpl
        output_file="${file%.ctmpl}"

        echo "Rendering ${file} to ${output_file} .."

        ${CONSUL_TEMPLATE_PATH}/consul-template \
            -once \
            -config=${CONSUL_CONFIG} \
            -log-level=${LOG_LEVEL} \
            -template=${file}:${output_file}
        error_out $? "FATAL ERROR: Unable to execute consul-template for ${file}!"

        clean_base64_file ${output_file}

        # clean up
        test "${KEEP_CTMPL_FILES_FLAG}" -eq 0 && rm -f ${file}

    done
}

do_files_require_vault_token() {
    file_needs_vault="false"

    # assume rest of args are files
    for file in ${FILES_TO_RENDER}
    do
        if [ ! -r "${file}" ]
        then
            echo "ERROR: specified file is not a regular file: (${file}) - Exiting"
            exit 1
        fi

        if $(grep -q "vault" "${file}"); then
            file_needs_vault="true"
            break
        fi

    done

    echo ${file_needs_vault}
}

shift $((OPTIND-1))

FILES_TO_RENDER=$*

echo "Checking Working Directory..."
test ! -z "${WORK_DIR}" && test -d "${WORK_DIR}" && cd "${WORK_DIR}"

do_files_need_vault=$(do_files_require_vault_token)
echo "DO FILES NEED VAULT: ${do_files_need_vault}"

if [ "${do_files_need_vault}" == "true" ]
then
    echo "VAULT TOKEN REQUIRED"
    get_vault_token
    verify_vault_token
else
    echo "VAULT TOKEN NOT REQUIRED"
fi

render_file

exit 0
