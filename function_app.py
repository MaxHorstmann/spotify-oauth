"""Azure Functions entry point: serves the same landing page and /callback as
main.py's local server, reusing its OAuth helpers.

Functions are stateless, so the OAuth `state` lives in a short-lived cookie
instead of in process memory.
"""

import html
import http.cookies
import secrets

import azure.functions as func
import requests

from main import (
    CONNECT_BUTTON,
    PAGE_TEMPLATE,
    build_authorize_url,
    exchange_code_for_token,
    get_playlists,
    render_playlists,
)

STATE_COOKIE = "spotify_oauth_state"

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def respond(content, status=200, set_cookie=None):
    headers = {"Set-Cookie": set_cookie} if set_cookie else None
    return func.HttpResponse(
        PAGE_TEMPLATE.format(content=content),
        status_code=status,
        mimetype="text/html",
        charset="utf-8",
        headers=headers,
    )


@app.route(route="callback", methods=["GET"])
def callback(req: func.HttpRequest) -> func.HttpResponse:
    cookies = http.cookies.SimpleCookie(req.headers.get("Cookie", ""))
    expected_state = cookies[STATE_COOKIE].value if STATE_COOKIE in cookies else None
    code = req.params.get("code")
    returned_state = req.params.get("state")
    clear_cookie = f"{STATE_COOKIE}=; Path=/callback; Max-Age=0"

    if expected_state is None or returned_state != expected_state or code is None:
        return respond("<p>Something went wrong - state mismatch or no code.</p>", 400, clear_cookie)

    try:
        access_token = exchange_code_for_token(code)
        playlists = get_playlists(access_token)
        return respond(f"<h2>Your playlists</h2>{render_playlists(playlists)}", set_cookie=clear_cookie)
    except requests.HTTPError as exc:
        return respond(f"<p>Spotify API error: {html.escape(str(exc))}</p>", 500, clear_cookie)


@app.route(route="{*path}", methods=["GET"])
def landing(req: func.HttpRequest) -> func.HttpResponse:
    state = secrets.token_urlsafe(16)
    cookie = f"{STATE_COOKIE}={state}; Path=/callback; Max-Age=600; HttpOnly; Secure; SameSite=Lax"
    return respond(CONNECT_BUTTON.format(authorize_url=html.escape(build_authorize_url(state))), set_cookie=cookie)
