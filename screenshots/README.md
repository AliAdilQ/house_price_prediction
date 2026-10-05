# Genuine application screenshots

The committed images are real captures of the running, trained, seeded Django application at 1440 × 1000 desktop viewport (full-page captures) and 375 × 900 mobile viewport.

| Image | Page |
| --- | --- |
| `home-page.png` | `/` — hero, actual metrics, neighborhood chart, and features |
| `prediction-page.png` | `/predict/` — complete form with sample property details |
| `result-page.png` | `/result/<uuid>/` — genuine model output after form submission |
| `history-page.png` | `/history/` — stored estimates, filters, and pagination |
| `admin-dashboard.png` | `/admin/` — authenticated demo administration dashboard |
| `about-page.png` | `/about/` — pipeline explanation and actual model comparison |
| `mobile-home.png` | `/` at 375 px — responsive landing page |
| `mobile-prediction.png` | `/predict/` at 375 px — responsive form |

To regenerate them, initialize/train/seed the project as described in the root README, and start `python manage.py runserver` in one terminal. Install the optional browser tooling in another terminal:

```bash
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node scripts/capture_screenshots.cjs
```

Node.js and Playwright are development-only screenshot tools, not dependencies of the Django application. `node_modules/` is ignored.

The script only operates on localhost. It submits one new synthetic prediction, checks invalid input constraints, signs in with the demo credentials, checks desktop/tablet/mobile layouts, verifies the chart, and saves the images. It expects the original demo password; update the local capture script if you have changed that password.

Optional environment variables: `APP_URL` for a different localhost port, and `BROWSER_EXECUTABLE` for an installed Chrome/Chromium executable. Manual capture is also possible using browser screenshots of the routes above after creating a valid estimate and signing into admin.
