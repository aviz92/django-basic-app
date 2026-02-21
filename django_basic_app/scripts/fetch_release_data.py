"""
fetch_release_data.py

Fetches all data for a specific release version from the API.
Uses pyrest-model-client for typed, model-driven API access.

Usage:
    python fetch_release_data.py --release-version v1.1.0
    python fetch_release_data.py --release-version v1.1.0 --status approved
    python fetch_release_data.py --release-version v1.1.0 --base-url http://prod-server:8000
"""

import argparse
import os

from dotenv import load_dotenv
from pyrest_model_client import RestApiClient, build_header, get_model_fields
from pyrest_model_client.base import BaseAPIModel

load_dotenv()


# ── Models ────────────────────────────────────────────────────────────────────


class FirstApp(BaseAPIModel):
    name: str
    description: str | None = None
    status: str | None = None
    resource_path: str = "first_app"


# Register all models here — add new ones as you expand the project
MODELS: list[type[BaseAPIModel]] = [
    FirstApp,
    # ProductModel,
    # PriceListModel,
    # StockLevelModel,
]


# ── Fetch logic ───────────────────────────────────────────────────────────────


def fetch_all_pages(client: RestApiClient, endpoint: str, params: dict) -> list:
    """Fetches all pages from a paginated endpoint."""
    results = []
    current_params = params.copy()

    while res := client.get(endpoint, params=current_params):  # pylint: disable=W0149
        # Handle both paginated and non-paginated responses
        if isinstance(res, list):
            results.extend(res)
            break
        results.extend(res.get("results", []))
        if not res.get("next"):
            break
        page = res["next"].split("page=")[-1].split("&")[0]
        current_params = {**params, "page": page}
    return results


def fetch_release_data(
    release_version: str,
    base_url: str,
    token: str | None = None,
    status_filter: str | None = None,
) -> dict[str, list[BaseAPIModel]]:
    """
    Fetches all data for a given release version.

    Args:
        release_version: e.g. "v1.1.0"
        base_url:        e.g. "http://localhost:8000"
        token:           Optional auth token
        status_filter:   Optional status filter — "approved", "draft", "future"
    """
    header = build_header(token=token) if token else {}
    client = RestApiClient(base_url=base_url, header=header, add_trailing_slash=True)

    # Base params sent on every request
    params = {"release__version": release_version}
    if status_filter:
        params["status"] = status_filter

    print(f"\n📦 Fetching data for release: {release_version}")
    if status_filter:
        print(f"   Status filter: {status_filter}")
    print(f"   API: {base_url}\n")

    all_data = {}

    for model_class in MODELS:
        dummy = model_class.model_construct()
        endpoint = dummy.resource_path

        raw_results = fetch_all_pages(client, endpoint, params)
        instances = get_model_fields(raw_results, model=model_class)

        all_data[endpoint] = instances
        print(f"  ✅ {model_class.__name__}: {len(instances)} records fetched")

    return all_data


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> dict:
    parser = argparse.ArgumentParser(description="Fetch release data from the API")
    parser.add_argument(
        "--base-url", help="Base URL for the API", default=os.getenv("BASE_URL", "http://localhost:8000")
    )
    parser.add_argument("--release-version", help="e.g. v1.1.0", default=os.getenv("RELEASE_VERSION"))
    parser.add_argument("--token", help="Optional auth token", default=os.getenv("TOKEN"))
    parser.add_argument(
        "--status",
        choices=["draft", "future", "approved"],
        default="draft",
        help="Filter by data status (default: approved)",
    )
    args = parser.parse_args()

    data = fetch_release_data(
        release_version=args.release_version,
        base_url=args.base_url,
        token=args.token,
        status_filter=args.status,
    )

    print(f"\n🎯 Done. Total models fetched: {len(data)}")
    return data


if __name__ == "__main__":
    main()
