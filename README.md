# spotify-oauth
Small demo app demonstrating Spotify OAuth

Minimal Python example that walks through Spotify's OAuth Authorization Code flow by hand,
using only `requests` and the standard library (no OAuth library), to log in and list the
current user's playlists. Written for learning how OAuth actually works under the hood.

## Setup

1. Create an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and add
   `http://127.0.0.1:8080/callback` as a Redirect URI.
2. Copy `.env.example` to `.env`, fill in your Client ID and Client Secret, then load it into your shell:

   ```bash
   export $(cat .env | xargs)
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run it:

   ```bash
   python main.py
   ```

   This opens a browser window to authorize the app, briefly runs a local server on
   `127.0.0.1:8080` to catch the redirect, exchanges the code for an access token, then
   prints your playlists.
