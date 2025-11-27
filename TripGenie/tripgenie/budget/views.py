import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from trips.models import Itinerary
from .models import Budget, Expense
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils.text import slugify
from membership.decorators import premium_required


# mapping from possible AI breakdown keys (or trip detail keys) to your categories
AI_KEY_TO_CATEGORY = {
    "hotel": "Accommodation",
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
    "hotels": "Accommodation",
}

CATEGORIES = [c[0] for c in Expense.CATEGORY_CHOICES]

@login_required(login_url='/login')
def budget_page(request):
    saved_trips = Itinerary.objects.filter(user=request.user)
    selected_trip = None
    budget = None
    expenses = []
    category_summary = {}
    categories = CATEGORIES

    # Accept trip selection by name (trip_name) or by id (trip_id) for backward compat.
    trip_name = request.GET.get("trip_name")
    trip_id = request.GET.get("trip_id") or request.GET.get("trip")

    if trip_name:
        # Note: trip titles should be unique for this to be reliable.
        try:
            selected_trip = Itinerary.objects.get(title=trip_name, user=request.user)
        except Itinerary.DoesNotExist:
            selected_trip = None
    elif trip_id:
        selected_trip = get_object_or_404(Itinerary, id=trip_id, user=request.user)

    if selected_trip:
        budget, created = Budget.objects.get_or_create(itinerary=selected_trip)

        # If budget was just created OR it exists but has no per-category budgets,
        # and the itinerary has an AI cost_breakdown JSON, populate per-category
        # budgets automatically. This prevents falling back to an equal split
        # when AI-provided breakdowns are available but the Budget record is empty.
        # detect if an existing budget was previously created by an equal-split
        # fallback (user saw equal amounts across categories). If so, and we
        # have an AI breakdown, prefer the AI values and overwrite the equal
        # split. This helps when budgets were created before AI integration.
        existing_cb = budget.category_budgets or {}
        looks_equal_split = False
        try:
            if existing_cb and budget.total_budget:
                vals = [float(existing_cb.get(cat, 0) or 0) for cat in categories]
                if vals:
                    avg = float(budget.total_budget) / len(categories)
                    # consider it an equal split if every value is very close to avg
                    if all(abs(v - avg) < 1e-6 for v in vals):
                        looks_equal_split = True
        except Exception:
            looks_equal_split = False

        # The AI cost breakdown is stored on the Trip model (selected_trip.trip).
        trip_obj = getattr(selected_trip, 'trip', None)
        if (created or not budget.category_budgets or looks_equal_split) and getattr(trip_obj, "cost_breakdown", None):
            breakdown = trip_obj.cost_breakdown or {}
            # Initialize category_budgets with zeros for all known categories
            cat_budgets = {cat: 0 for cat in categories}
            # Map AI keys to categories
            for k, v in breakdown.items():
                mapped = AI_KEY_TO_CATEGORY.get(k.lower(), None)
                # if breakdown gives nested dict like {"hotel": {"cost": 1000}}, handle numeric extraction
                amount = 0
                if isinstance(v, (int, float)):
                    amount = float(v)
                elif isinstance(v, dict):
                    # try common keys
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
                    # unknown mapping -> put into Misc
                    cat_budgets["Misc"] = cat_budgets.get("Misc", 0) + amount

            # Save to budget
            budget.category_budgets = cat_budgets
            # Update total budget as sum of category budgets
            try:
                budget.total_budget = sum(float(x or 0) for x in cat_budgets.values())
            except Exception:
                budget.total_budget = 0
            budget.update_remaining()
            # persist changes
            budget.save()

        # load all expenses (show full list instead of limiting to 10)
        expenses = list(Expense.objects.filter(budget=budget).order_by("-date"))

        # Category summary: compute spent, budget and remaining per category
        for cat in categories:
            cat_expenses = [e for e in expenses if e.category == cat]
            spent = sum(e.amount for e in Expense.objects.filter(budget=budget, category=cat))
            # Use exact AI-provided category budgets when present. If a category
            # wasn't generated by the AI, it will be present with value 0 so the
            # UI allows users to edit it. Only if there are no category_budgets
            # at all we fall back to equal split.
            if budget.category_budgets:
                try:
                    budgeted = float(budget.category_budgets.get(cat, 0) or 0)
                except Exception:
                    budgeted = 0
            else:
                # fallback: equal split if no per-category budgets
                budgeted = budget.get_category_budget(len(categories))
            remaining_cat = budgeted - spent
            category_summary[cat] = {
                "spent": spent,
                "budget": budgeted,
                "remaining": remaining_cat
            }

    context = {
        "saved_trips": saved_trips,
        "selected_trip": selected_trip,
        "budget": budget,
        "expenses": expenses,
        "category_summary": category_summary,
        "categories": categories,
    }
    return render(request, "budget.html", context)


@login_required(login_url='/login')
@require_POST
def api_add_expense(request):
    """
    Accept either JSON or form-encoded (FormData) requests to create an Expense.
    Returns updated recent expenses and the updated category summary & totals.
    """
    # support both JSON and form posts
    if request.content_type and "application/json" in request.content_type:
        data = json.loads(request.body.decode("utf-8"))
        trip_id = data.get("trip_id")
        title = data.get("title")
        category = data.get("category")
        amount = float(data.get("amount") or 0)
        date_str = data.get("date")
    else:
        trip_id = request.POST.get("trip_id")
        title = request.POST.get("title")
        category = request.POST.get("category")
        amount = float(request.POST.get("amount") or 0)
        date_str = request.POST.get("date")

    itinerary = get_object_or_404(Itinerary, id=trip_id, user=request.user)
    budget, _ = Budget.objects.get_or_create(itinerary=itinerary)

    # parse date if provided, else auto_now will set current date on model save
    if date_str:
        parsed = parse_date(date_str)
        if parsed:
            expense = Expense.objects.create(budget=budget, title=title, category=category, amount=amount, date=parsed)
            # Some models set `auto_now` on the date field which overrides
            # passed-in dates during save(); update via QuerySet to ensure
            # the chosen date is persisted in the DB.
            try:
                Expense.objects.filter(pk=expense.pk).update(date=parsed)
            except Exception:
                pass
        else:
            expense = Expense.objects.create(budget=budget, title=title, category=category, amount=amount)
    else:
        expense = Expense.objects.create(budget=budget, title=title, category=category, amount=amount)

    # budget.update_remaining() is triggered by Expense.save() (your model does this)
    # Compose response with latest expenses and updated totals & summary
    latest_expenses = list(Expense.objects.filter(budget=budget).order_by("-date").values("title", "category", "amount", "date"))

    # Build category_summary similar to budget_page
    categories = CATEGORIES
    cat_summary = {}
    for cat in categories:
        spent = sum(e.amount for e in Expense.objects.filter(budget=budget, category=cat))
        budgeted = float(budget.category_budgets.get(cat, 0) or 0) if budget.category_budgets else budget.get_category_budget(len(categories))
        cat_summary[cat] = {
            "spent": spent,
            "budget": budgeted,
            "remaining": budgeted - spent
        }

    response = {
        "status": "ok",
        "expenses": [
            {"title": e["title"], "category": e["category"], "amount": float(e["amount"]), "date": e["date"].strftime("%d %b %Y")}
            for e in latest_expenses
        ],
        "totals": {
            "total_budget": budget.total_budget,
            "total_spent": budget.total_spent,
            "remaining": budget.remaining,
        },
        "category_summary": cat_summary,
    }
    return JsonResponse(response)


@login_required(login_url='/login')
@require_POST
def api_update_category_budget(request):
    """
    Expects JSON body: { "trip_id": 35, "category": "Food", "budgeted_amount": 1234.5 }
    Updates budget.category_budgets and recalculates totals. Returns updated totals & category_summary.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        # fallback to form post
        data = request.POST

    trip_id = data.get("trip_id")
    category = data.get("category")
    try:
        amount = float(data.get("budgeted_amount") or 0)
    except Exception:
        return HttpResponseBadRequest("Invalid budget amount")

    itinerary = get_object_or_404(Itinerary, id=trip_id, user=request.user)
    budget, _ = Budget.objects.get_or_create(itinerary=itinerary)

    # ensure category_budgets exists
    cb = budget.category_budgets or {c: 0 for c in CATEGORIES}
    cb[category] = amount
    budget.category_budgets = cb

    # update total_budget as sum of categories
    try:
        budget.total_budget = sum(float(v or 0) for v in cb.values())
    except Exception:
        budget.total_budget = budget.total_budget

    budget.update_remaining()

    # Build category summary for response
    cat_summary = {}
    for cat in CATEGORIES:
        spent = sum(e.amount for e in Expense.objects.filter(budget=budget, category=cat))
        budgeted = float(budget.category_budgets.get(cat, 0) or 0)
        cat_summary[cat] = {
            "spent": spent,
            "budget": budgeted,
            "remaining": budgeted - spent
        }

    return JsonResponse({
        "status": "ok",
        "totals": {
            "total_budget": budget.total_budget,
            "total_spent": budget.total_spent,
            "remaining": budget.remaining,
        },
        "category_summary": cat_summary
    })


@login_required(login_url='/login')
def api_get_recent_expenses(request, trip_id):
    """Return the latest 10 expenses for the selected trip (for AJAX updates)."""
    itinerary = get_object_or_404(Itinerary, id=trip_id, user=request.user)
    budget = get_object_or_404(Budget, itinerary=itinerary)
    # return all expenses for the given trip
    expenses = (
        Expense.objects.filter(budget=budget)
        .order_by("-date")
        .values("title", "category", "amount", "date")
    )

    # Format date and amounts for frontend
    expense_list = [
        {
            "title": e["title"],
            "category": e["category"],
            "amount": float(e["amount"]),
            "date": e["date"].strftime("%d %b %Y"),
        }
        for e in expenses
    ]
    return JsonResponse({"status": "ok", "expenses": expense_list})


@premium_required
@login_required
def export_budget_pdf(request, budget_id):
    # Budget doesn't have a direct `user` field; it belongs to an Itinerary.
    # Restrict by the related itinerary's user to ensure owners only can export.
    budget = get_object_or_404(Budget, id=budget_id, itinerary__user=request.user)
    expenses = Expense.objects.filter(budget=budget).order_by("-date")
    recent_expenses = expenses

    # Render HTML template with context
    template = get_template("budget_pdf_template.html")
    html = template.render({
        "budget": budget,
        "expenses": expenses,
        "recent_expenses": recent_expenses,
        "user": request.user
    })

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    # Budget model doesn't have a title; use related itinerary title if available
    itin_title = getattr(getattr(budget, 'itinerary', None), 'title', None)
    filename_base = slugify(itin_title) if itin_title else f"budget-{budget.id}"
    response['Content-Disposition'] = f'attachment; filename="{filename_base}_report.pdf"'

    # Generate PDF
    pisa_status = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=response, encoding='UTF-8')

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response