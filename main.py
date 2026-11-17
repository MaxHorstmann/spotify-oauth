"""Minimal example: walk through Spotify's OAuth Authorization Code flow
by hand (no OAuth library) and show the current user's playlists in the browser.

Steps:
  1. Serve a landing page with a "Connect to Spotify" button.
  2. The button links to Spotify's /authorize page.
  3. Catch the redirect on the same local HTTP server's /callback route.
  4. Exchange the returned `code` for an access token via POST /api/token.
  5. Call the Web API with the token and render the playlists as the response.
"""

import base64
import html
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

PAGE_TEMPLATE = """
<!doctype html>
<html>
  <body style="font-family: sans-serif; text-align: center; margin-top: 10%;">
    <h1>Spotify OAuth Demo</h1>
    {content}
  </body>
</html>
"""

CONNECT_BUTTON = """
<a href="{authorize_url}">
  <button style="background:#1db954; color:white; border:none;
                  padding:14px 28px; font-size:16px; border-radius:999px;
                  cursor:pointer;">
    Connect to Spotify
  </button>
</a>
"""


def build_authorize_url(state):
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


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


def render_playlists(playlists):
    rows = []
    for playlist in playlists:
        if playlist is None:
            continue
        track_count = (playlist.get("items") or {}).get("total", "?")
        rows.append(f"<li>{html.escape(playlist['name'])} ({track_count} tracks)</li>")
    return f"<ul style='list-style:none; padding:0;'>{''.join(rows)}</ul>"


def run_server():
    state = secrets.token_urlsafe(16)
    done = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path == "/callback":
                self._handle_callback()
            else:
                self._respond(CONNECT_BUTTON.format(authorize_url=html.escape(build_authorize_url(state))))

        def _handle_callback(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code = query.get("code", [None])[0]
            returned_state = query.get("state", [None])[0]

            if returned_state != state or code is None:
                self._respond("<p>Something went wrong - state mismatch or no code.</p>", status=400)
                done["finished"] = True
                return

            try:
                access_token = exchange_code_for_token(code)
                playlists = get_playlists(access_token)
                self._respond(f"<h2>Your playlists</h2>{render_playlists(playlists)}")
            except requests.HTTPError as exc:
                self._respond(f"<p>Spotify API error: {html.escape(str(exc))}</p>", status=500)
            done["finished"] = True

        def _respond(self, content, status=200):
            body = PAGE_TEMPLATE.format(content=content).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass  # silence default request logging

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    print("Open http://127.0.0.1:8080/ in your browser to connect.")
    try:
        webbrowser.open("http://127.0.0.1:8080/")
    except webbrowser.Error:
        pass  # no GUI browser available (e.g. inside a container) - user opens it manually

    with Server(("0.0.0.0", 8080), Handler) as httpd:
        while "finished" not in done:
            httpd.handle_request()


if __name__ == "__main__":
    run_server()
