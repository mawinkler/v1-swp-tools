#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import textwrap
from typing import Any, Dict, List

import requests

# import urllib3
from typeguard import typechecked

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s (%(threadName)s) [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# HERE
REGION_SWP = "us-1"  # Examples: de-1 sg-1
# API_BASE_URL_DS = f"https://3.120.149.217:4119/api/"
# /HERE

# Do not change
ENDPOINT_SWP = "swp"
# ENDPOINT_DS = "ds"
API_KEY_SWP = os.environ["API_KEY_SWP"]
if REGION_SWP == "":
    API_BASE_URL_SWP = "https://workload.us-1.cloudone.trendmicro.com/api/"
else:
    API_BASE_URL_SWP = f"https://workload.{REGION_SWP}.cloudone.trendmicro.com/api/"
# API_KEY_DS = os.environ["API_KEY_DS"]
REQUESTS_TIMEOUTS = (2, 30)
# /Do not change


# #############################################################################
# Errors
# #############################################################################
class TrendRequestError(Exception):
    """Define a base error."""

    pass


class TrendRequestAuthorizationError(TrendRequestError):
    """Define an error related to invalid API Permissions."""

    pass


class TrendRequestValidationError(TrendRequestError):
    """Define an error related to a validation error from a request."""

    pass


class TrendRequestNotFoundError(TrendRequestError):
    """Define an error related to requested information not found."""

    pass


# #############################################################################
# Connector to SWP/DS
# #############################################################################
class Connector:
    def __init__(self, endpoint) -> None:
        # # V1
        # self._headers = {
        #     "Authorization": f"Bearer {API_KEY_SWP}",
        #     "Content-Type": "application/json;charset=utf-8",
        # }

        # SWP / DS
        if endpoint == ENDPOINT_SWP:
            self._url = f"{API_BASE_URL_SWP}"
            self._headers = {
                "Content-type": "application/json",
                "api-secret-key": API_KEY_SWP,
                "api-version": "v1",
            }
            self._verify = True

        # elif endpoint == ENDPOINT_DS:
        #     self._url = f"{API_BASE_URL_DS}"
        #     self._headers = {
        #         "Content-type": "application/json",
        #         "Accept": "application/json",
        #         "api-secret-key": API_KEY_DS,
        #         "api-version": "v1",
        #     }
        #     self._verify = False

        else:
            raise ValueError(f"Invalid endpoint: {endpoint}")

    def get(self, endpoint) -> Any:
        """Send an HTTP GET request and check response for errors.

        Args:
            url (str): API Endpoint
        """

        response = None
        try:
            response = requests.get(
                self._url + endpoint, headers=self._headers, verify=self._verify, timeout=REQUESTS_TIMEOUTS
            )
            self._check_error(response)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            _LOGGER.error(errh.args[0])
            raise
        except requests.exceptions.ReadTimeout:
            _LOGGER.error("Time out")
            raise
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Connection error")
            raise
        except requests.exceptions.RequestException:
            _LOGGER.error("Exception request")
            raise

        return response.json()

    def patch(self, endpoint, data) -> Any:
        """Send an HTTP PATCH request and check response for errors.

        Args:
            url (str): API Endpoint
            data (json): PATCH request body.
        """

        response = None
        try:
            response = requests.patch(
                self._url + endpoint,
                data=json.dumps(data),
                headers=self._headers,
                verify=self._verify,
                timeout=REQUESTS_TIMEOUTS,
            )
            self._check_error(response)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            _LOGGER.error(errh.args[0])
            raise
        except requests.exceptions.ReadTimeout:
            _LOGGER.error("Time out")
            raise
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Connection error")
            raise
        except requests.exceptions.RequestException:
            _LOGGER.error("Exception request")
            raise

        return response.json()

    def post(self, endpoint, data) -> Any:
        """Send an HTTP POST request and check response for errors.

        Args:
            url (str): API Endpoint
            data (json): POST request body.
        """

        response = None
        try:
            response = requests.post(
                self._url + endpoint,
                data=json.dumps(data),
                headers=self._headers,
                verify=self._verify,
                timeout=REQUESTS_TIMEOUTS,
            )
            self._check_error(response)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            _LOGGER.error(errh.args[0])
            raise
        except requests.exceptions.ReadTimeout:
            _LOGGER.error("Time out")
            raise
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Connection error")
            raise
        except requests.exceptions.RequestException:
            _LOGGER.error("Exception request")
            raise

        return response.json()

    @typechecked
    def get_paged(self, endpoint, key) -> Dict:
        """Retrieve all from endpoint"""

        paged = {}
        id_value, total_num = 0, 0
        max_items = 100

        while True:
            payload = {
                "maxItems": max_items,
                "searchCriteria": [
                    {
                        "idValue": id_value,
                        "idTest": "greater-than",
                    }
                ],
                "sortByObjectID": "true",
            }

            response = self.post(endpoint + "/search", data=payload)

            num_found = len(response[key])
            if num_found == 0:
                break

            for item in response[key]:
                # Filter out groups from cloud providers
                # TODO: validate checks
                if item.get("cloudType") is None and item.get("type") != "aws-account":
                    paged[item.get("ID")] = item

            id_value = response[key][-1]["ID"]

            if num_found == 0:
                break

            total_num = total_num + num_found

        return paged

    @typechecked
    def get_by_name(self, endpoint, key, name, parent_id) -> int:
        """Retrieve all"""

        # We limit to more than one to detect duplicates by name
        max_items = 2

        if parent_id is None:
            payload = {
                "maxItems": max_items,
                "searchCriteria": [
                    {
                        "fieldName": "name",
                        "stringTest": "equal",
                        "stringValue": name,
                    }
                ],
                "sortByObjectID": "true",
            }
        else:
            parent_field = "parentID"

            payload = {
                "maxItems": max_items,
                "searchCriteria": [
                    {
                        "fieldName": "name",
                        "stringTest": "equal",
                        "stringValue": name,
                    },
                    {
                        "fieldName": parent_field,
                        "numericTest": "equal",
                        "numericValue": parent_id,
                    },
                ],
                "sortByObjectID": "true",
            }

        response = self.post(endpoint + "/search", data=payload)

        cnt = len(response[key])
        if cnt == 1:
            item = response[key][0]
            if item.get("ID") is not None:
                return item.get("ID")
        elif cnt > 1:
            _LOGGER.warning(f"More than one group or folder where returned. Count {len(response[key])}")
            # endpoint_groups = self.get_paged(endpoint, key)

        else:
            raise ValueError(f"Group or folder named {name} not found.")

    @staticmethod
    def _check_error(response: requests.Response) -> None:
        """Check response for Errors.

        Args:
            response (Response): Response to check.
        """

        if not response.ok:
            match response.status_code:
                case 400:
                    tre = TrendRequestError("400 Bad request")
                    tre.message = json.loads(response.content.decode("utf-8")).get("message")
                    _LOGGER.error(f"{tre.message}")
                    raise tre
                case 401:
                    raise TrendRequestAuthorizationError(
                        "401 Unauthorized. The requesting user does not have enough privilege."
                    )
                case 403:
                    raise TrendRequestAuthorizationError(
                        "403 Forbidden. The requesting user does not have enough privilege."
                    )
                case 404:
                    raise TrendRequestNotFoundError("404 Not found")
                case 422:
                    raise TrendRequestValidationError("500 Unprocessed Entity. Validation error")
                case 500:
                    raise TrendRequestError("500 The parsing of the template file failed")
                case 503:
                    raise TrendRequestError("503 Service unavailable")
                case _:
                    raise TrendRequestError(response.text)


# #############################################################################
# Compare
# #############################################################################
def compare_json(json1, json2):
    """
    Recursively compares two JSON objects and returns a report of differences.

    Args:
      json1: The first JSON object.
      json2: The second JSON object.

    Returns:
      A dictionary containing the comparison results:
        - 'identical': True if the objects are identical, False otherwise.
        - 'differences': A list of dictionaries, each containing information about a difference.
          - 'path': The path to the differing element (e.g., '["key1", "subkey"]').
          - 'value1': The value in json1.
          - 'value2': The value in json2.
    """

    differences = []

    def _compare(obj1, obj2, path):
        # Comare Dictionaries
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            for key in obj1:
                if key not in obj2 or obj1.get("key", None) != obj2.get("key", None):
                    if obj1.get("key", None) is not None and obj2.get("key", None) is not None:
                        differences.append(
                            {
                                "path": f"{path}{'/' if path else ''}{key}",
                                "value1": obj1.get("key", None),
                                "value2": obj2.get("key", None),
                            }
                        )
                _compare(obj1[key], obj2.get(key, {}), f"{path}/{key}")

        # Compare Lists
        elif isinstance(obj1, list) and isinstance(obj2, list):
            # Find Differences Between Two Lists
            only_in_list1 = set(obj1) - set(obj2)  # Elements in obj1 but not in obj2
            only_in_list2 = set(obj2) - set(obj1)
            if only_in_list1 != only_in_list2:
                differences.append(
                    {
                        "path": f"{path}{'/' if path else ''}",
                        "value1": only_in_list1,
                        "value2": only_in_list2,
                    }
                )

            # # Compare Items in Lists
            # for i in range(min(len(obj1), len(obj2))):
            #     if obj1[i] != obj2[i]:
            #         differences.append(
            #             {
            #                 "path": f"{path}[{i}]",
            #                 "value1": obj1[i],
            #                 "value2": obj2[i],
            #             }
            #         )
            #     _compare(obj1[i], obj2[i], f"{path}[{i}]")

        # Compare Primitive Types
        else:  # Primitive types (strings, numbers, booleans)
            if obj1 != obj2:
                differences.append(
                    {
                        "path": path,
                        "value1": obj1,
                        "value2": obj2,
                    }
                )

    _compare(json1, json2, "")
    
    return {
        "identical": len(differences) == 0,
        "differences": differences,
    }


# #############################################################################
# Main
# #############################################################################
# Connectors
# connector_ds = Connector(ENDPOINT_DS)
connector_swp = Connector(ENDPOINT_SWP)


def main() -> None:
    """Entry point."""

    parser = argparse.ArgumentParser(
        prog="python3 policy-compare.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Compare two Policies and list the differences",
        epilog=textwrap.dedent(
            """\
            Examples:
            --------------------------------
            $ ./policy-compare.py --policy1 ID --policy2 ID
            """
        ),
    )

    parser.add_argument("--policy1", type=int, nargs=1, metavar="ID", help="policy one")
    parser.add_argument("--policy2", type=int, nargs=1, metavar="ID", help="policy two")

    args = parser.parse_args()

    json1 = connector_swp.get(endpoint=f"policies/{args.policy1[0]}")
    json2 = connector_swp.get(endpoint=f"policies/{args.policy2[0]}")

    json1_name = json1.get("name", "Policy 1")
    json2_name = json2.get("name", "Policy 1")

    comparison_result = compare_json(json1, json2)

    print("Identical:", comparison_result["identical"])
    if len(comparison_result["differences"]) > 0:
        print("Differences:")
        for diff in comparison_result["differences"]:
            print(f"- Path: {diff['path']}")
            print(f"  {json1_name}: {diff['value1']}")
            print(f"  {json2_name}: {diff['value2']}\n")


if __name__ == "__main__":
    main()
