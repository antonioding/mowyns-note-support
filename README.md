# Mowyns Note support

Independent static support and privacy website for Mowyns Note, in Simplified Chinese, Traditional Chinese, English, Spanish, German, French, Russian, Japanese, Korean, Turkish and Italian.

Published from main:/docs at https://antonioding.github.io/mowyns-note-support/. Native app screenshots use fictional demonstration notes. The Duo opening images are unretouched simulator captures. No analytics, account system, remote scripts, external fonts or personal review contact details are included. Feedback is handled by this repository’s Issues.

The dated wireless-data notice is maintained in `content/network-permission-notice.json` for all 11 languages. It records the current investigation limits, the Apple forum reference, an apology, and guidance for version 1.0.39. Update the content and regenerate all pages with:

```sh
python3 script/network_notice.py --site-dir docs --notice-file content/network-permission-notice.json
python3 script/network_notice.py --site-dir docs --notice-file content/network-permission-notice.json --check
python3 -m unittest discover -s script -p 'test_*.py' -v
```

Keep this notice data and renderer in sync with the app repository's `script/app-store/` copies so a full site regeneration preserves the disclosure. The generator preserves the existing policy text and screenshots; the notice has its own update date and does not claim a verified fix.
