from django.shortcuts import render, redirect

def home(request):
    return render(request,"index.html")

def faqs(request):
    return render(request,"faqs.html")

