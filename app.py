import os, json, uuid
from datetime import datetime, date
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
try:
    from groq import Groq
except ImportError:
    Groq = None

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')
app = Flask(__name__)
HOTELS_FILE, BOOKINGS_FILE = BASE/'hotels.json', BASE/'bookings.json'
API_KEY = os.getenv('GROQ_API_KEY', '').strip()
MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
with open(HOTELS_FILE, encoding='utf-8') as f:
    HOTELS = json.load(f)

def read_bookings():
    if not BOOKINGS_FILE.exists(): return []
    try:
        with open(BOOKINGS_FILE, encoding='utf-8') as f: return json.load(f)
    except (OSError, json.JSONDecodeError): return []

def write_bookings(rows):
    tmp = BOOKINGS_FILE.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(rows, f, indent=2, ensure_ascii=False)
    tmp.replace(BOOKINGS_FILE)

def find_hotel(hotel_id):
    return next((h for h in HOTELS if h['id'] == hotel_id), None)

@app.get('/')
def index():
    return render_template('index.html', hotels=HOTELS, today=date.today().isoformat(), groq_enabled=bool(API_KEY and Groq))

@app.get('/api/hotels')
def filter_hotels():
    city = request.args.get('city', '').strip().lower()
    try:
        budget = float(request.args['max_price']) if request.args.get('max_price') else None
        rating = float(request.args['min_rating']) if request.args.get('min_rating') else None
        guests = max(1, min(int(request.args.get('guests', '1')), 12))
    except ValueError: return jsonify(error='Invalid filter value.'), 400
    rows = [h for h in HOTELS if (not city or city in h['city'].lower()) and (budget is None or h['price_per_night'] <= budget) and (rating is None or h['rating'] >= rating) and guests <= h['max_guests']]
    rows.sort(key=lambda h: (-h['rating'], h['price_per_night']))
    return jsonify(hotels=rows, count=len(rows))

@app.post('/api/recommend')
def recommend():
    data = request.get_json(silent=True) or {}
    preferences = str(data.get('preferences', '')).strip()
    if not preferences: return jsonify(error='Describe your ideal stay first.'), 400
    if not (API_KEY and Groq):
        return jsonify(recommendation='Groq is not configured. Browse the local demo listings and use the filters. Add GROQ_API_KEY to .env to enable AI recommendations.', ai_enabled=False)
    try:
        client = Groq(api_key=API_KEY)
        safe_hotels = [{k:h[k] for k in ('id','name','city','price_per_night','rating','category','amenities','description','max_guests')} for h in HOTELS]
        response = client.chat.completions.create(
            model=MODEL, temperature=0.2, max_completion_tokens=700,
            messages=[
                {'role':'system','content':'You are a hotel recommendation assistant for a student demo. Recommend only hotels in the supplied local data. These are fictional demo records: never claim real availability, verified ratings, or live prices. Explain 2-3 matches with name, city, demo price and reasons. Never create or confirm a booking.'},
                {'role':'user','content':'Customer preferences:\n'+preferences+'\n\nLocal fictional hotel data:\n'+json.dumps(safe_hotels, ensure_ascii=False)}
            ])
        return jsonify(recommendation=response.choices[0].message.content or 'No recommendation returned.', ai_enabled=True)
    except Exception as e:
        return jsonify(recommendation='Groq is temporarily unavailable. You can still browse and book demo records. Details: '+str(e), ai_enabled=False)

def calculate_preview(data):
    hotel = find_hotel(str(data.get('hotel_id','')))
    if not hotel: return None, 'Select a valid hotel.'
    try:
        checkin, checkout = date.fromisoformat(str(data.get('check_in',''))), date.fromisoformat(str(data.get('check_out','')))
        guests = int(data.get('guests', 1))
    except (ValueError, TypeError): return None, 'Enter valid dates and guest count.'
    if checkin < date.today(): return None, 'Check-in cannot be in the past.'
    if checkout <= checkin: return None, 'Check-out must be after check-in.'
    if guests < 1 or guests > hotel['max_guests']: return None, f"This demo listing supports 1 to {hotel['max_guests']} guests."
    nights = (checkout-checkin).days
    subtotal = nights * hotel['price_per_night']
    taxes = round(subtotal * 0.12)
    return {'hotel':hotel, 'check_in':checkin.isoformat(), 'check_out':checkout.isoformat(), 'guests':guests, 'nights':nights, 'subtotal':subtotal, 'taxes':taxes, 'total':subtotal+taxes}, None

@app.post('/api/booking-preview')
def booking_preview():
    preview, error = calculate_preview(request.get_json(silent=True) or {})
    return (jsonify(error=error), 400) if error else jsonify(preview)

@app.post('/api/bookings')
def create_booking():
    data = request.get_json(silent=True) or {}
    if data.get('confirmed') is not True: return jsonify(error='Explicit confirmation is required.'), 400
    name, email = str(data.get('guest_name','')).strip(), str(data.get('guest_email','')).strip()
    if len(name) < 2: return jsonify(error='Enter the guest name.'), 400
    if '@' not in email or '.' not in email.rsplit('@',1)[-1]: return jsonify(error='Enter a valid email address.'), 400
    preview, error = calculate_preview(data)
    if error: return jsonify(error=error), 400
    h = preview['hotel']
    booking = {'booking_id':'DEMO-'+uuid.uuid4().hex[:8].upper(), 'created_at':datetime.now().astimezone().isoformat(timespec='seconds'), 'hotel_id':h['id'], 'hotel_name':h['name'], 'city':h['city'], 'guest_name':name, 'guest_email':email, 'check_in':preview['check_in'], 'check_out':preview['check_out'], 'guests':preview['guests'], 'nights':preview['nights'], 'total_estimate':preview['total'], 'status':'DEMO_BOOKING_CONFIRMED', 'notice':'Local workshop demo only. No real reservation or payment was made.'}
    rows = read_bookings(); rows.append(booking); write_bookings(rows)
    return jsonify(message='Demo booking saved successfully.', booking=booking, notice=booking['notice']), 201

@app.get('/api/bookings')
def bookings():
    return jsonify(bookings=read_bookings())

if __name__ == '__main__':
    print('AI HOTEL FINDER & BOOKING AGENT — local demo only')
    print('Groq AI enabled.' if API_KEY and Groq else 'Groq not configured; browsing and demo booking still work.')
    app.run(host='127.0.0.1', port=5000, debug=True)
