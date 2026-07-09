from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime


class Scholarship(models.Model):
    name = models.CharField(max_length=100)
    type_of_scholarship = models.CharField(max_length=50)
    grade = models.CharField(max_length=20)
    year = models.IntegerField()
    category = models.CharField(max_length=50)
    criteria = models.TextField()
    documents_required = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.type_of_scholarship}"


class ScholarshipApplication(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        WAITING_DISBURSEMENT = "WAITING_DISBURSEMENT", "Waiting for disbursement"
        DISBURSED = "DISBURSED", "Disbursed"

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW)

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Keep simple for now (can upgrade to FileField later)
    statement = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("applicant", "scholarship")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.applicant.username} - {self.scholarship.name} ({self.status})"


# Backward compatibility model (not used by views)
class Web_User(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.user.email}"


class WebUserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="webuserprofile")
    # Optional avatar for non-compulsory profile picture
    # Use FileField to avoid requiring Pillow/ImageField dependency during migrations.
    profile_image = models.FileField(upload_to="profile_images/", blank=True, null=True)


    def __str__(self):
        return f"Profile({self.user.username})"



class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_otps")

    # Store OTP in hashed form
    otp_hash = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)
    consumed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"PasswordResetOTP(user={self.user.username}, expires_at={self.expires_at}, is_used={self.is_used})"

    
