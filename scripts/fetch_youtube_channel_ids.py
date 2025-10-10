#!/usr/bin/env python3
"""
Utility script to fetch YouTube channel IDs from handles.

Usage:
    python scripts/fetch_youtube_channel_ids.py @HowIAI @EverydayAI

This script helps you manually look up and verify YouTube channel IDs.
Due to YouTube's consent pages and API restrictions, manual verification
is often necessary.

Instructions:
1. Visit https://www.youtube.com/@HANDLE
2. Right-click -> View Page Source
3. Search for "channelId" or "externalId"
4. Copy the channel ID (starts with UC, 24 characters total)
5. Update the OPML file with the RSS feed URL format:
   https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
"""

import sys
from pathlib import Path

# List of YouTube handles to look up
YOUTUBE_CHANNELS = [
    ("How I AI", "@HowIAI", "UCqZSBSRcc_EzDYISssxmGHw"),  # Found but uncertain
    ("Everyday AI Podcast", "@EverydayAI", None),
    ("AI For Humans", "@AIForHumansShow", "UCghJTNTO9kcDeUFXMuSDGLQ"),
    ("Behind the Craft", "@peteryangyt", None),  # Peter Yang's channel
    ("AI and I", "@danshipper", None),
    ("Product Growth Podcast", "@growproduct", None),  # Aakash Gupta
]


def main():
    """Print YouTube channel lookup instructions."""
    print("=" * 70)
    print("YouTube Channel ID Lookup Guide")
    print("=" * 70)
    print()

    for name, handle, channel_id in YOUTUBE_CHANNELS:
        print(f"📺 {name}")
        print(f"   Handle: {handle}")
        print(f"   URL: https://www.youtube.com/{handle}")

        if channel_id:
            print(f"   ✓ Channel ID: {channel_id}")
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            print(f"   ✓ RSS Feed: {rss_url}")
        else:
            print("   ❌ Channel ID: NOT FOUND - needs manual lookup")
            print("   📝 Steps:")
            print(f"      1. Visit: https://www.youtube.com/{handle}")
            print("      2. Right-click -> View Page Source")
            print('      3. Search for: "channelId" or "externalId"')
            print("      4. Copy the channel ID (starts with UC, 24 chars)")

        print()

    print("=" * 70)
    print("Manual Lookup Tools:")
    print("=" * 70)
    print("• https://commentpicker.com/youtube-channel-id.php")
    print("• https://www.tunepocket.com/youtube-channel-id-finder/")
    print()

    print("=" * 70)
    print("YouTube RSS Feed Format:")
    print("=" * 70)
    print("https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID")
    print()


if __name__ == "__main__":
    main()
