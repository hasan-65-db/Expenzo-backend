from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from dateutil.relativedelta import relativedelta
from .models import Transaction

@shared_task
def send_registration_mail(email):
    try:
        subject = "Signup Alert"
        body = "You have successfully signeup at SpendWisely"
        send_mail(
        subject,
        body,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False
    )
        return f"email sent to {email}"

    except Exception as e:
        return f"failed to send email: {str(e)}"

@shared_task
def create_recurring_expenses():
    today = timezone.now().date()
    recurring_items = Transaction.objects.filte (
        is_occurence = True,
        next_occurence = today
    )
    for item in recurring_items:
        Transaction.objects.create(
            title = item.title,
            amount = item.amount,
            category = item.category,
            owner = item.owner,
            is_recurring = False
        )

        item.next_occurence = today + relativedelta(month=1)
        item.save()

@shared_task
def budgetAlertMail(email):
    try:
        subject = "Budget Alert"
        body = "You have reached 80% of your monthly budget limit, Kindly check your dashboard to stay on track!!"
        send_mail(
            subject,
            body,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )
        return f"email sent to {email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"




    
