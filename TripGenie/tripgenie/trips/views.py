import os, json, re, json5
import requests
from urllib.parse import quote_plus
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from groq import Groq
from .models import Trip, Wishlist, Itinerary, ItineraryDay, Activity
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from budget.models import Budget, Expense
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Clear session data when user logs out"""
    print(f"User logged out: {user.username if user else 'Unknown'}")
    try:
        # Clear all recommendation-related session data
        request.session['ai_trips'] = []
        request.session['last_user_id'] = None
        # Ensure changes are saved
        request.session.modified = True
        print("Successfully cleared session data on logout")
    except Exception as e:
        print(f"Error clearing session data: {str(e)}")
    
    # Force session to be saved
    request.session.save()


# Initialize Groq client
client = Groq(api_key=settings.GROQ_API_KEY)


@login_required(login_url='/login')
def recommendations(request):
    if request.method == "GET":
        # Always check if the user has changed
        current_user_id = str(request.user.id)
        last_user_id = request.session.get('last_user_id')
        
        # Clear recommendations if this is a different user or first login
        if last_user_id != current_user_id:
            print(f"Clearing recommendations - User changed from {last_user_id} to {current_user_id}")
            request.session['ai_trips'] = []
            request.session['last_user_id'] = current_user_id
            request.session.modified = True
            
        # Clear recommendations if requested
        if request.GET.get('clear') == 'true':
            print("Clearing recommendations - Requested via URL")
            request.session['ai_trips'] = []
            request.session.modified = True
            
        # Get existing recommendations (will be empty if just cleared)
        existing_recommendations = request.session.get('ai_trips', [])
        
        context = {
            'existing_recommendations': json.dumps(existing_recommendations),
            'has_recommendations': bool(existing_recommendations)
        }
        return render(request, "recommendation.html", context)
    return HttpResponseBadRequest("Method not allowed")



@login_required(login_url='/login')
@require_POST
def generate_recommendations(request):
    import re, ast, json
    try:
        payload = json.loads(request.body.decode("utf-8"))
        
        prompt = f"""
            You are TripGenie, an AI travel planner that designs *complete, realistic* trip packages.

            Based on the user's preferences:
            - Destination: {payload.get('destination', 'Any')}
            - Budget: {payload.get('budget', 'Any')}
            - Duration: {payload.get('duration', 'Any')}
            - Travelers: {payload.get('travelers', 'Solo')}
            - Interests: {', '.join(payload.get('interests', []))}

            Your task:
            Now generate 9-12 *unique and diverse* travel packages that match the user’s style.
            Each package must be **completely distinct** — destinations, activities, cost, and itinerary details should NOT repeat across trips.

            For each trip:
            - Personalize it to match the traveler type and budget.
            - The duration (number of days) must reflect what the user selected.
                Example:
                "Weekend" → 2-3 days
                "1 Week" → 6-8 days
                "2 Weeks" → 12-15 days
                "1 Month+" → 28-32 days

            Generate 9-12 travel *packages*.
            Each package must be detailed and complete, following this structure exactly (JSON array only): 
            {{
            Each package should include:
            - "name": Short unique package name,
            - "country": Country name,
            - "image": A relevant direct image URL (preferably from Google Images / Google Custom Search). If a direct image link cannot be provided, include a separate field "google_query" with short search terms so the server can fetch an image. Example: {{"image": "https://example.com/paris.jpg", "google_query": "paris travel sunset"}},
            - "price": integer (Approx total package cost in ₹),
            - "duration_days": Integer,
            - "description": Short overview (2-3 sentences),
            - "highlights": Top experiences (list of 3-5),
            - "best_time": Best months to visit,
            - "rating": Number (4.0-5.0),
            - "match_score": AI match %,
            - "itinerary": {{
              "Day 1": "Activity",
              "Day 2": "Activity",
              ...
              (One unique entry for each day, according to duration_days)
              }},
            - "inclusions": ["Accomodation", "Sightseeing", "Meals", "Transfers", "Transport"],
            - "exclusions": ["Airfare", "Personal expenses", "Shopping"],
            - "tips": 3-line useful travel tip
            - "cost_breakdown": {{
                "hotels": 40000,
                "meals": 12000,
                "activities": 15000,
                "transport": 8000,
                "misc": 5000
                }},
            - "hotels": [
                {{"name": "The Anvaya Beach Resort", "location": "Kuta", "price_per_night": 12000, "rating": 4.7}},
                {{"name": "Alaya Resort Ubud", "location": "Ubud", "price_per_night": 9500, "rating": 4.5}},
                {{"name": "Legian Beach Hotel", "location": "Legian", "price_per_night": 10500, "rating": 4.4}}
                ],
            - "restaurants": [
                {{"name": "Mamasan Bali", "cuisine": "Asian Fusion", "avg_cost": 1800, "location": "Seminyak"}},
                {{"name": "La Lucciola", "cuisine": "Italian", "avg_cost": 2200, "location": "Petitenget"}},
                {{"name": "Warung Babi Guling Pak Malen", "cuisine": "Balinese", "avg_cost": 1000, "location": "Kuta"}}
                ],
            - "local_transport": [
                {{"type": "Airport Transfer", "provider": "Istanbul Shuttle", "cost": 2000, "mode": "Car"}},
                {{"type": "City Sightseeing Tour", "provider": "Turkish Explorer Bus", "cost": 3500, "mode": "Bus"}},
                {{"type": "Intercity Travel", "provider": "Turkish Airlines (Domestic)", "cost": 8000, "mode": "Flight"}}
                ],
            }}

            📋 Rules:
            - Always generate one unique itinerary per trip (no duplicate days).
            - Ensure total cost ≈ sum of cost_breakdown values.
            - Match traveler type (family-friendly, romantic, group-oriented, etc.).
            - Use INR for all costs.
            - Return a complete, valid JSON array of trip objects. Do not truncate or summarize the output. Only return JSON.(no explanation or text outside the array)
        """


        # Call Groq API with optimized parameters for multiple packages
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {
                    "role": "system", 
                    "content": "You are a precise travel expert AI that responds ONLY in valid JSON. Each package must be complete with all fields. No truncation or omission.",
                    },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Further reduced temperature for more reliable output
            max_tokens=12000,  # Significantly increased token limit
            top_p=0.9,  # Added top_p to help with completion reliability
        )

        content = completion.choices[0].message.content.strip()
        print("\n🧠 Raw AI Response:\n", content[:5000], "...\n")

        # --- Clean & repair malformed JSON ---
        
        # Remove code blocks and normalize content
        content = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', content, flags=re.DOTALL)
        content = content.strip()
        
        # Print the raw content length and preview
        print(f"📏 Raw content length: {len(content)} characters")
        print("📄 Content preview (first 500 chars):", content[:500])
        print("📄 Content end (last 500 chars):", content[-500:])
        
        # Remove any trailing ellipsis or incomplete content
        content = re.sub(r'\.\.\.\s*$', '', content)
        
        # Try to extract complete JSON array with improved regex
        match = re.search(r'\[\s*(\{(?:(?:[^{}]|(?:\{[^{}]*\}))*)\}(?:\s*,\s*\{(?:(?:[^{}]|(?:\{[^{}]*\}))*)\})*)\s*\]', content, re.DOTALL | re.MULTILINE)
        if match:
            content = f"[{match.group(1)}]"
            print("✅ Successfully extracted JSON array")
            # Print preview of each object to verify extraction
            objects = re.findall(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', content)
            print(f"Found {len(objects)} objects in array")
            for i, obj in enumerate(objects[:3], 1):  # Show first 3 objects
                name = re.search(r'"name":\s*"([^"]+)"', obj)
                print(f"Object {i}: {name.group(1) if name else 'Unknown'}")
        else:
                # Try to find individual objects with improved regex
            objects = re.findall(r'\{(?:[^{}]*(?:\{[^{}]*\})*[^{}]*)*\}', content)
            if objects:
                print(f"📦 Found {len(objects)} potential trip objects")
                # Debug print first few characters of each object
                for i, obj in enumerate(objects):
                    print(f"Object {i + 1} preview: {obj[:100]}...")
                content = "[" + ",".join(objects) + "]"
                print("🔄 Combined objects into array")
            else:
                print("❌ No valid JSON objects found in response")
                return JsonResponse({"destinations": [], "message": "Invalid response format"})        # Fix common JSON issues
        content = re.sub(r',(\s*[}\]])', r'\1', content)  # Remove trailing commas
        content = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)  # Quote unquoted keys
        content = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r':"\1"\2', content)  # Quote unquoted string values
        content = re.sub(r':\s*\'([^\']*)\'\s*([,}])', r':"\1"\2', content)  # Convert single to double quotes
        content = re.sub(r'\\(?!["\\/bfnrtu])', '', content)  # Remove invalid escapes
        
        # Balance brackets/braces using a stack
        def balance_brackets(s):
            stack = []
            brackets = {'{': '}', '[': ']'}
            balanced = []
            
            for char in s:
                if char in '{[':
                    stack.append(char)
                    balanced.append(char)
                elif char in '}]':
                    if stack and brackets[stack[-1]] == char:
                        stack.pop()
                        balanced.append(char)
                    # Skip unmatched closing brackets
                else:
                    balanced.append(char)
            
            # Close any remaining open brackets
            while stack:
                balanced.append(brackets[stack.pop()])
            
            return ''.join(balanced)
        
        content = balance_brackets(content)
        
        # Ensure it's a valid array
        if not content.startswith('['):
            content = '[' + content
        if not content.endswith(']'):
            content = content + ']'

                # --- Attempt to parse JSON safely ---
        try:
            destinations = json.loads(content)
        except json.JSONDecodeError as err:
            print("⚠️ JSON Decode failed:", err)
            print("Attempting recovery...")

            # Try JSON5 (handles trailing commas, unquoted keys, etc.)
            try:
                destinations = json5.loads(content)
                print("✅ Recovered using JSON5")
            except Exception:
                # Fallback 1: cut off incomplete tail
                cutoff = content.rfind("}")
                if cutoff != -1:
                    truncated = content[:cutoff+1] + "]"
                    try:
                        destinations = json.loads(truncated)
                        print("✅ Recovered by truncating incomplete JSON tail")
                    except Exception:
                        # Fallback 2: final soft repair
                        fixed = content.replace("'", '"')
                        fixed = re.sub(r',\s*([\]}])', r'\1', fixed)
                        fixed = re.sub(r'\\(?!["\\/bfnrtu])', '', fixed)  # fix bad escapes
                        try:
                            destinations = json.loads(fixed)
                            print("✅ Recovered with lenient cleanup")
                        except Exception as inner_err:
                            print("❌ Final JSON parse failed:", inner_err)
                            destinations = []

        # --- Validate & finalize ---
        if not isinstance(destinations, list):
            destinations = [destinations]

        if not destinations:
            print("⚠️ No destinations generated")
            return JsonResponse({"destinations": [], "message": "No destinations found"})

        # Print the parsed destinations for debugging
        print(f"🎯 Number of parsed destinations: {len(destinations)}")
        
        # Validate each destination has required fields
        valid_destinations = []
        for i, trip in enumerate(destinations):
            try:
                print(f"\n📝 Validating trip {i + 1}: {trip.get('name', 'Unknown')}")
                
                # Convert price to proper format if needed
                if isinstance(trip.get('price'), (int, float)):
                    trip['price'] = f"₹{trip['price']:,.2f}"
                elif isinstance(trip.get('price'), str):
                    # Clean up price string
                    price_str = trip['price'].replace('₹', '').replace(',', '')
                    try:
                        price_float = float(price_str)
                        trip['price'] = f"₹{price_float:,.2f}"
                    except ValueError:
                        trip['price'] = "₹0.00"

                # Ensure duration_days is a number
                if isinstance(trip.get('duration_days'), str):
                    try:
                        trip['duration_days'] = int(trip['duration_days'])
                    except ValueError:
                        trip['duration_days'] = 0

                # Set default values for optional fields
                trip.setdefault('highlights', [])
                trip.setdefault('description', '')
                trip.setdefault('best_time', '')
                trip.setdefault('rating', 4.5)
                trip.setdefault('match_score', 80)

                # Validate required fields
                required_fields = {
                    "name": (str, "Unknown Destination"),
                    "country": (str, "Various Countries"),
                    "price": (str, "₹0.00"),
                    "duration_days": ((int, float), 0),
                    "description": (str, "No description available"),
                }

                # Ensure all required fields exist with correct types
                for field, (field_type, default_value) in required_fields.items():
                    if not isinstance(trip.get(field), field_type):
                        trip[field] = default_value

                trip["id"] = str(i + 1)
                valid_destinations.append(trip)

                # --- Normalize duration and fill missing days if needed ---
                for trip in valid_destinations:
                    duration = trip.get("duration_days", 0)
                    if duration and "itinerary" in trip:
                        itin = trip["itinerary"]
                        # if AI produced fewer days, auto-fill missing
                        if len(itin) < duration:
                            for d in range(len(itin) + 1, duration + 1):
                                itin[f"Day {d}"] = f"Free exploration or leisure day in {trip.get('country', 'destination')}"
                        trip["itinerary"] = itin

                
            except Exception as e:
                print(f"⚠️ Error processing destination {i + 1}: {str(e)}")
                print(f"Problematic trip data: {json.dumps(trip, indent=2)}")
                # Try to salvage what we can from the trip data
                try:
                    salvaged_trip = {
                        "name": trip.get('name', f"Trip {i + 1}"),
                        "country": trip.get('country', 'Unknown'),
                        "price": trip.get('price', '₹0.00'),
                        "duration_days": int(trip.get('duration_days', 0)),
                        "description": trip.get('description', ''),
                        "highlights": trip.get('highlights', []),
                        "image": trip.get('image', ''),
                        "best_time": trip.get('best_time', ''),
                        "rating": float(trip.get('rating', 4.5)),
                        "match_score": int(trip.get('match_score', 80)),
                        "id": str(i + 1)
                    }
                    valid_destinations.append(salvaged_trip)
                    print(f"✅ Salvaged basic information from trip {i + 1}")
                except Exception as inner_e:
                    print(f"❌ Could not salvage trip {i + 1}: {str(inner_e)}")
                continue

        print(f"✅ Validated {len(valid_destinations)} destinations")
        # Ensure package names are unique (append suffix if duplicates)
        seen_names = set()
        for trip in valid_destinations:
            name = (trip.get('name') or 'Package').strip()
            original = name
            count = 1
            while name in seen_names:
                count += 1
                name = f"{original} ({count})"
            seen_names.add(name)
            trip['name'] = name

        # --- Image fallback: Prefer direct image links; optionally use Google CSE if configured ---
        def fetch_google_image(query):
            """Try Google Custom Search Image API if configured, otherwise return a google images search URL or a placeholder.

            Requires settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_CX to perform a real image lookup.
            """
            api_key = getattr(settings, 'GOOGLE_CSE_API_KEY', None)
            cx = getattr(settings, 'GOOGLE_CSE_CX', None)
            safe_query = quote_plus(query or '')

            # If API keys are present, try the Custom Search API
            if api_key and cx:
                try:
                    url = (
                        f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}"
                        f"&q={safe_query}&searchType=image&num=1"
                    )
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get('items') or []
                        if items:
                            link = items[0].get('link')
                            if link:
                                return link
                except Exception as e:
                    print(f"⚠️ Google CSE lookup failed: {e}")

            # Fallback: return a Google Images search page (not a direct image) so user can open it
            if safe_query:
                return f"https://www.google.com/search?tbm=isch&q={safe_query}"

            # Last resort: a generic placeholder image (loremflickr)
            return f"https://loremflickr.com/600/400/travel"

        # Apply image fallback for trips that didn't include an image
        for trip in valid_destinations:
            img = trip.get('image') or ''
            # If empty or non-useful, try to fetch via google or use query
            if not img or str(img).strip() == '':
                # Prefer an explicit google_query if provided by the model
                gq = trip.get('google_query') or trip.get('name') or trip.get('country') or ''
                try:
                    img_url = fetch_google_image(gq)
                    trip['image'] = img_url
                except Exception as e:
                    print(f"⚠️ Image fallback failed for '{trip.get('name')}': {e}")

        # Parse numeric price for each trip and store temporarily for filtering
        for trip in valid_destinations:
            price_raw = trip.get('price', 0)
            num_price = 0.0
            try:
                if isinstance(price_raw, (int, float)):
                    num_price = float(price_raw)
                else:
                    s = str(price_raw)
                    # strip common currency tokens and text
                    s_clean = s.replace('₹', '').replace('Rs.', '').replace('INR', '')
                    m = re.search(r'([\d,]+(?:\.\d+)?)', s_clean)
                    if m:
                        num_price = float(m.group(1).replace(',', ''))
            except Exception:
                num_price = 0.0
            trip['_numeric_price'] = num_price

        # Determine desired budget range from payload (supports keywords and numeric ranges)
        budget_min = None
        budget_max = None
        user_budget = payload.get('budget') if payload else None
        if isinstance(payload.get('budget_min'), (int, float)):
            budget_min = float(payload.get('budget_min'))
        if isinstance(payload.get('budget_max'), (int, float)):
            budget_max = float(payload.get('budget_max'))

        if budget_min is None and budget_max is None and user_budget:
            ub = str(user_budget).lower()
            # common keyword mapping
            if 'under' in ub or 'less' in ub or 'low' in ub:
                budget_min, budget_max = 0.0, 50000.0
            elif 'mid' in ub or 'middle' in ub or ('50000' in ub and ('150000' in ub or '1,50,000' in ub)):
                budget_min, budget_max = 50000.0, 150000.0
            elif 'high' in ub or 'luxury' in ub or 'above' in ub or '>' in ub:
                budget_min, budget_max = 150000.0, float('inf')
            else:
                # try to parse numeric values out of the string
                nums = re.findall(r'[\d,]+', ub)
                nums = [int(n.replace(',', '')) for n in nums]
                if len(nums) == 1:
                    budget_min, budget_max = 0.0, float(nums[0])
                elif len(nums) >= 2:
                    a, b = nums[0], nums[1]
                    budget_min, budget_max = float(min(a, b)), float(max(a, b))

        # Apply budget filter if we have a range, else keep all
        filtered = []
        if budget_min is not None and budget_max is not None:
            for trip in valid_destinations:
                p = trip.get('_numeric_price', 0.0)
                if p >= budget_min and p <= budget_max:
                    filtered.append(trip)

            # If nothing matches exactly, fall back to lowest-priced options (prefer matching count)
            if not filtered:
                filtered = sorted(valid_destinations, key=lambda t: t.get('_numeric_price', float('inf')))[:6]
        else:
            filtered = valid_destinations

        # Clean up temporary numeric price keys
        for t in filtered:
            if '_numeric_price' in t:
                del t['_numeric_price']

        request.session["ai_trips"] = filtered
        return JsonResponse({"destinations": filtered})

    except Exception as e:
        print(f"❌ Error in generate_recommendations: {str(e)}")
        return JsonResponse(
            {
                "error": "Failed to generate recommendations",
                "details": str(e),
            },
            status=500,
        )



@login_required(login_url='/login')
def trip_details(request, trip_slug):
    try:
        # First try to get trip from the database
        db_trip = Trip.objects.get(slug=trip_slug, user=request.user)
        
        # Get itinerary and its activities
        itinerary = Itinerary.objects.filter(trip=db_trip, user=request.user).first()
        
        itinerary_data = {}
        if itinerary:
            # Get all days and their activities
            days = ItineraryDay.objects.filter(itinerary=itinerary).order_by('day_index')
            
            for day in days:
                # Get activities for this day ordered by ID to maintain sequence
                activities = Activity.objects.filter(itinerary_day=day).order_by('id')
                itinerary_data[f"Day {day.day_index}"] = [
                    activity.title for activity in activities if activity.title
                ]
        
        # Construct trip data
        trip = {
            'id': str(db_trip.id),
            'name': db_trip.name,
            'country': db_trip.country,
            'price': f"₹{db_trip.estimated_cost:,.2f}" if db_trip.estimated_cost else "Price not available",
            'duration_days': db_trip.duration,
            'description': db_trip.description,
            'image': db_trip.image_url,
            'highlights': db_trip.highlights,
            'best_time': db_trip.best_time,
            'rating': db_trip.rating,
            'match_score': db_trip.match_score,
            'inclusions': db_trip.inclusions,
            'exclusions': db_trip.exclusions,
            'tips': db_trip.travel_tips,
            'itinerary': itinerary_data if itinerary else {},
            'hotels': db_trip.hotels or [],
            'restaurants': db_trip.restaurants or [],
            'local_transport': db_trip.local_transport or [],
            'cost_breakdown': db_trip.cost_breakdown or {}
        }
        
        # Normalize local_transport items into a predictable shape for the template
        try:
            normalized_lt = []
            for item in (trip.get('local_transport') or []):
                if not isinstance(item, dict):
                    # If it's a string, turn into a simple dict
                    normalized_lt.append({'type': str(item), 'cost': 0})
                    continue
                t_type = item.get('type') or item.get('name') or item.get('details') or item.get('provider') or ''
                t_cost = item.get('cost') or item.get('estimated_cost') or item.get('price') or 0
                # ensure numeric where possible
                try:
                    t_cost = float(t_cost)
                except Exception:
                    t_cost = 0
                normalized_lt.append({'type': t_type, 'cost': t_cost})
            trip['local_transport'] = normalized_lt
        except Exception:
            trip.setdefault('local_transport', [])

        # Store the current trip in session for back navigation
        request.session['current_trip'] = trip
        # Provide flags so the template can show Export vs Save button
        context = {
            "trip": trip,
            "is_saved": bool(itinerary),
            "saved_itinerary_id": itinerary.id if itinerary else None,
        }
        return render(request, "trip_details.html", context)
        
    except Trip.DoesNotExist:
        # If the trip isn't in the DB, look in session-generated AI trips and
        # render the details without creating DB records. This prevents
        # automatic saving when a user simply views the details page.
        trips_data = request.session.get('ai_trips', [])
        try:
            # Try to find the trip by comparing slugified names
            from django.utils.text import slugify
            session_trip = next(t for t in trips_data if slugify(t['name']) == trip_slug)

            # Build a trip dict to render (same shape as DB-backed trip)
            trip = {
                'id': session_trip.get('id', '0'),
                'name': session_trip.get('name'),
                'country': session_trip.get('country', ''),
                'price': session_trip.get('price', '₹0.00'),
                'duration_days': session_trip.get('duration_days', session_trip.get('duration', 3)),
                'description': session_trip.get('description', ''),
                'image': session_trip.get('image', ''),
                'highlights': session_trip.get('highlights', []),
                'best_time': session_trip.get('best_time', ''),
                'rating': session_trip.get('rating', 4.5),
                'match_score': session_trip.get('match_score', 80),
                'inclusions': session_trip.get('inclusions', []),
                'exclusions': session_trip.get('exclusions', []),
                'tips': session_trip.get('tips', ''),
                'itinerary': session_trip.get('itinerary', {}),
                'hotels': session_trip.get('hotels', []),
                'restaurants': session_trip.get('restaurants', []),
                'local_transport': session_trip.get('local_transport', []),
                'cost_breakdown': session_trip.get('cost_breakdown', {})
            }
            # Normalize itinerary values so template loops over full activity strings
            try:
                itin = trip.get('itinerary', {}) or {}
                normalized_itin = {}
                for day, acts in itin.items():
                    if isinstance(acts, str):
                        normalized_itin[day] = [acts]
                    elif isinstance(acts, list):
                        normalized_itin[day] = acts
                    else:
                        normalized_itin[day] = [str(acts)]
                trip['itinerary'] = normalized_itin
            except Exception:
                trip.setdefault('itinerary', {})

            # Store current trip in session for back navigation / saving later
            # Normalize local_transport items into predictable shape for the template
            try:
                normalized_lt = []
                for item in (trip.get('local_transport') or []):
                    if not isinstance(item, dict):
                        normalized_lt.append({'type': str(item), 'cost': 0})
                        continue
                    t_type = item.get('type') or item.get('name') or item.get('details') or item.get('provider') or ''
                    t_cost = item.get('cost') or item.get('estimated_cost') or item.get('price') or 0
                    try:
                        t_cost = float(t_cost)
                    except Exception:
                        t_cost = 0
                    normalized_lt.append({'type': t_type, 'cost': t_cost})
                trip['local_transport'] = normalized_lt
            except Exception:
                trip.setdefault('local_transport', [])

            # Store current trip in session for back navigation / saving later
            request.session['current_trip'] = trip

            # Render the trip details WITHOUT creating DB entries. Saving must
            # be done explicitly via the Save button which calls
            # `save_trip_to_itinerary`. Provide explicit saved_itinerary_id=None
            return render(request, "trip_details.html", {"trip": trip, "is_saved": False, "saved_itinerary_id": None})

        except StopIteration:
            return render(request, "error.html", {"message": "Trip not found"})



@login_required(login_url='/login')
def itinerary_page(request):
    itineraries = Itinerary.objects.filter(user=request.user).select_related("trip")
    context = {"itineraries": itineraries}
    return render(request, "itinerary.html", context)



@login_required(login_url='/login')
@require_http_methods(["DELETE"])
def delete_trip(request, trip_id):
    try:
        # Get the trip and verify ownership
        trip = get_object_or_404(Trip, id=trip_id, user=request.user)
        
        # Delete associated records
        Itinerary.objects.filter(trip=trip).delete()
        trip.delete()
        
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)



@login_required(login_url='/login')
@require_POST
def save_trip_to_itinerary(request):
    data = json.loads(request.body.decode("utf-8"))
    trip_id = data.get("trip_id")
    
    # Get trip data from session
    trips_data = request.session.get('ai_trips', [])
    try:
        trip_data = next(t for t in trips_data if t['id'] == trip_id)
    except StopIteration:
        return JsonResponse({"status": "error", "message": "Trip not found"}, status=404)
    
    # Create or get Trip object
    # Handle price conversion
    price = trip_data.get('price', 0)
    if isinstance(price, str):
        # Remove ₹ symbol and commas if it's a string
        price = price.replace('₹', '').replace(',', '')
    estimated_cost = float(price)

    trip, created = Trip.objects.get_or_create(
        user=request.user,
        name=trip_data['name'],
        defaults={
            'country': trip_data.get('country', ''),
            'duration': trip_data.get('duration_days', 3),
            'estimated_cost': estimated_cost,
            'category': trip_data.get('category', ''),
            'image_url': trip_data.get('image', ''),
            'description': trip_data.get('description', ''),
            'inclusions': trip_data.get('inclusions', []),
            'exclusions': trip_data.get('exclusions', []),
            'highlights': trip_data.get('highlights', []),
            'best_time': trip_data.get('best_time', ''),
            'rating': float(trip_data.get('rating', 4.5)),
            'match_score': int(trip_data.get('match_score', 80)),
            'travel_tips': trip_data.get('tips', ''),
            'hotels': trip_data.get('hotels', []),
            'restaurants': trip_data.get('restaurants', []),
            'local_transport': trip_data.get('local_transport', []),
            'cost_breakdown': trip_data.get('cost_breakdown', {})
        }
    )

    # Update fields if trip already exists
    if not created:
        trip.country = trip_data.get('country', '')
        trip.duration = trip_data.get('duration_days', 3)
        trip.estimated_cost = estimated_cost
        trip.category = trip_data.get('category', '')
        trip.image_url = trip_data.get('image', '')
        trip.description = trip_data.get('description', '')
        trip.inclusions = trip_data.get('inclusions', [])
        trip.exclusions = trip_data.get('exclusions', [])
        trip.highlights = trip_data.get('highlights', [])
        trip.best_time = trip_data.get('best_time', '')
        trip.rating = float(trip_data.get('rating', 4.5))
        trip.match_score = int(trip_data.get('match_score', 80))
        trip.travel_tips = trip_data.get('tips', '')
        trip.hotels = trip_data.get('hotels', [])
        trip.restaurants = trip_data.get('restaurants', [])
        trip.local_transport = trip_data.get('local_transport', [])
        trip.cost_breakdown = trip_data.get('cost_breakdown', {})
        trip.save()

    # Create or update Itinerary
    itinerary, created_itinerary = Itinerary.objects.get_or_create(
        user=request.user,
        trip=trip,
        defaults={
            "title": trip.name,
            "total_days": trip.duration
        }
    )

    # Always update itinerary details
    itinerary.title = trip.name
    itinerary.total_days = trip.duration
    itinerary.save()

    # Clear existing itinerary days and activities
    ItineraryDay.objects.filter(itinerary=itinerary).delete()
    
    # Create or update ItineraryDays and Activities from the trip data
    if 'itinerary' in trip_data:
        print("\n📅 Creating itinerary days and activities...")
        for day, activities in trip_data['itinerary'].items():
            try:
                day_num = int(day.replace('Day ', ''))
                print(f"Creating day {day_num}")
                
                itinerary_day = ItineraryDay.objects.create(
                    itinerary=itinerary,
                    day_index=day_num,
                )
                
                # Normalize activities to a list
                if isinstance(activities, str):
                    activity_list = [activities]
                elif isinstance(activities, list):
                    activity_list = activities
                else:
                    activity_list = [str(activities)]
                
                print(f"Activities for day {day_num}: {activity_list}")
                
                # Create activities for this day
                for activity_title in activity_list:
                    if activity_title and isinstance(activity_title, str):
                        Activity.objects.create(
                            itinerary_day=itinerary_day,
                            title=activity_title.strip(),
                            description=activity_title.strip()
                        )
                        print(f"Created activity: {activity_title.strip()}")
                        
            except (ValueError, AttributeError) as e:
                print(f"Error processing day {day}: {str(e)}")
                continue  # Skip this day if there's an error but continue with others
        print("✅ Finished creating itinerary days and activities")

    # Create Budget
    estimated_cost = float(trip_data.get('price', '0').replace('₹', '').replace(',', ''))
    Budget.objects.get_or_create(
        itinerary=itinerary,
        defaults={"total_budget": estimated_cost}
    )

    return JsonResponse({
        "status": "ok",
        "redirect": reverse("itinerary")  # Redirect to itinerary page instead
    })


@login_required(login_url='/login')
def export_trip_pdf(request, trip_id):
    itinerary = get_object_or_404(Itinerary, id=trip_id, user=request.user)
    trip = itinerary.trip
    template = get_template("export_trip_pdf.html")

    # Build itinerary structure from ItineraryDay and Activity records (best-effort)
    itinerary_dict = {}
    try:
        days = ItineraryDay.objects.filter(itinerary=itinerary).order_by('day_index')
        for day in days:
            # collect activity text from common fields, fall back to string()
            acts = []
            activities = Activity.objects.filter(itinerary_day=day).order_by('id')
            for a in activities:
                text = getattr(a, 'description', None) or getattr(a, 'activity', None) or getattr(a, 'name', None) or str(a)
                acts.append(text)
            key = f"Day {getattr(day, 'day_index', None) or getattr(day, 'id', '')}"
            itinerary_dict[key] = acts
    except Exception:
        itinerary_dict = {}

    # Compose a rich trip mapping for the template
    trip_map = {
        "name": trip.name,
        "country": trip.country,
        "duration_days": getattr(trip, 'duration', None) or getattr(trip, 'duration_days', None) or '',
        "estimated_cost": getattr(trip, 'estimated_cost', None) or getattr(trip, 'price', None) or 0,
        "category": getattr(trip, 'category', '') or '',
        "description": trip.description or '',
        "inclusions": getattr(trip, 'inclusions', []) or [],
        "exclusions": getattr(trip, 'exclusions', []) or [],
        "highlights": getattr(trip, 'highlights', []) or [],
        "best_time": getattr(trip, 'best_time', '') or '',
        "travel_tips": getattr(trip, 'travel_tips', '') or '',
        "hotels": getattr(trip, 'hotels', []) or [],
        "restaurants": getattr(trip, 'restaurants', []) or [],
        "local_transport": getattr(trip, 'local_transport', []) or [],
        "cost_breakdown": getattr(trip, 'cost_breakdown', {}) or {},
        "itinerary": itinerary_dict,
    }

    html = template.render({"trip": trip_map})

    response = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    response.seek(0)
    pdf = response.read()

    from django.http import HttpResponse
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f"attachment; filename={trip.name}.pdf"
    return resp
