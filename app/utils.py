import os
import json
import base64
import hashlib
import hmac
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
import fitz
from PIL import Image, ImageDraw, ImageFont
import img2pdf

def get_text_boxwise_and_show_boxes(pdf_path, min_pages=1, max_pages=5):
    pdf_document = fitz.open(pdf_path)
    all_text_boxes = []
    total_pages = pdf_document.page_count
    pages_to_process = max(min(total_pages, max_pages), min_pages)

    for page_num in range(pages_to_process):
        page = pdf_document[page_num]
        text_boxes = []
        page_dict = page.get_text("dict")
        for block in page_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        x0, y0, x1, y1 = span["bbox"]
                        text = span["text"].strip()
                        if text:
                            text_boxes.append((x0, y0, x1, y1, text))
        all_text_boxes.append(text_boxes)
    pdf_document.close()
    return all_text_boxes

def aes_encrypt(text, key_base64):
    key_bytes = base64.b64decode(key_base64)
    key_hash = hashlib.sha256(key_bytes).digest()
    iv = get_random_bytes(16)
    cipher = AES.new(key_hash, AES.MODE_CBC, iv)
    padded_text = pad(text.encode(), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_text)
    mac = hmac.new(key_hash, iv + encrypted_bytes, hashlib.sha256).digest()
    encrypted_data = base64.b64encode(iv + encrypted_bytes + mac).decode('utf-8')
    return encrypted_data

def truncate_text_to_fit(draw, text, box_width, font, font_size=10):
    try:
        while draw.textlength(text, font=font) > box_width:
            if len(text) <= 4:
                return "..."
            text = text[:-4] + "..."
        return text
    except:
        # Fallback if font measurement fails
        max_chars = int(box_width / (font_size * 0.6))  # Approximate char width
        return text[:max_chars] + "..." if len(text) > max_chars else text

def draw_text_in_box(draw, text, box, font, fill="black"):
    x0, y0, x1, y1 = box
    box_height = y1 - y0
    try:
        text_bbox = font.getbbox("A")
        text_height = text_bbox[3] - text_bbox[1]
        y_centered = y0 + (box_height - text_height) / 2
        draw.text((x0, y_centered), text, font=font, fill=fill)
    except:
        # Simple fallback if font metrics fail
        draw.text((x0, y0), text, font=font, fill=fill)

def replace_text_with_encrypted_images_accurate(pdf_path, text_boxes, output_dir, font_size=12, save_json_path=None):
    os.makedirs(output_dir, exist_ok=True)
    key = get_random_bytes(16)
    key_base64 = base64.b64encode(key).decode('utf-8')
    pdf_document = fitz.open(pdf_path)
    encrypted_data_to_save = []

    # Use default font
    try:
        font = ImageFont.load_default()
        # Scale default font
        font = ImageFont.load_default().font_variant(size=font_size)
    except:
        # Ultimate fallback
        font = ImageFont.load_default()

    for page_num, page_boxes in enumerate(text_boxes):
        page = pdf_document[page_num]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)
        page_info = []

        for box in page_boxes:
            x0, y0, x1, y1, original_text = box
            encrypted_text = aes_encrypt(original_text, key_base64)
            page_info.append((x0, y0, x1, y1, encrypted_text, original_text))
            box_width = x1 - x0
            box_height = y1 - y0
            
            # Dynamic font sizing
            try:
                current_font_size = max(8, int(box_height * 0.6))
                current_font = font.font_variant(size=current_font_size)
            except:
                current_font = font

            encrypted_short = truncate_text_to_fit(draw, encrypted_text, box_width, current_font)
            draw.rectangle([x0, y0, x1, y1], fill="white")
            draw_text_in_box(draw, encrypted_short, (x0, y0, x1, y1), current_font)

        output_path = os.path.join(output_dir, f"encrypted_page_{page_num + 1}.png")
        img.save(output_path)
        encrypted_data_to_save.append(page_info)

    pdf_document.close()
    
    if save_json_path:
        with open(save_json_path, "w", encoding="utf-8") as f:
            json.dump(encrypted_data_to_save, f, indent=2)

    return key_base64

def convert_encrypted_images_to_pdf(encrypted_images_dir, output_pdf_path):
    image_files = [
        os.path.join(encrypted_images_dir, f)
        for f in os.listdir(encrypted_images_dir)
        if f.endswith(".png") and f.startswith("encrypted_page_")
    ]
    image_files.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))
    with open(output_pdf_path, "wb") as pdf_file:
        pdf_file.write(img2pdf.convert(image_files))