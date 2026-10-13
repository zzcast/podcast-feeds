# podcast-feeds
Custom RSS feeds for Overcast

GitHub Actions runs `update_feeds.py` three times a day (`.github/workflows/update-feeds.yml`)
and commits any changed `*.xml`. To update now, run it from the Actions tab
(`workflow_dispatch`). Before changing the generator or a PNG locally, `git pull`,
then re-run `python3 update_feeds.py` and commit its output with your change.
`trudno-byt-bogom.xml` is maintained by hand and is not generated.
