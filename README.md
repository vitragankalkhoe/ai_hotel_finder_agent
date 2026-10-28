# AI Hotel Finder & Booking Agent — workshop practical

A Flask web dashboard using fictional local hotel data and your existing Groq API key for AI recommendations. It includes filters, recommendation prompts, booking estimate preview, and an explicit confirmation before saving a local demo booking.

**Important:** all hotels, photos, prices, ratings and listings are illustrative. This app does not check live availability, contact a hotel, take payment, or make a real reservation. Do not enter real customer data. This is a single-user educational prototype, not a production booking platform.

## Windows setup
1. Extract the ZIP and open the `ai_hotel_finder_agent` folder in VS Code.
2. In terminal run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`. Paste your existing Groq API key into `GROQ_API_KEY=`. Keep `.env` private. If the key is blank, browsing, filters and local demo bookings still work; AI recommendations are disabled.
4. Run:
   ```bat
   python app.py
   ```
5. Open `http://127.0.0.1:5000` in your browser.

## Demo flow
- Filter stays by destination, budget, rating and guests.
- Ask the AI: `A family-friendly hotel in Goa under ₹7000 per night with a pool and breakfast.`
- Click **Choose stay**, select dates, then **Preview booking**.
- Review the estimate, enter demo guest details, tick the checkbox, and click **Confirm demo booking**.
- Confirm the browser confirmation dialog. The record is saved to `bookings.json`.

`hotels.json` contains fictional hotel data. `bookings.json` is created after explicit confirmation. The `/api/bookings` endpoint is for local demo inspection only and has no authentication.

## Production gaps
Before real use, add authentication, CSRF protection, HTTPS, a database with transactional writes, privacy controls, and an authorized hotel inventory/booking provider. Never present demo prices or ratings as real.
