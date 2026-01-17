# CI quick notes (Pack 7)

* Coverage gate: **95%** for unit tests (`-m 'not integration'`).
* Integration tests run only if `API` env is provided (e.g., your Render URL).
* Add a GitHub secret `RENDER_API_BASE` like `https://valhalla-api-ha6a.onrender.com` to enable perf smoke.
* Dev deps are in `requirements-dev.txt`.
