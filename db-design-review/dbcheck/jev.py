"""Minimal client for the TypeSafe System One endpoint (POST /v1/systemone), with an on-disk cache."""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.typesafe.ai/v1/systemone"
RETRY_STATUSES = {429, 500, 502, 503, 529}


class JevError(RuntimeError):
    pass


class JevClient:
    def __init__(self, model: str = "jev-latest", cache_dir: str | Path | None = ".dbcheck-cache",
                 api_key: str | None = None, retries: int = 4, timeout: float = 60.0):
        self.model = model
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.retries = retries
        self.timeout = timeout
        self.usage = {"input_tokens": 0, "output_tokens": 0, "requests": 0, "cached": 0}

    def ask(self, state: Any, questions: dict[str, dict]) -> dict[str, dict]:
        """Send one request; every question runs in parallel against the same state."""
        body = {"state": state, "model": self.model, "questions": questions}
        payload = json.dumps(body, sort_keys=True, ensure_ascii=False).encode()

        cache_file = None
        if self.cache_dir:
            cache_file = self.cache_dir / f"{hashlib.sha256(payload).hexdigest()}.json"
            if cache_file.exists():
                self.usage["cached"] += 1
                return json.loads(cache_file.read_text())["answers"]

        if not self.api_key:
            raise JevError("TYPESAFE_API_KEY is not set (get one at https://console.typesafe.ai/keys, or use --dry-run)")

        req = urllib.request.Request(API_URL, data=payload, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read())
                break
            except urllib.error.HTTPError as e:
                if e.code in RETRY_STATUSES and attempt < self.retries:
                    time.sleep(min(2 ** attempt, 20))
                    continue
                raise JevError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from e
            except urllib.error.URLError as e:
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 20))
                    continue
                raise JevError(f"connection failed: {e.reason}") from e

        self.usage["requests"] += 1
        for k in ("input_tokens", "output_tokens"):
            self.usage[k] += (data.get("usage") or {}).get(k, 0)
        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(data, indent=2))
        return data["answers"]
