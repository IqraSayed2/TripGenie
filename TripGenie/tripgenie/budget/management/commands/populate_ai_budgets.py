from django.core.management.base import BaseCommand
from budget.models import Budget, Expense
from trips.models import Itinerary
from django.db import transaction

# mapping should mirror the one in views.py
AI_KEY_TO_CATEGORY = {
    "hotel": "Accommodation",
    "hotels": "Accommodation",
    "lodging": "Accommodation",
    "accommodation": "Accommodation",
    "stay": "Accommodation",
    "food": "Food",
    "meals": "Food",
    "transport": "Transportation",
    "transportation": "Transportation",
    "taxi": "Transportation",
    "flight": "Transportation",
    "activities": "Activities",
    "tours": "Activities",
    "shopping": "Shopping",
    "misc": "Misc",
    "miscellaneous": "Misc",
}

CATEGORIES = [c[0] for c in Expense.CATEGORY_CHOICES]

class Command(BaseCommand):
    help = "Populate or overwrite existing equal-split/empty Budgets using Trip.cost_breakdown (AI-generated)"

    def handle(self, *args, **options):
        count = 0
        updated = 0
        for b in Budget.objects.select_related('itinerary__trip').all():
            count += 1
            trip = getattr(b, 'itinerary', None)
            trip_obj = getattr(trip, 'trip', None) if trip else None
            breakdown = getattr(trip_obj, 'cost_breakdown', None)
            if not breakdown:
                continue

            # determine if existing category_budgets empty or equal-split
            existing_cb = b.category_budgets or {}
            looks_equal_split = False
            try:
                if existing_cb and b.total_budget:
                    vals = [float(existing_cb.get(cat, 0) or 0) for cat in CATEGORIES]
                    if vals:
                        avg = float(b.total_budget) / len(CATEGORIES)
                        if all(abs(v - avg) < 1e-6 for v in vals):
                            looks_equal_split = True
            except Exception:
                looks_equal_split = False

            if existing_cb and not looks_equal_split:
                # If user-customized budgets exist, normally leave them alone.
                # However, if Accommodation is zero but the Trip cost_breakdown
                # contains hotel(s), allow remapping so hotel amounts do not
                # remain lumped in Misc.
                has_hotels_in_breakdown = any(k.lower() in ("hotel", "hotels", "lodging") for k in breakdown.keys())
                try:
                    accommodation_val = float(existing_cb.get("Accommodation", 0) or 0)
                except Exception:
                    accommodation_val = 0
                if not (accommodation_val == 0 and has_hotels_in_breakdown):
                    continue

            # build new cat_budgets from breakdown
            cat_budgets = {cat: 0 for cat in CATEGORIES}
            for k, v in breakdown.items():
                mapped = AI_KEY_TO_CATEGORY.get(k.lower(), None)
                amount = 0
                if isinstance(v, (int, float)):
                    amount = float(v)
                elif isinstance(v, dict):
                    for maybe in ("cost", "amount", "price", "total"):
                        if maybe in v and isinstance(v[maybe], (int, float)):
                            amount = float(v[maybe])
                            break
                elif isinstance(v, str):
                    try:
                        amount = float(v.replace(',', '').strip())
                    except Exception:
                        amount = 0
                if mapped and mapped in cat_budgets:
                    cat_budgets[mapped] = amount
                else:
                    cat_budgets['Misc'] = cat_budgets.get('Misc', 0) + amount

            # apply and save
            with transaction.atomic():
                b.category_budgets = cat_budgets
                try:
                    b.total_budget = sum(float(x or 0) for x in cat_budgets.values())
                except Exception:
                    pass
                b.update_remaining()
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Scanned {count} budgets, updated {updated} budgets."))