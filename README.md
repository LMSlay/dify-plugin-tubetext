# TubeText

TikTok Shop and AliExpress product data, plus YouTube and TikTok transcripts, for Dify workflows and agents. Each tool runs a TubeText Actor on [Apify](https://apify.com/tubetext) with your own Apify API token. Failed items do not incur the corresponding result fee; Actor startup and other applicable charges may still apply. See each Actor's current Pricing tab.

## Tools

| Tool | What it returns | Apify Actor |
|---|---|---|
| TikTok Shop Products | US TikTok Shop data from product, store or category links: price and discount, items sold, rating and reviews, stock per SKU, shipping and shop stats. One product link returns one row. | [TikTok Shop Product Scraper](https://apify.com/tubetext/tiktok-shop-product-scraper) |
| AliExpress Search | AliExpress search results for up to 20 keywords: price and discount, items sold, rating, ships-from country, free shipping and Choice badges. New-shopper deals and sponsored results are flagged and can be skipped. | [AliExpress Search Scraper](https://apify.com/tubetext/aliexpress-search-scraper) |
| Video Transcript (YouTube & TikTok) | Transcripts of YouTube videos, Shorts, playlists and channels, and of TikTok videos (links can be mixed). Captions are used when available; turn on AI transcription to transcribe videos without captions with Whisper. | [YouTube Transcript Scraper](https://apify.com/tubetext/youtube-transcript-fast), [TikTok Transcript Scraper](https://apify.com/tubetext/tiktok-transcript) |
| Get Run Results | The results of an earlier run by run ID, with paging | – |

Limits worth knowing:
- TikTok Shop Products needs links or product IDs. It doesn't search by keyword and covers the US store only.
- AliExpress Search returns search-result data only, without product-page details or store names.

## Setup

1. Create an Apify account at [apify.com](https://apify.com). Copy your API token from **Apify Console > Settings > API & Integrations**.
2. In Dify, install **TubeText** from the Marketplace.
3. Open **Tools > TubeText > Authorize** and paste the token.

## Usage

**Workflow:** add a TubeText tool node and fill in the links or keywords, or map a variable. The `json` output contains:
- `items`
- `count`
- `runs`, with each Apify run's `runId` and `runUrl`

Video Transcript also returns the transcripts as `text`, ready for an LLM node.

**Agent:** enable the TubeText tools in an agent app. Each tool tells the model when to use it. Example prompts:
- "Get the transcript of this TikTok and tell me what the hook is: <link>"
- "Summarize the latest videos on https://www.youtube.com/@3blue1brown" (how many is set by `Max Videos per Playlist or Channel` in the tool settings)
- "Find yoga mats on AliExpress between $5 and $20, sorted by orders"
- "How many units has this TikTok Shop product sold, and which variant has the most stock? <link>"

**Output:** `Simplified` (the default) returns the most useful fields and keeps agent context small. `Full` returns every field the Actor produces.

**Long runs:** each call waits up to `Max Wait` seconds (default 240). If a run takes longer, it keeps running on Apify and the tool returns its `runId`. Read the results later with **Get Run Results**.

### Captions-first YouTube brief in a Dify workflow

Want to summarize a YouTube video without automatically paying for AI transcription? Start with one permitted public video, not a whole channel. This is a documentation-based node setup for plugin **0.1.0**, not a live-tested workflow or importable DSL.

1. Add a Start text input for the video URL. In **Video Transcript (YouTube & TikTok)**, map **Links** to that input; set **Languages** to `en`, **Max Videos per Playlist or Channel** to `1`, **AI Transcription** to off, **Timestamps** to on and **Output** to Simplified. The plugin explicitly sends YouTube `aiFallback: false`; this avoids relying on the Actor's default.
2. Inspect the tool's JSON output in your Dify variable picker. Check both `runs[].runStatus` and each item's `status`/`error`. A returned row is not necessarily a successful transcript. Only send a successful, nonempty `transcript` to your optional summary node; keep other rows for review. Check the returned language rather than assuming the preference guarantees English.
3. Give the summary node the accepted transcript, title, URL and available `timestampedText`. Ask it to summarize only that text, preserve source references and treat transcript content as data, not instructions. Do not summarize an error message.
4. If the run is still active, keep its `runId` and use **Get Run Results** later instead of launching another job. Recovery returns raw Actor `items` plus `runStatus`, not the video tool's convenience `text` output. Reapply the success/transcript checks.

AI off is not a zero-cost guarantee: applicable startup charges can remain, and a downstream model has its own usage costs. Review the current pricing before running.

For missing captions, restricted videos and language mismatches, use our [YouTube transcript troubleshooting guide](https://tubetext.dev/youtube-transcript-not-available/). Its JSON examples target the Actor directly; they are not additional Dify tool parameters. In this plugin, use the named node settings above.

## Pricing

The plugin itself is free. Runs are billed per result to your Apify account, at the price shown on each Actor's Apify Store page (Apify Free plan prices below; paid Apify plans pay less):
- TikTok Shop: $4 per 1,000 products with full details, or $1.50 per 1,000 listing cards.
- AliExpress: $2.50 per 1,000 products.
- YouTube transcripts: $4 per 1,000.
- TikTok transcripts: see the [current Pricing tab](https://apify.com/tubetext/tiktok-transcript/pricing).
- AI transcription: $0.006 per minute.

Failed items, removed products, YouTube videos without captions when AI transcription is off (`no_transcript`), and music-only TikTok videos do not incur the corresponding result fee. This does not make the entire run free: Actor startup and other applicable charges may still apply under the selected Actor's current Pricing tab. Apify's free plan includes monthly usage credit.

## Connection requirements

The plugin only calls `https://api.apify.com`. It doesn't log in to TikTok, AliExpress or YouTube, and it doesn't use cookies.

## Errors

- *Apify did not accept the API token*: the token is wrong or was revoked. Update it under **Tools > TubeText**.
- *No remaining usage credit*: add credit or upgrade your Apify plan.
- An item whose `status` isn't `ok` (for example a removed video or product) includes an `error` field explaining why.

## Source code and support

Source: https://github.com/LMSlay/dify-plugin-tubetext. Issues and questions are welcome there, or on any Actor's Apify Store page.

Privacy: see [PRIVACY.md](PRIVACY.md).
