# contributing_file.py - Downloads the text of a repo's CONTRIBUTING file from GitHub.
# GitHub's community profile gives two links: "url" (for programs) and "html_url" (the web
# page). When the file lives in an organisation's shared ".github" repo, "url" can be wrong,
# so we also try an address built from "html_url". Read-only, like everything else.

import base64

from github_api import API_URL, get_json

MAX_TEXT = 6000  # characters of CONTRIBUTING we keep


# Turns a web link like "https://github.com/owner/repo/blob/main/CONTRIBUTING.md" into the
# matching API address. In: html_url. Out: the API address, or "" if it isn't that shape.
def html_to_api_url(html_url):
    prefix = "https://github.com/"
    if not html_url.startswith(prefix):
        return ""
    parts = html_url[len(prefix):].split("/")
    if len(parts) < 5 or parts[2] != "blob":
        return ""
    file_path = "/".join(parts[4:])
    return API_URL + "/repos/" + parts[0] + "/" + parts[1] + "/contents/" + file_path + "?ref=" + parts[3]


# Downloads one file through GitHub's contents API (the text arrives base64-encoded).
# In: the API address and token. Out: the first 6000 characters, or None if it didn't work.
def download_text(url, token):
    if not url.startswith(API_URL + "/"):
        return None
    try:
        data, calls_left = get_json(url[len(API_URL):], token)
        raw_bytes = base64.b64decode(data["content"])
    except (RuntimeError, KeyError, ValueError):
        return None
    return raw_bytes.decode("utf-8", errors="replace")[:MAX_TEXT]


# Tries the "url" link first, then the address built from "html_url".
# In: the community profile's contributing entry and the token. Out: text, or None.
def download_contributing(contributing, token):
    text = download_text(contributing.get("url") or "", token)
    if text is None:
        text = download_text(html_to_api_url(contributing.get("html_url") or ""), token)
    if text is None:
        print("Could not download the CONTRIBUTING file.")
    return text
