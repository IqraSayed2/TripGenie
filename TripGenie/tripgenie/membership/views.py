import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import MembershipPlan
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import timedelta
from .models import UserMembership, MembershipPayment
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login')
def membership_page(request):
    plans = MembershipPlan.objects.all()
    user_plan = None
    user_period = None
    if request.user.is_authenticated:
        try:
            membership = UserMembership.objects.get(user=request.user)
            user_plan = membership.plan_id
            user_period = getattr(membership, 'billing_period', None)
        except:
            # If the user has no membership yet, default to the 'Explorer' plan
            user_plan = None
            user_period = None
            try:
                explorer = MembershipPlan.objects.get(name__iexact='Explorer')
                user_plan = explorer.id
                # Mark both monthly and yearly as active for default explorer
                user_period = 'both'
            except MembershipPlan.DoesNotExist:
                # No explorer plan exists — leave defaults as None
                pass

    return render(request, "membership.html", {
        "plans": plans,
        "razorpay_key": settings.RAZORPAY_ID,
        "user_plan": user_plan,
        "user_period": user_period
    })


@login_required(login_url='/login')
def create_order(request, plan_id):
    if request.method == "POST":
        plan = get_object_or_404(MembershipPlan, id=plan_id)
        price = int(request.POST.get("price"))
        amount_paise = price * 100

        client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        # Save pending payment
        MembershipPayment.objects.create(
            user=request.user,
            plan=plan,
            order_id=order["id"],
            amount=price,
            status="FAILED"
        )

        return JsonResponse({
            "order_id": order["id"],
            "amount": amount_paise,
            "price":price,
            "plan_name": plan.name
        })
    


@login_required(login_url='/login')
@csrf_exempt 
def payment_success(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    user = request.user if request.user.is_authenticated else None
    plan_id = request.POST.get("plan_id")
    payment_id = request.POST.get("payment_id")
    order_id = request.POST.get("order_id")

    if not all([plan_id, payment_id, order_id]):
        return JsonResponse({"error": "Missing payment data"}, status=400)

    try:
        plan = MembershipPlan.objects.get(id=plan_id)
    except MembershipPlan.DoesNotExist:
        return JsonResponse({"error": "Invalid plan"}, status=400)

    try:
        pay = MembershipPayment.objects.get(order_id=order_id)
    except MembershipPayment.DoesNotExist:
        return JsonResponse({"error": "Payment record not found"}, status=404)

    # Update payment record
    pay.payment_id = payment_id
    pay.status = "SUCCESS"
    pay.save()

    # Activate membership for the user who made the payment (if available)
    if user:
        membership, created = UserMembership.objects.get_or_create(user=user)
        membership.plan = plan
        # Set billing period if provided in the POST (monthly/yearly)
        period = request.POST.get('period') or 'monthly'
        if period not in ('monthly', 'yearly'):
            period = 'monthly'
        membership.billing_period = period
        membership.is_active = True
        # Set validity depending on period (monthly -> 30 days, yearly -> 365 days)
        membership.valid_till = now().date() + (timedelta(days=365) if period == 'yearly' else timedelta(days=30))
        membership.save()

        # Email confirmation (best-effort)
        try:
            user.email_user(
                    subject="TripGenie Membership Activated",
                    message=(
                        f"Hi {user.username},\n\nYour membership '{plan.name}' has been successfully activated." \
                        f"\nAmount Paid: ₹{(pay.amount or 0)/100}\nValid Till: {membership.valid_till}\n\nHappy Traveling!\nTripGenie"
                    )
                )
        except Exception:
            # don't fail the request if email sending fails
            pass

    # Respond with a JSON redirect used by JS handler
    return JsonResponse({"redirect": "/membership/payment-status/?status=success"})

@login_required(login_url='/login')
def payment_status(request):
    status = request.GET.get("status")
    return render(request, "payment_status.html", {"status": status})

