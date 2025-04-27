from django.contrib import admin
from .models import EncryptedPaper, EncryptedPDF  # Import your models

# Register them so they show in the admin panel
admin.site.register(EncryptedPaper)
