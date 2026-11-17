# spotify-oauth
Small demo app demonstrating Spotify OAuth

Minimal Python example that walks through Spotify's OAuth Authorization Code flow by hand,
using only `requests` and the standard library (no OAuth library), to log in and list the
current user's playlists. Written for learning how OAuth actually works under the hood.

## Setup

1. Create an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and add
   `http://127.0.0.1:8080/callback` as a Redirect URI.
2. Copy `.env.example` to `.env` and fill in your Client ID and Client Secret.
3. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

## Run it

```bash
export $(cat .env | xargs)
.venv/bin/python main.py
```

This opens `http://127.0.0.1:8080/` in your browser with a "Connect to Spotify" button.
Click it, authorize the app, and you'll be redirected back to a page that lists your
playlists.

## How it works

```mermaid
sequenceDiagram
    participant Browser
    participant App as main.py (127.0.0.1:8080)
    participant Spotify as Spotify Accounts/API

    Browser->>App: GET /
    App-->>Browser: Landing page with "Connect to Spotify" button

    Browser->>Spotify: GET /authorize (click button)
    Spotify-->>Browser: Login + consent screen
    Spotify->>Browser: Redirect to /callback?code=...

    Browser->>App: GET /callback?code=...
    App->>Spotify: POST /api/token (exchange code for access token)
    Spotify-->>App: access_token

    App->>Spotify: GET /v1/me/playlists (Bearer access_token)
    Spotify-->>App: playlists JSON

    App-->>Browser: Rendered playlist page
```
