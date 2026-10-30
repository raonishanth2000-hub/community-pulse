# github_api.py - Talking to GitHub.
# Reads the token, makes GET requests (read-only), and turns errors into plain English.
# Problems are "raised" as errors, so whoever called us (the command line, or a
# dashboard) can decide how to show the message.

import os
import time

import requests
from dotenv import load_dotenv

API_URL = "https://api.github.com"
# The .env file in the project folder (the same folder as this file), wherever we're run from.
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


# Loads GITHUB_TOKEN from the project's .env file. In: nothing. Out: the token text.
# Raises an error if the token is missing. The token is never printed.
def read_token():
    load_dotenv(ENV_FILE)
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("No GITHUB_TOKEN found. Put GITHUB_TOKEN=your_token in a .env file.")
    return token


# Turns a GitHub error code into a plain-English message.
# In: the status code number. Out: the message.
def explain_error(status_code):
    if status_code == 401:
        return "Bad GitHub token"
    if status_code == 403 or status_code == 429:
        return "GitHub rate limit reached, try again later"
    if status_code == 404:
        return "Repo not found, or it is private"
    return "GitHub returned an unexpected error, code " + str(status_code)


# Makes one GET request to GitHub, after a short pause so we are polite.
# In: the path after api.github.com (like "/repos/fastapi/fastapi/issues") and the token.
# Out: the JSON data and how many API calls we have left. Raises an error if it fails.
def get_json(path, token):
    time.sleep(0.1)
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"}
    try:
        response = requests.get(API_URL + path, headers=headers, timeout=30)
    except requests.RequestException:
        raise RuntimeError("Could not reach GitHub. Check your internet connection.")
    if response.status_code != 200:
        raise RuntimeError(explain_error(response.status_code))
    calls_left = int(response.headers.get("X-RateLimit-Remaining", "5000"))
    return response.json(), calls_left
