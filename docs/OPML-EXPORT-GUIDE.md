# How to Export Your Podcast Subscriptions (OPML)

## What is OPML?

OPML is a standard format for sharing podcast subscriptions between apps. You need to export your subscriptions as an OPML file and save it to `data/podcasts.opml`.

## Export from Popular Podcast Apps

### Apple Podcasts (Mac)
1. Open Apple Podcasts
2. Go to **File** → **Export Subscriptions**
3. Save as `podcasts.opml`
4. Move to: `/Users/marc/Code/personal-projects/media-digest/media-digest/data/podcasts.opml`

### Overcast (iOS)
1. Open Overcast app
2. Tap your profile (top right)
3. Tap **Settings**
4. Scroll to **Import/Export OPML**
5. Tap **Export OPML**
6. Share the file and save to your Mac
7. Move to `data/podcasts.opml`

### Pocket Casts
1. Go to Settings → **Import/Export**
2. Tap **Export Subscriptions**
3. Save the file
4. Move to `data/podcasts.opml`

### Castro
1. Open Settings
2. Go to **Export Subscriptions**
3. Save the file
4. Move to `data/podcasts.opml`

### Google Podcasts
1. Open Google Podcasts on web
2. Click Settings (gear icon)
3. Click **Export subscriptions**
4. Save the file
5. Move to `data/podcasts.opml`

## Manual OPML Creation

If you only have a few podcasts, you can create the file manually:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>My Podcasts</title>
  </head>
  <body>
    <outline text="Podcasts" title="Podcasts">
      <outline type="rss" text="Podcast Name" xmlUrl="RSS_FEED_URL_HERE" />
      <!-- Add more podcasts here -->
    </outline>
  </body>
</opml>
```

To find RSS feed URLs:
1. Go to the podcast's website
2. Look for "RSS" or "Subscribe" links
3. Copy the RSS feed URL (usually starts with https://)

## Example

See `data/podcasts.opml.example` for a sample file with 3 podcasts.
