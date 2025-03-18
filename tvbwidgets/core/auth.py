# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
import json
import os
import requests
from .logger.builder import get_logger

CLB_AUTH = 'CLB_AUTH'

LOGGER = get_logger(__name__)


def get_current_token():
    try:
        # for ebrains lab
        from clb_nb_utils import oauth as clb_oauth

        bearer_token = clb_oauth.get_token()
        return bearer_token

    except Exception:
        try:
            # for jsc lab
            LOGGER.info("Try to retrieve auth token from Jupyter-JSC.")
            api_url = os.getenv("JUPYTERHUB_API_URL")
            user_api_url = f"{api_url}/user_oauth"
            headers = {"Authorization": "token {}".format(os.getenv("JUPYTERHUB_API_TOKEN"))}
            r = requests.get(user_api_url, headers=headers)
            response = json.loads(r.content.decode("utf-8"))
            token = response["auth_state"]["access_token"]
            return token

        except Exception:
            # local
            LOGGER.info("We could not find Collab Auth Token or retrieve it from Jupyter-JSC,"
                        " we will search for env CLB_AUTH variable")

            env_token = os.environ.get(CLB_AUTH)
            if env_token is not None:
                LOGGER.info("We found Collab Auth in environment!")
                return env_token

    raise RuntimeError("Could not authenticate in Collab. Try to define local env CLB_AUTH or login EBRAINS")
