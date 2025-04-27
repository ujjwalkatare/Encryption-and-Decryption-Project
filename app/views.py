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

# app/views.py
# app/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import AESKeyRequest

@login_required
def view_key_requests(request):
    # Restrict to university admins only
    if not (request.user.is_superuser or 
            request.user.groups.filter(name='University').exists()):
        return render(request, 'unauthorized.html')

    # Only show requests for this university’s papers
    key_requests = AESKeyRequest.objects.filter(
        paper__university=request.user
    ).select_related('paper', 'requested_by')

    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')

        kr = get_object_or_404(
            AESKeyRequest,
            id=req_id,
            paper__university=request.user
        )

        if action == 'approve':
            kr.status = 'approved'
            kr.approved_at = timezone.now()
            kr.decision_notes = 'Approved by university admin'
            kr.save()

            # email the AES key...
            aes_key = kr.paper.aes_key
            subject_name = kr.paper.subject_name
            exam_name = kr.paper.exam_name
            to_email = kr.requested_by.email

            send_mail(
                f"AES Key for {subject_name} – {exam_name}",
                f"Dear {kr.requested_by.username},\n\n"
                f"Your request has been approved.\n\n"
                f"AES Key:\n{aes_key}\n\n"
                "— University Admin",
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
            )

            messages.success(
                request,
                f"Approved and emailed key to {kr.requested_by.username}"
            )

        elif action == 'reject':
            kr.status = 'rejected'
            kr.decision_notes = 'Rejected by university admin'
            kr.save()
            messages.info(
                request,
                f"Rejected request from {kr.requested_by.username}"
            )

        # ← Redirect back to this same view
        return redirect('view_key_requests')

    return render(request, 'view_key_requests.html', {
        'key_requests': key_requests
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AESKeyRequest

def approve_key_request(request, request_id):
    aes_request = AESKeyRequest.objects.get(id=request_id)
    aes_request.approve()
    messages.success(request, "Request approved successfully.")
    return redirect('view_key_requests')

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import EncryptedPaper, AESKeyRequest
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

def print_encrypted_pdf(request, paper_id):
    paper = get_object_or_404(EncryptedPaper, id=paper_id)
    aes_request = AESKeyRequest.objects.get(paper=paper, requested_by=request.user, status='approved')

    # Fetch the AES key (ensure it's base64 encoded)
    aes_key = base64.b64decode(paper.aes_key)

    # Read the encrypted PDF file
    encrypted_pdf = paper.encrypted_pdf.read()

    # Initialize AES cipher in CBC mode, with the IV from the first block
    cipher = AES.new(aes_key, AES.MODE_CBC, iv=encrypted_pdf[:AES.block_size])

    # Decrypt the content (after removing the IV)
    decrypted_pdf = unpad(cipher.decrypt(encrypted_pdf[AES.block_size:]), AES.block_size)

    # Prepare the decrypted PDF for response
    response = HttpResponse(decrypted_pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{paper.exam_name}_decrypted.pdf"'

    return response

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from .models import EncryptedPaper

def print_encrypted_pdf(request, paper_id):
    paper = get_object_or_404(EncryptedPaper, id=paper_id)
    
    # Return the encrypted PDF directly (no decryption)
    response = FileResponse(
        paper.encrypted_pdf.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'inline; filename="{paper.exam_name}.pdf"'
    return response


def log_out(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("/")

import os
import json
import base64
import tempfile
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hmac
import hashlib
import img2pdf
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import EncryptedPaper
from django.conf import settings


def aes_decrypt(encrypted_text, key_base64):
    try:
        key_bytes = base64.b64decode(key_base64)
        key_hash = hashlib.sha256(key_bytes).digest()
        raw = base64.b64decode(encrypted_text)
        iv = raw[:16]
        encrypted = raw[16:-32]
        mac = raw[-32:]

        expected_mac = hmac.new(key_hash, iv + encrypted, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("HMAC verification failed")

        cipher = AES.new(key_hash, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted)
        return unpad(decrypted, AES.block_size).decode("utf-8")
    except Exception as e:
        print(f"Decryption failed: {str(e)}")
        return "[DECRYPTION ERROR]"


def draw_wrapped_text(draw, text, box_x, box_y, box_width, box_height, font_path, min_font_size=8, padding=20):
    font_size = int(box_height * 0.7)
    while font_size >= min_font_size:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        padded_width = box_width - 2 * padding
        padded_height = box_height - 2 * padding

        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if draw.textlength(test_line, font=font) <= padded_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
        total_height = len(lines) * line_height

        if total_height <= padded_height or font_size == min_font_size:
            return lines, font, line_height

        font_size -= 1

    return lines, font, line_height


def print_encrypted_pdf(request, paper_id):
    paper = get_object_or_404(EncryptedPaper, id=paper_id)
    encrypted_pdf_path = paper.encrypted_pdf.path
    json_path = paper.json_data.path
    aes_key = paper.aes_key

    temp_dir = tempfile.mkdtemp()
    dpi = 300
    letter_width_px = int(8.5 * dpi)
    letter_height_px = int(11 * dpi)
    decrypted_images = []
    font_path = "C:\\Windows\\Fonts\\arial.ttf" if os.name == 'nt' else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        pdf_document = fitz.open(encrypted_pdf_path)

        for page_num, page_data in enumerate(all_data):
            if page_num >= len(pdf_document):
                break

            original_page = pdf_document[page_num]
            original_width = original_page.rect.width
            original_height = original_page.rect.height

            scale_x = letter_width_px / original_width
            scale_y = letter_height_px / original_height

            img = Image.new("RGB", (letter_width_px, letter_height_px), "white")
            draw = ImageDraw.Draw(img)

            for box_info in page_data:
                if len(box_info) >= 6:
                    x0, y0, x1, y1 = box_info[0], box_info[1], box_info[2], box_info[3]
                    encrypted_text = box_info[4]

                    decrypted_text = aes_decrypt(encrypted_text, aes_key)

                    scaled_x0 = x0 * scale_x
                    scaled_y0 = y0 * scale_y
                    scaled_x1 = x1 * scale_x
                    scaled_y1 = y1 * scale_y
                    box_width = scaled_x1 - scaled_x0
                    box_height = scaled_y1 - scaled_y0

                    lines, font, line_height = draw_wrapped_text(
                        draw, decrypted_text, scaled_x0, scaled_y0, box_width, box_height, font_path
                    )

                    for i, line in enumerate(lines):
                        text_x = scaled_x0 + 20
                        text_y = scaled_y0 + 20 + i * line_height
                        draw.text((text_x, text_y), line, font=font, fill="black")

            temp_img_path = os.path.join(temp_dir, f"page_{page_num + 1}.png")
            img.save(temp_img_path, dpi=(dpi, dpi))
            decrypted_images.append(temp_img_path)

        # Create PDF
        output_pdf_path = os.path.join(temp_dir, "decrypted_output.pdf")
        with open(output_pdf_path, "wb") as f_out:
            f_out.write(img2pdf.convert(decrypted_images))

        return FileResponse(open(output_pdf_path, "rb"), as_attachment=False, filename="Decrypted_Paper.pdf")

    except Exception as e:
        raise Http404(f"Decryption failed: {e}")
