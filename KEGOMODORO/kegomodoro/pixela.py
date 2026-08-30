"""Optional Pixela synchronization service with bounded retries and timeouts."""

import datetime as dt
import logging
import os
import threading
import time
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)


class PixelaClient:
    """Handles optional background synchronization with Pixela graph service."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        username: Optional[str] = None,
        token: Optional[str] = None,
        graph_id: Optional[str] = None,
    ):
        if endpoint is None:
            endpoint = os.getenv("PIXELA_ENDPOINT", "https://pixe.la/v1/users")
        if username is None:
            username = os.getenv("PIXELA_USERNAME", "")
        if token is None:
            token = os.getenv("PIXELA_TOKEN", "")
        if graph_id is None:
            graph_id = os.getenv("PIXELA_GRAPH_ID", "")

        self.endpoint = str(endpoint or "").strip()
        self.username = str(username or "").strip()
        self.token = str(token or "").strip()
        self.graph_id = str(graph_id or "").strip()

        self._lock = threading.Lock()
        self._is_syncing = False

    def is_configured(self) -> bool:
        """Check if all required Pixela credentials and graph ID are present."""
        return bool(self.username and self.token and self.graph_id)

    def sync_hours_async(
        self,
        hours: int,
        date_str: Optional[str] = None,
        on_complete: Optional[Callable[[bool, str], None]] = None,
    ) -> bool:
        """
        Trigger asynchronous synchronization of hours in a daemon thread.
        Returns True if a sync task was launched, False if not configured or already syncing.
        """
        if not self.is_configured():
            return False

        with self._lock:
            if self._is_syncing:
                logger.info("Pixela sync is already in progress, skipping duplicate.")
                return False
            self._is_syncing = True

        if date_str is None:
            date_str = dt.datetime.now().strftime("%Y%m%d")

        thread = threading.Thread(
            target=self._sync_worker,
            args=(hours, date_str, on_complete),
            daemon=True,
            name="PixelaSyncThread",
        )
        thread.start()
        return True

    def _sync_worker(
        self,
        hours: int,
        date_str: str,
        on_complete: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        success = False
        message = ""
        max_retries = 2
        timeout = (5.0, 10.0)  # (connect_timeout, read_timeout)

        try:
            headers = {"X-USER-TOKEN": self.token}

            for attempt in range(max_retries + 1):
                try:
                    # 1. Ensure user exists (ignore if already exists)
                    user_params = {
                        "token": self.token,
                        "username": self.username,
                        "agreeTermsOfService": "yes",
                        "notMinor": "yes",
                    }
                    try:
                        requests.post(
                            self.endpoint, json=user_params, timeout=timeout
                        )
                    except Exception:
                        pass

                    # 2. Ensure graph exists
                    graph_endpoint = f"{self.endpoint.rstrip('/')}/{self.username}/graphs"
                    graph_params = {
                        "id": self.graph_id,
                        "name": self.username,
                        "unit": "hours",
                        "type": "float",
                        "color": "momiji",
                    }
                    try:
                        requests.post(
                            graph_endpoint,
                            json=graph_params,
                            headers=headers,
                            timeout=timeout,
                        )
                    except Exception:
                        pass

                    # 3. Post / Update pixel
                    pixel_endpoint = (
                        f"{self.endpoint.rstrip('/')}/{self.username}/graphs/{self.graph_id}"
                    )
                    pixel_params = {"date": date_str, "quantity": str(hours)}
                    post_res = requests.post(
                        pixel_endpoint,
                        json=pixel_params,
                        headers=headers,
                        timeout=timeout,
                    )

                    # Update if already exists or on certain Pixela retry conditions
                    update_endpoint = f"{pixel_endpoint}/{date_str}"
                    update_res = requests.put(
                        update_endpoint,
                        json={"quantity": str(hours)},
                        headers=headers,
                        timeout=timeout,
                    )

                    if post_res.status_code in (200, 201) or update_res.status_code in (
                        200,
                        201,
                    ):
                        success = True
                        message = "Pixela sync succeeded"
                        break

                    # If Pixela free tier retry condition occurs
                    if attempt < max_retries:
                        time.sleep(0.5)
                        continue
                    else:
                        message = f"Pixela sync failed with status {post_res.status_code}/{update_res.status_code}"

                except (requests.RequestException, Exception) as e:
                    if attempt < max_retries:
                        time.sleep(0.5)
                        continue
                    message = f"Pixela network error: {e}"

        finally:
            with self._lock:
                self._is_syncing = False

            if on_complete is not None:
                try:
                    on_complete(success, message)
                except Exception:
                    pass
