"""Test behavior related to the current network status."""

import urllib.request

import pytest


def test_sb_domain_reachable() -> None:
    """Sanity check to make sure domain is reachable."""
    # set seleniumbase domain
    domain = "https://seleniumbase.io/realworld/login"

    # attempt to reach domain
    try:
        # get response from request
        response = urllib.request.urlopen(domain)

        # check status code is 200
        assert response.getcode() == 200

    except urllib.error.URLError:
        # notify failure to reach
        pytest.fail(f"Could not reach domain {domain:!r}")
