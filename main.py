"""Minimal example: walk through Spotify's OAuth Authorization Code flow
by hand (no OAuth library) and list the current user's playlists.

Steps:
  1. Send the user to Spotify's /authorize page.
  2. Catch the redirect on a tiny local HTTP server to grab the `code`.
  3. Exchange that code for an access token via POST /api/token.
  4. Use the access token to call the Web API with plain requests.
"""

import base64
import http.server
import os
import secrets
import socketserver
import urllib.parse
import webbrowser

import requests

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = "http://127.0.0.1:8080/callback"
SCOPE = "playlist-read-private playlist-read-collaborative"

AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"


def get_authorization_code():
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
    }
    webbrowser.open(f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}")

    result = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            result["code"] = params.get("code", [None])[0]
            result["state"] = params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Logged in</h1>You can close this tab.")

        def log_message(self, format, *args):
            pass  # silence default request logging

    with socketserver.TCPServer(("127.0.0.1", 8080), CallbackHandler) as httpd:
        httpd.handle_request()  # blocks until the one redirect comes in

    if result.get("state") != state:
        raise RuntimeError("State mismatch - possible CSRF, aborting")
    if result.get("code") is None:
        raise RuntimeError("No authorization code returned")

    return result["code"]


def exchange_code_for_token(code):
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {credentials}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_playlists(access_token):
    response = requests.get(
        f"{API_BASE_URL}/me/playlists",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()["items"]


def main():
    code = get_authorization_code()
    access_token = exchange_code_for_token(code)
    for playlist in get_playlists(access_token):
        print(f"{playlist['name']} ({playlist['tracks']['total']} tracks)")


if __name__ == "__main__":
    main()
