# Release 1.1 verification

The implementation adds recoverable skill resolution, reused-skill integrity checks, a 74-entry catalog, native-host evidence records and three managed tool integrations. Installation, native discovery, authentication, hook trust and actual execution are separate results.

The release rollout record will be populated from actual commands and native observations. Existing release 1.0 records remain historical evidence for their tested revisions.

Browser fixtures include a clean page and deliberate width, readability, accessible-name and interaction defects. CLI screenshots and measurements are retained with original CLI video. Original frame inspection found scaling limitations after resizing, so separate matching-viewport Playwright recordings provide readable evidence. Wall elapsed action times are not assumed equal to video presentation timestamps; inspected frame mappings bind exact video and image hashes.

Run the fixture server in one terminal:

```sh
python3 -m http.server 45021 --bind 127.0.0.1 --directory tests/fixtures/browser
```

Then capture with the installed pinned CLI:

```sh
python3 scripts/check-browser-fixtures.py --output /tmp/browser-review --session workflow-review
node scripts/record-browser-fallback.mjs --runtime /path/to/managed/playwright-runtime --output /tmp/browser-review --url http://127.0.0.1:45021
```

The fixture script reports expected failures for the deliberately broken variant; a successful capture alone does not establish visual acceptance. Independently inspect source frames, screenshots, interaction results and the adopted design before accepting evidence.
