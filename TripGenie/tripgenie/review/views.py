from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Review
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login')
def add_review(request):
    if request.method == "POST":
        name = request.POST.get("name")
        location = request.POST.get("location")
        rating = int(request.POST.get("rating", 5))
        comment = request.POST.get("comment")

        Review.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            location=location,
            rating=rating,
            comment=comment
        )

        messages.success(request, "⭐ Thank you! Your review has been submitted.")
        return redirect("home")

    return render(request, "add_review.html")
