#!/usr/bin/env python3

import requests
from collections import Counter

API = "https://public.api.bsky.app/xrpc/"
LIST_URI = (
    "at://did:plc:zmyydkc2zzznc4smjufuerlx/"
    "app.bsky.graph.list/3myxgysokhc2t"
)
REDFOX = "redfoxofficial.bsky.social"
LIMIT = 100
TIMEOUT = 30

session = requests.Session()
session.headers["User-Agent"] = "BlueskyListAnalyzer/1.0"

def get_json(endpoint, params):
    response = session.get(
        API + endpoint,
        params=params,
        timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def has_media(embed):
    if not embed:
        return False

    kind = embed.get("$type", "")

    if kind in (
        "app.bsky.embed.images#view",
        "app.bsky.embed.video#view",
    ):
        return True

    if kind == "app.bsky.embed.recordWithMedia#view":
        return has_media(embed.get("media", {}))

    return False


def mentions_redfox(record):
    text = record.get("text", "").lower()

    if REDFOX in text:
        return True

    # Ook echte Bluesky-mentions via facets herkennen.
    for facet in record.get("facets", []) or []:
        for feature in facet.get("features", []):
            if feature.get("$type") == (
                "app.bsky.richtext.facet#mention"
            ):
                if feature.get("did", "").lower() == REDFOX:
                    return True

    return False


def main():
    authors = Counter()
    redfox_counts = Counter()
    reposted_authors = Counter()
    reposters = Counter()

    seen_items = set()
    cursor = None
    total_posts = 0
    total_replies = 0
    total_redfox = 0
    total_reposts = 0

    print("Bluesky-lijst analyseren...")

    while True:
        params = {
            "list": LIST_URI,
            "limit": LIMIT,
        }

        if cursor:
            params["cursor"] = cursor

        data = get_json("app.bsky.feed.getListFeed", params)

        for item in data.get("feed", []):
            post = item.get("post", {})
            record = post.get("record", {})
            author = post.get("author", {})
            embed = post.get("embed", {})
            uri = post.get("uri", "")

            # Alleen media-items analyseren.
            if not has_media(embed):
                continue

            # Quote-only posts uitsluiten.
            if embed.get("$type") == "app.bsky.embed.record#view":
                continue

            # Dubbelen van hetzelfde bericht vermijden.
            if uri in seen_items:
                continue
            seen_items.add(uri)

            handle = author.get("handle", "onbekend")
            is_reply = bool(record.get("reply"))
            is_redfox = mentions_redfox(record)

            authors[handle] += 1

            if is_reply:
                total_replies += 1
                if is_redfox:
                    redfox_counts["replies"] += 1
            else:
                total_posts += 1
                if is_redfox:
                    redfox_counts["posts"] += 1

            if is_redfox:
                total_redfox += 1

            # Alleen expliciete repost-redenen meetellen.
            reason = item.get("reason", {}) or {}
            if reason.get("$type") == (
                "app.bsky.feed.defs#reasonRepost"
            ):
                total_reposts += 1
                reposted_authors[handle] += 1
                reposter = reason.get("by", {}).get(
                    "handle", "onbekend"
                )
                reposters[reposter] += 1

        cursor = data.get("cursor")
        if not cursor:
            break

    print("\n========== TOTAAL ==========")
    print(f"Media-posts: {total_posts}")
    print(f"Media-replies: {total_replies}")
    print(f"Totaal media: {total_posts + total_replies}")

    print("\n========== REDFOX ==========")
    print(f"RedFox posts: {redfox_counts['posts']}")
    print(f"RedFox replies: {redfox_counts['replies']}")
    print(f"Totaal RedFox mentions: {total_redfox}")

    print("\n========== MEESTE MEDIA ==========")
    for handle, amount in authors.most_common(30):
        print(f"{handle}: {amount}")

    print("\n========== MEEST GEREPOSTE AUTEURS ==========")
    if reposted_authors:
        for handle, amount in reposted_authors.most_common(30):
            print(f"{handle}: {amount}")
    else:
        print(
            "Geen repost-redenen gevonden in de opgehaalde "
            "lijstfeed."
        )

    print("\n========== ACCOUNTS DIE REPOSTEN ==========")
    for handle, amount in reposters.most_common(20):
        print(f"{handle}: {amount}")

    print("\n========== VOLGADVIES ==========")
    print("Controleer de topaccounts onder MEESTE MEDIA.")
    print(
        "Dit zijn kandidaten om te volgen; controleer ook "
        "de kwaliteit en actualiteit van hun media."
    )


if __name__ == "__main__":
    main()