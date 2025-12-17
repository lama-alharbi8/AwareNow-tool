from django.core.mail import send_mail
from django.conf import settings

def send_activation_email(user):
    activation_link = f"http://127.0.0.1:8000/account/activate/{user.activation_token}/"

    send_mail(
        subject="Activate your AwareNow account",
        message=f"Click the link to activate your account:\n{activation_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
