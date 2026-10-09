# Privacy Policy

The TubeText plugin for Dify runs TubeText Actors on the Apify platform with the user's own Apify API token.

## Data collection and storage

- The plugin does not collect, store or log user data. It keeps no database, files or cache.
- Your Apify API token is stored by Dify as an encrypted tool credential. The plugin only uses it to call the Apify API and never writes it to logs, results or error messages.

## Data sent to third parties

- Tool inputs (TikTok Shop links, AliExpress search terms, YouTube or TikTok video links and the selected options) are sent to the Apify API (`api.apify.com`) to start an Actor run on your Apify account. Apify processes them under the [Apify Privacy Policy](https://apify.com/privacy-policy).
- Results are read from that run's Apify dataset and returned to your Dify workflow or agent. They stay in your Apify account according to your Apify data retention settings.
- No other third party receives data from the plugin.

## Personal data

The Actors return public product and video data only. They do not log in to any site and do not use cookies. TikTok Shop reviews never include reviewer names or IDs.

## Contact

Questions about this policy: open an issue in the plugin's source repository.
