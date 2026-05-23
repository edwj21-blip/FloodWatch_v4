# 🌊 FloodWatch Kerala v4 — with Live Weather API

## New in v4
- **Portal Landing Page** (`/portal/`) — users choose Public or Admin portal
- **OpenWeatherMap API integration** — live rainfall, temperature, humidity per location
- **Auto water level updates** — rainfall → water rise calculation, auto-status update
- **Rainfall accuracy %** — computed from rain intensity + humidity + weather type
- **Auto-generated flood alerts** — when status hits DANGER/CRITICAL
- **Admin weather sync** — button in admin dashboard + every 5 min auto-sync
- **New API endpoints** — `/api/water-levels/` and `/api/weather-status/`
- **Login required** — all pages require login; unauthenticated → portal page

---

## Setup

```bash
pip install Django Pillow
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Open: https://floodwatch-v4.onrender.com
---

## OpenWeatherMap API (FREE)

1. Register at https://openweathermap.org/api (free tier = 1000 calls/day)
2. Copy your API key
3. In `floodwatch/settings.py`, replace:
   ```python
   OPENWEATHER_API_KEY = 'YOUR_OPENWEATHER_API_KEY_HERE'
   ```
   with your actual key.

**Without a key:** The system uses realistic Kerala monsoon simulation (rotates hourly per district). It still works perfectly for testing.

---

## Auto Weather Sync

### Option A — Management Command (recommended for production)
```bash
# Run once
python manage.py sync_weather

# Run every 5 minutes continuously
python manage.py sync_weather --loop 300
```

### Option B — Admin UI
Log in as admin → click **"🌧️ Sync Weather & Water Levels"** button.  
The admin dashboard also auto-syncs every 5 minutes via JavaScript.

### Option C — Cron (Linux/Mac)
```bash
# Add to crontab -e
*/10 * * * * cd /path/to/floodwatch_new && python manage.py sync_weather
```

---

## Portal Flow

```
/portal/          → Landing page (choose portal)
  ├── /login/     → Login page
  ├── /register/  → Register page
  └── After login:
      ├── User  → / (Dashboard)
      └── Admin → /admin-reports/ (Admin Dashboard)
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/water-levels/` | All water levels with weather data |
| `GET /api/weather-status/` | Summary counts + avg rainfall |
| `GET /admin/sync-weather/` | Trigger sync (admin only) |
