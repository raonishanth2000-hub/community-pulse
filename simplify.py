# simplify.py - Turns GitHub's big replies into small dictionaries.
# GitHub sends dozens of fields per issue; we keep only the ones Community Pulse uses.

BODY_LENGTH = 800  # how many characters of the issue or PR text we keep


# Gets the login name and account type (User or Bot) of a GitHub user.
# In: user data (empty for deleted accounts). Out: login and type.
def describe_user(user):
    if user is None:
        return "ghost", "User"
    return user["login"], user["type"]


# Gets the names of an item's labels. In: raw item. Out: list of names like ["bug", "docs"].
def label_names(raw):
    names = []
    for label in raw.get("labels", []):
        names.append(label["name"])
    return names


# Removes hidden HTML comments like "<!-- Please describe your change -->". Many repos'
# PR templates start with one, and it isn't shown on GitHub, so it isn't the author's words.
# In: text. Out: the text without comments. A comment with no end (because the text
# was cut short) is removed up to the end of the text.
def remove_html_comments(text):
    result = ""
    while True:
        start = text.find("<!--")
        if start == -1:
            return result + text
        end = text.find("-->", start)
        if end == -1:
            return result + text[:start]
        result = result + text[:start]
        text = text[end + 3:]


# Gets the first 800 characters of the item's own text, after removing hidden comments.
# In: raw item. Out: the text, or an empty string if the author left it blank.
def short_body(raw):
    body = raw.get("body")
    if body is None:
        return ""
    return remove_html_comments(body).strip()[:BODY_LENGTH]


# Keeps only the fields we need from one issue or PR. In: raw item. Out: small dictionary.
# An item is a PR if GitHub gave it a "pull_request" field.
def simplify_item(raw):
    login, user_type = describe_user(raw["user"])
    return {"number": raw["number"], "title": raw["title"],
            "is_pr": "pull_request" in raw, "author": login,
            "author_association": raw["author_association"],
            "created_at": raw["created_at"], "updated_at": raw["updated_at"],
            "state": raw["state"], "draft": raw.get("draft", False),
            "labels": label_names(raw), "body": short_body(raw),
            "comments": [], "reviews": []}
