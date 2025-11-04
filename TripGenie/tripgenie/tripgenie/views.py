from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request,"index.html")


def faqs(request):
    return render(request,"faqs.html")


@login_required(login_url='/login')
def contact(request):
    if request.method == "POST":
        name = request.POST.get("contact-form-name")
        email = (request.user.email if request.user.is_authenticated else None) or request.POST.get("contact-form-email")
        subject = request.POST.get("contact-form-subject")
        message = request.POST.get("contact-form-message")

        # Email to admin
        admin_subject = f"[TripGenie Contact] {subject}"
        admin_message = (
            f"New contact form submission:\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Subject: {subject}\n"
            f"Message:\n{message}"
        )

        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        # Confirmation email to user
        user_subject = "Thanks for contacting TripGenie!"
        user_message = (
            f"Hi {name},\n\n"
            f"Thanks for getting in touch with the TripGenie team.\n"
            f"We’ve received your message and will get back to you soon.\n\n"
            f"Your message details:\n"
            f"Subject: {subject}\n"
            f"Message: {message}\n\n"
            f"Warm regards,\nThe TripGenie Team"
        )

        send_mail(
            subject=user_subject,
            message=user_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully! Our support team will reach out soon.")
        return redirect("contact")
    
    return render(request, "contact.html")


def about(request):
    return render(request,"about.html")
