from __future__ import annotations

import requests

DEFAULT_TIMEOUT = 20
USER_AGENT = "job-application-agent/0.3 (+manual-review; no-auto-submit)"


def get_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> object:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.json()
