from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def send_submission_email(submission):
    subject = f"Nuevo envio: {submission.form.name}"
    message = render_to_string("forms_builder/email/submission.txt", {"submission": submission})
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@cardbook.local")
    reply_to = [submission.sender_email] if submission.sender_email else None
    try:
        email = EmailMessage(
            subject,
            message,
            from_email,
            [submission.form.recipient_email],
            reply_to=reply_to,
        )
        email.send(fail_silently=False)
        submission.email_sent = True
        submission.email_error = ""
        submission.save(update_fields=["email_sent", "email_error"])
    except Exception as exc:
        submission.email_sent = False
        submission.email_error = str(exc)[:1000]
        submission.save(update_fields=["email_sent", "email_error"])
    return submission.email_sent
