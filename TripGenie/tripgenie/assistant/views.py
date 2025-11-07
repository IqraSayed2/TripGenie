from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from groq import Groq
from .models import ChatMessage
import json

client = Groq(api_key=settings.GROQ_API_KEY)


@csrf_exempt
@login_required(login_url='/login')
def chatbot_response(request):
    """Handles sending and saving chat messages."""
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        ChatMessage.objects.create(user=request.user, role="user", content=user_message)

        # Include context (last 10 messages)
        recent = ChatMessage.objects.filter(user=request.user).order_by("-created_at")[:10]
        conversation = [{"role": m.role, "content": m.content} for m in reversed(recent)]
        conversation.insert(0, {
            "role": "system",
            "content": "You are TripGenie, a friendly and smart travel assistant. Respond conversationally."
        })

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=conversation,
                temperature=0.7,
            )
            ai_reply = response.choices[0].message.content
            ChatMessage.objects.create(user=request.user, role="assistant", content=ai_reply)
            return JsonResponse({"reply": ai_reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required(login_url='/login')
def load_chat(request):
    """Return all saved messages for current user."""
    messages = ChatMessage.objects.filter(user=request.user).order_by("created_at")
    data = [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.strftime("%H:%M"),
        }
        for msg in messages
    ]
    return JsonResponse({"messages": data})


@login_required(login_url='/login')
@csrf_exempt
def clear_chat(request):
    """Clear chat history."""
    ChatMessage.objects.filter(user=request.user).delete()
    return JsonResponse({"success": True})
