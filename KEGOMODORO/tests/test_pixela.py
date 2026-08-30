"""Unit tests for kegomodoro.pixela."""

import time
from unittest.mock import MagicMock, patch
import requests

from kegomodoro.pixela import PixelaClient


def test_pixela_is_configured():
    client_empty = PixelaClient(username="", token="", graph_id="")
    assert client_empty.is_configured() is False

    client_partial = PixelaClient(username="user", token="", graph_id="graph")
    assert client_partial.is_configured() is False

    client_valid = PixelaClient(username="user", token="token123", graph_id="graph456")
    assert client_valid.is_configured() is True


def test_pixela_unconfigured_sync():
    client = PixelaClient(username="", token="", graph_id="")
    called = False

    def on_complete(success, msg):
        nonlocal called
        called = True

    launched = client.sync_hours_async(5, on_complete=on_complete)
    assert launched is False
    assert called is False


@patch("requests.post")
@patch("requests.put")
def test_pixela_configured_sync_success(mock_put, mock_post):
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post.return_value = mock_post_resp

    mock_put_resp = MagicMock()
    mock_put_resp.status_code = 200
    mock_put.return_value = mock_put_resp

    client = PixelaClient(username="testuser", token="testtok", graph_id="testgraph")

    result = {}

    def on_complete(success, msg):
        result["success"] = success
        result["msg"] = msg

    launched = client.sync_hours_async(3, date_str="20260830", on_complete=on_complete)
    assert launched is True

    # Wait for background thread
    for _ in range(50):
        if "success" in result:
            break
        time.sleep(0.05)

    assert result.get("success") is True
    assert mock_post.called
    assert mock_put.called


@patch("requests.post")
@patch("requests.put")
def test_pixela_network_error_bounded_retry(mock_put, mock_post):
    mock_post.side_effect = requests.RequestException("Network timeout")
    mock_put.side_effect = requests.RequestException("Network timeout")

    client = PixelaClient(username="testuser", token="testtok", graph_id="testgraph")

    result = {}

    def on_complete(success, msg):
        result["success"] = success
        result["msg"] = msg

    launched = client.sync_hours_async(2, on_complete=on_complete)
    assert launched is True

    for _ in range(50):
        if "success" in result:
            break
        time.sleep(0.05)

    assert result.get("success") is False
    assert "error" in result.get("msg", "").lower() or "failed" in result.get("msg", "").lower()
