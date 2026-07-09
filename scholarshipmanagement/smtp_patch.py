import smtplib
import ssl

_original_starttls = smtplib.SMTP.starttls

def patched_starttls(self, *args, **kwargs):
    context = kwargs.get("context")
    if context is None:
        context = ssl.create_default_context()
    return _original_starttls(self, context=context)

smtplib.SMTP.starttls = patched_starttls