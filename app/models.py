from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class EncryptedPaper(models.Model):
    university = models.ForeignKey(User, on_delete=models.CASCADE)
    exam_name = models.CharField(max_length=255)
    pat = models.CharField(max_length=100)
    subject_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    encrypted_pdf = models.FileField(upload_to='encrypted_papers/')
    aes_key = models.TextField()  # Store base64-encoded key
    json_data = models.FileField(upload_to='encrypted_data_json/')

    def __str__(self):
        return f"{self.exam_name} - {self.subject_name}"
    

class EncryptedPDF(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='uploaded_pdfs', on_delete=models.CASCADE, null=True)
    encrypted_file = models.FileField(upload_to='encrypted_pdfs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.encrypted_file.name} -> {self.user.username}"

class DistributionLog(models.Model):
    paper = models.ForeignKey(EncryptedPaper, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ])
    email = models.EmailField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-sent_at']
        
    def __str__(self):
        return f"{self.paper.exam_name} to {self.recipient.username}"

class AESKeyRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    paper = models.ForeignKey(EncryptedPaper, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aes_key_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)

    def approve(self):
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()

    class Meta:
        unique_together = ('paper', 'requested_by')

    def __str__(self):
        return f"{self.requested_by.username} → {self.paper.exam_name} ({self.status})"

