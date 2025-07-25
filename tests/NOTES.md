# Our URL Shortener: The Essentials

## How It Works
* **Shortening:** We use a simple in-memory dictionary and generate random 6-character alphanumeric codes. It's fast and easy, perfect for an in-memory setup.
* **Data Flow:**
    * **Shorten (`POST /api/shorten`):** Send a long URL; we validate, generate/find a short code, and save it.
    * **Visit (`GET /<short_code>`):** Click a short link; we look it up, count the click, and redirect you.
    * **Stats (`GET /api/stats/<short_code>`):** Ask for a short code's stats; we'll show you the original URL, clicks, and creation time.

## Keeping It Smooth
* **Thread Safety (`db_lock`):** Our `threading.Lock` (`db_lock`) acts like a turnstile, letting only one operation modify our URL data at a time. This prevents data mix-ups during busy periods.
* **Why Short Code as Key:** We use the short code as the main lookup key because we expect way more "reads" (redirects, stats checks) than "writes" (new short links). This makes lookups super fast!

## AI's Role
* **Gemini:** Gemini was my go-to for creating detailed test cases and for learning more about Flask APIs and Python.