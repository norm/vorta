#!/bin/bash
#
# Library functions used by slackbot commands.

CHECKOUTS_DIR="${CHECKOUTS_DIR:-/tmp}"


function _pushd {
    # silence the debugging output of the directory stack
    pushd "$1" >/dev/null
}

function _popd {
    # silence the debugging output of the directory stack
    popd >/dev/null
}

function local_repo_to_ref {
    local repo="$1"
    local git_ref="$2"
    local sha

    _pushd "$CHECKOUTS_DIR"

    if [ ! -d "$repo" ]; then
        git clone "git@github.com:moneyadviceservice/${repo}.git"
    fi

    _pushd "$repo" || exit 1
    git fetch

    # lookup the ref (assuming it is a branch or tag), then fallback
    # to treating it as a sha
    if ! sha="$(git show-ref -s "$git_ref")"; then
        sha="$git_ref"
    fi

    git reset --hard "$sha"
    git clean -d --force

    _popd
    _popd
}

# FIXME add tests
function get_hostnames {
    local hostname="$1"

    # allow exact hostname matches, expanding to FQDN if needed
    if [[ "$hostname" == az* ]]; then
        if [[ "$hostname" == *.dev.mas.local ]]; then
            echo "$hostname"
        else
            echo "${hostname}.dev.mas.local"
        fi
    else
        lookup_hostnames_by_tag "$hostname"
    fi
}

function lookup_hostnames_by_tag {
    # The regexp says:
    #
    #   '.{100}'    100 of any character
    #   ' +'        at least one space
    #   '.*'        any number of chars
    #   '\b$1\b'    word break, $1, word break
    #
    # The 100 chars should skip to the last column of the facts file,
    # the word break around the matching parameter ensure it only takes
    # whole word matches (eg not finding 'gin' in 'staging'), and the
    # intermediate '.*' any chars will skip over multiple tags rather than
    # expecting to be only one.

    grep -E ".{100} +.*\b${1}\b" bootstrap/hosts.txt \
        | awk '{ print $1 ".dev.mas.local" }'
}
