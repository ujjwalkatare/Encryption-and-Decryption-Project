import os
import json
import uuid
import base64
import shutil
import hashlib
import hmac

from django.shortcuts import render, redirect
from django.http import FileResponse, Http404, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.cache import cache_control
from cryptography.fernet import Fernet
from PyPDF2 import PdfReader, PdfWriter
import pikepdf
import fitz
from PIL import Image, ImageDraw, ImageFont
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
import img2pdf

from .auth import authentication
from .extract_pdf import get_text_boxwise, encrypt, encrypt_text_boxes, replace_text_with_encrypted_images, extract_text_from_pdf, encrypt_text_blocks
from .models import EncryptedPaper

import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UploadPDFForm
from .models import EncryptedPaper
from .utils import (
    get_text_boxwise_and_show_boxes,
    replace_text_with_encrypted_images_accurate,
    convert_encrypted_images_to_pdf
)
from PIL import ImageFont

# Use the default PIL font instead of arial.ttf
font = ImageFont.load_default()

# ========== Views ==========
def index(request):
    return render(request, 'index.html')

def choose_registration(request):
    return render(request, "choose_registration.html")

def college_register(request):
    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        phone = request.POST['phone']
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['confirmPassword']

        verify = authentication(fname, lname, password, password1)
        if verify == "success":
            user = User.objects.create_user(username=username, password=password)
            user.first_name = fname
            user.last_name = lname
            user.save()

            college_group, _ = Group.objects.get_or_create(name='College')
            user.groups.add(college_group)

            messages.success(request, "Your College Account has been created.")
            return redirect("user_login")
        else:
            messages.error(request, verify)
            return redirect("college_register")
    
    return render(request, "college_register.html")

def university_register(request):
    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        phone = request.POST['phone']
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['confirmPassword']

        verify = authentication(fname, lname, password, password1)
        if verify == "success":
            user = User.objects.create_superuser(username=username, password=password)
            user.first_name = fname
            user.last_name = lname
            user.save()

            university_group, _ = Group.objects.get_or_create(name='University')
            user.groups.add(university_group)

            messages.success(request, "University admin account created.")
            return redirect("user_login")
        else:
            messages.error(request, verify)
            return redirect("university_register")
    
    return render(request, "university_register.html")

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Log In Successful!")
            
            if user.groups.filter(name='College').exists():
                return redirect("college_dashboard")
            elif user.groups.filter(name='University').exists():
                return redirect("university_dashboard")
            else:
                return redirect("dashboard")
        else:
            messages.error(request, "Invalid Username or Password.")
            return redirect("user_login")
    return render(request, "user_login.html")

def college_dashboard(request):
    return render(request, "college_dashboard.html")

@login_required
def university_dashboard(request):
    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            exam_name = form.cleaned_data['exam_name']
            pat = form.cleaned_data['pat']
            subject_name = form.cleaned_data['subject_name']
            original_pdf = form.cleaned_data['original_pdf']

            temp_dir = None
            try:
                # === TEMP SETUP ===
                unique_id = str(uuid.uuid4())
                temp_dir = os.path.join(settings.MEDIA_ROOT, f'temp_uploads/{unique_id}')
                os.makedirs(temp_dir, exist_ok=True)
                temp_pdf_path = os.path.join(temp_dir, original_pdf.name)

                with open(temp_pdf_path, 'wb+') as f:
                    for chunk in original_pdf.chunks():
                        f.write(chunk)

                # === TEXT EXTRACTION ===
                text_boxes = get_text_boxwise_and_show_boxes(temp_pdf_path, min_pages=1, max_pages=5)
                if not text_boxes or all(len(page) == 0 for page in text_boxes):
                    raise Exception("No readable text found in the uploaded PDF.")

                # === ENCRYPT + DRAW ===
                encrypted_img_dir = os.path.join(temp_dir, "encrypted_images")
                json_path = os.path.join(temp_dir, "encrypted_data.json")
                output_pdf_path = os.path.join(temp_dir, "final_encrypted.pdf")

                aes_key = replace_text_with_encrypted_images_accurate(
                    pdf_path=temp_pdf_path,
                    text_boxes=text_boxes,
                    output_dir=encrypted_img_dir,
                    font_size=12,  # Set base font size
                    save_json_path=json_path
                )

                convert_encrypted_images_to_pdf(encrypted_img_dir, output_pdf_path)

                # === SAVE TO DB ===
                paper = EncryptedPaper.objects.create(
                    university=request.user,
                    exam_name=exam_name,
                    pat=pat,
                    subject_name=subject_name,
                    aes_key=aes_key
                )

                with open(output_pdf_path, 'rb') as f:
                    paper.encrypted_pdf.save("encrypted_output.pdf", ContentFile(f.read()))
                with open(json_path, 'rb') as f:
                    paper.json_data.save("encrypted_data.json", ContentFile(f.read()))

                messages.success(request, "PDF encrypted and saved successfully.")
                return redirect('university_dashboard')

            except Exception as e:
                messages.error(request, f"Error occurred: {str(e)}")
                return redirect('university_dashboard')

            finally:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        form = UploadPDFForm()

    return render(request, 'university_dashboard.html', {'form': form})


@login_required
def college_list_view(request):
    colleges = User.objects.filter(groups__name='College')

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_colleges')
        pdf_file = request.FILES.get('pdf_file')

        if not selected_ids or not pdf_file:
            messages.error(request, "Please select at least one college and upload a PDF.")
        else:
            for college_id in selected_ids:
                college = User.objects.get(id=college_id)
                EncryptedPaper.objects.create(
                    university=college,
                    uploaded_by=request.user,
                    encrypted_pdf=pdf_file
                )
            messages.success(request, "Encrypted PDF sent to selected colleges successfully.")
            return redirect('college_list_view')

    return render(request, 'college_list.html', {
        'colleges': colleges,
    })

def log_out(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("/")