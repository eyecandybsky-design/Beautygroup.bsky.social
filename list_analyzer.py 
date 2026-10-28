import requests
from collections import Counter

API = "https://public.api.bsky.app/xrpc/"
LIST = (
    "at://did:plc:zmyydkc2zzznc4smjufuerlx/"
    "app.bsky.graph.list/3myxgysokhc2t"
)
REDFOX = "redfoxofficial.bsky.social"

counts = Counter()
cursor = None
seen = set()

while True:
    params = {"list": LIST, "limit": 100}
    if cursor:
        params["cursor"] = cursor

    r = requests.get(
        API + "app.bsky.feed.getListFeed",
        params=params,
        timeout=30
    )
    r.raise_for_status()
    data = r.json()

    for item in data.get("feed", []):
        post = item["post"]
        record = post.get("record", {})
        author = post.get("author", {})
        embed = post.get("embed", {})
        uri = post.get("uri")

        if uri in seen:
            continue
        seen.add(uri)

        # Alleen media uit originele posts; geen quote-posts
        if record.get("embed", {}).get("$type") == \
                "app.bsky.embed.record":
            continue

        media_types = {
            "app.bsky.embed.images#view",
            "app.bsky.embed.video#view",
            "app.bsky.embed.recordWithMedia#view",
        }

        if embed.get("$type") not in media_types:
            continue

        # recordWithMedia telt alleen als de media zelf foto/video is
        if embed.get("$type") == \
                "app.bsky.embed.recordWithMedia#view":
            inner = embed.get("media", {}).get("$type", "")
            if inner not in {
                "app.bsky.embed.images#view",
                "app.bsky.embed.video#view",
            }:
                continue

        handle = author.get("handle", "onbekend")
        counts[handle] += 1

        text = record.get("text", "").lower()
        if REDFOX in text:
            counts[handle + " | RedFox"] += 1
            counts["TOTAAL REDFOX MENTIONS"] += 1

    cursor = data.get("cursor")
    if not cursor:
        break

print("\n=== MEDIA-ANALYSE ===")
for account, amount in sorted(counts.items()):
    print(f"{account}: {amount}")

print(f"\nTOTAAL MEDIA: {sum(v for k, v in counts.items() if ' | RedFox' not in k and k != 'TOTAAL REDFOX MENTIONS')}")