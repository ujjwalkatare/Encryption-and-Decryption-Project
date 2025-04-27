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
from django.core.mail import EmailMessage
from django.conf import settings
import os
from .models import EncryptedPaper, DistributionLog
from PIL import ImageFont
from django.core.mail import EmailMessage
from django.conf import settings
import logging


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

from django.core.mail import get_connection, EmailMessage
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
import os
import logging

logger = logging.getLogger(__name__)

@login_required
def college_list_view(request):
    colleges = User.objects.filter(groups__name='College').order_by('first_name')
    papers = EncryptedPaper.objects.filter(university=request.user).order_by('-uploaded_at')
    
    if request.method == 'POST':
        selected_colleges = request.POST.getlist('selected_colleges', [])
        paper_id = request.POST.get('paper_id')
        
        if not selected_colleges or not paper_id:
            messages.error(request, "Please select both colleges and a paper")
            return redirect('college_list')
        
        try:
            paper = EncryptedPaper.objects.get(id=paper_id, university=request.user)
            success_count = 0
            failed_emails = []

            # Use storage-aware existence check
            if not paper.encrypted_pdf or not paper.encrypted_pdf.storage.exists(paper.encrypted_pdf.name):
                raise FileNotFoundError("PDF file not found or not accessible")
            
            # Create SMTP connection
            connection = get_connection(fail_silently=False, timeout=30)

            for college_id in selected_colleges:
                try:
                    college = User.objects.get(id=college_id, groups__name='College')
                    
                    # Use username as email (as per your design)
                    recipient_email = college.username
                    
                    dist_log = DistributionLog.objects.create(
                        paper=paper,
                        recipient=college,
                        status='pending',
                        email=recipient_email
                    )
                    
                    with paper.encrypted_pdf.open('rb') as pdf_file:
                        email = EmailMessage(
                            subject=f"New Exam Paper: {paper.exam_name}",
                            body=f"""Dear {college.first_name or college.username},

You've received an encrypted exam paper:

Exam: {paper.exam_name}
Subject: {paper.subject_name}
PAT: {paper.pat}

The encrypted PDF is attached to this email.

University Administration
{request.user.get_full_name() or request.user.username}""",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[recipient_email],
                            connection=connection
                        )
                        email.attach(
                            f"{paper.exam_name.replace(' ', '_')}.pdf",
                            pdf_file.read(),
                            'application/pdf'
                        )
                        email.send()
                    
                    dist_log.status = 'sent'
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to send to {recipient_email}: {str(e)}", exc_info=True)
                    dist_log.status = 'failed'
                    dist_log.notes = str(e)
                    failed_emails.append(recipient_email)
                finally:
                    dist_log.save()

            connection.close()

            messages.success(request, f"Successfully sent to {success_count} college(s)")
            if failed_emails:
                messages.warning(request, f"Failed to send to: {', '.join(failed_emails)}")

            return redirect('college_list')

        except EncryptedPaper.DoesNotExist:
            messages.error(request, "Selected paper not found")
            logger.error(f"Paper not found: {paper_id}")
        except Exception as e:
            logger.error(f"Distribution error: {str(e)}", exc_info=True)
            messages.error(request, f"Distribution failed: {str(e)}")

    context = {
        'colleges': colleges,
        'encrypted_papers': papers,
    }
    return render(request, 'college_list.html', context)


@login_required
def uploaded_papers_view(request):
    papers = EncryptedPaper.objects.filter(university=request.user).order_by('-uploaded_at')
    return render(request, 'uploaded_papers.html', {'papers': papers})

from django.shortcuts import render, get_object_or_404
from .models import EncryptedPaper

def view_encrypted_pdf(request, paper_id):
    paper = get_object_or_404(EncryptedPaper, id=paper_id)
    return render(request, 'view_encrypted_pdf.html', {'paper': paper})



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import EncryptedPaper, DistributionLog, AESKeyRequest

@login_required
def college_dashboard(request):
    college_user = request.user

    # ✅ Get all EncryptedPaper instances sent to this college user
    distribution_logs = DistributionLog.objects.filter(recipient=college_user)
    papers = [log.paper for log in distribution_logs]

    # ✅ Get related AES key requests (if any)
    key_requests = AESKeyRequest.objects.filter(requested_by=college_user, paper__in=papers)
    request_dict = {kr.paper.id: kr for kr in key_requests}

    return render(request, "college_dashboard.html", {
        "papers": papers,
        "requests": request_dict
    })

@login_required
def college_assigned_papers(request):
    # Get all distribution logs where this college is the recipient
    distribution_logs = DistributionLog.objects.filter(
        recipient=request.user,
        status='sent'  # Only show successfully sent papers
    ).select_related('paper')
    
    # Get all papers from these logs
    papers = [log.paper for log in distribution_logs]
    
    # Get all AES key requests made by this user
    requests = AESKeyRequest.objects.filter(requested_by=request.user)
    request_dict = {r.paper.id: r for r in requests}
    
    context = {
        'papers': papers,
        'requests': request_dict,
        'distribution_logs': distribution_logs,  # Pass logs for additional info if needed
    }
    return render(request, 'college_dashboard.html', context)

@login_required
def request_aes_key(request, paper_id):
    if request.method == 'POST':
        paper = get_object_or_404(EncryptedPaper, id=paper_id)
        
        # Verify this paper was actually sent to this user
        if not DistributionLog.objects.filter(paper=paper, recipient=request.user, status='sent').exists():
            messages.error(request, "You don't have access to this paper.")
            return redirect('college_assigned_papers')
        
        # Check if already requested
        existing_request = AESKeyRequest.objects.filter(
            paper=paper,
            requested_by=request.user
        ).first()
        
        if existing_request:
            messages.info(request, "You have already requested the AES key for this paper.")
        else:
            AESKeyRequest.objects.create(
                paper=paper,
                requested_by=request.user,
                status='pending'
            )
            messages.success(request, "AES key request submitted successfully.")
        
        return redirect('college_assigned_papers')
    
    # If not POST, redirect back
    return redirect('college_assigned_papers')

def log_out(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("/")