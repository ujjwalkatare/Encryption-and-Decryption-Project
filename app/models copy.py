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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='uploaded_pdfs', on_delete=models.CASCADE)
    encrypted_file = models.FileField(upload_to='encrypted_pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.encrypted_file.name} -> {self.user.username}"

