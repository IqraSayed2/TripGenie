from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.mail import send_mail
from django.contrib import messages
from tripgenie import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import random
import logging
from django.contrib.auth.decorators import login_required


logger = logging.getLogger(__name__)

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def register(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        first_name = (request.POST.get("firstname") or "").strip()
        last_name = (request.POST.get("lastname") or "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password") or ""
        confirm = request.POST.get("confirmpassword") or ""

        # Basic validation
        if not username or not first_name or not email or not password:
            messages.error(request, "Please fill required fields.")
            return render(request, "signup.html")

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "signup.html")

        # Password validation
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, f"Password error: {' '.join(e.messages)}")
            return render(request, "signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different username.")
            return render(request, "signup.html", {
                'form_data': request.POST
            })

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered. Please use a different email or login.")
            return render(request, "signup.html", {
                'form_data': request.POST  # Send back form data to repopulate fields
            })

        # Create user but set is_active to False
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            # Ensure user starts inactive. Save explicitly and force update of is_active
            user.is_active = False
            user.save()
            # Force-write the is_active field again to avoid any possible signals/overwrites
            try:
                User.objects.filter(pk=user.pk).update(is_active=False)
                user.refresh_from_db()
            except Exception:
                # If DB-level update fails, log but continue (we still have user saved above)
                logger.exception("Failed to force-update is_active for user %s", user.pk)
            logger.info("New user created (id=%s, username=%s) is_active after save: %s", user.pk, user.username, user.is_active)
        except Exception as e:
            messages.error(request, "An error occurred during registration. Please try again.")
            return render(request, "signup.html", {
                'form_data': request.POST
            })



        # Generate & save OTP in session
        otp = generate_otp()
        request.session['signup_otp'] = otp
        request.session['signup_user_id'] = user.id

        # Debug/log OTP (remove in production)
        logger.info("Signup OTP for %s: %s", email, otp)
        print(f"[DEBUG] Signup OTP for {email}: {otp}")

        # Send OTP email but don't crash the flow if mail fails
        try:
            send_mail(
                'TripGenie - Verify your account',
                f'Your verification OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            logger.exception("Failed to send signup OTP to %s", email)
            messages.warning(request, "Unable to send verification email right now. Use the code shown in server logs for testing.")

        return redirect('verify_otp')

    return render(request, "signup.html")


def verify_otp(request):
    if request.method == "POST":
        posted_otp = request.POST.get("otp")
        if not posted_otp:
            posted_otp = ''.join([request.POST.get(f"otp{i}", "") for i in range(6)])

        stored_otp = request.session.get('signup_otp')
        user_id = request.session.get('signup_user_id')

        logger.debug("verify_otp: posted=%s stored=%s user_id=%s", posted_otp, stored_otp, user_id)
        print(f"[DEBUG] posted_otp={posted_otp} stored_otp={stored_otp} user_id={user_id}")

        if not stored_otp or not user_id:
            messages.error(request, "No OTP session found. Please sign up again.")
            return redirect('register')

        if posted_otp == stored_otp:
            try:
                user = User.objects.get(pk=user_id)
                user.is_active = True
                user.save()
                # mark email_verified on the related UserProfile (create if missing)
                try:
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.email_verified = True
                    profile.save()
                except Exception:
                    logger.exception("Failed to set email_verified for user %s", user.pk)
                request.session.pop('signup_otp', None)
                request.session.pop('signup_user_id', None)
                messages.success(request, "User registered successfully! Please login to continue.")
                # explicit path if name resolution fails: return redirect('/users/login/')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('register')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "otp.html")


def user_login(request):
    if request.method == "GET":
        return render(request, "login.html")

    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    if not username or not password:
        messages.error(request, "Enter both username and password.")
        return render(request, "login.html")

    user = authenticate(request, username=username, password=password)
    if user is not None:
        # Require both Django's is_active and our email_verified flag
        try:
            profile = UserProfile.objects.get(user=user)
            email_verified = getattr(profile, 'email_verified', False)
        except UserProfile.DoesNotExist:
            email_verified = False

        if user.is_active and email_verified:
            login(request, user)
            return redirect("home")
        messages.error(request, "Account inactive or email not verified. Please verify your email first.")
    else:
        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect("login")


@login_required(login_url='/login')
def view_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {
        'user': request.user,
        'profile': profile
    })


@login_required(login_url='/login')
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()

        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()

        return redirect('profile')

    return render(request, 'edit_profile.html', {
        'user': request.user,
        'profile': profile
    })