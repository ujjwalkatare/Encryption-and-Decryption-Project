import re
# Authenticate User
def name_valid(name):
    if name.isalpha() and len(name) > 1:
        return True
    else:
        return False
def password_valid(pass1):
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pat = re.compile(reg)
    mat = re.search(pat, pass1)
    if mat:
        return True
    else:
        return False
def password_check(password1, password2):
    if password1 == password2:
        return True
    else:
        return False
def authentication(first_name, last_name, pass1, pass2):
    if not name_valid(first_name):
        return "Invalid First Name"
    elif not name_valid(last_name):
        return "Invalid Last Name"
    elif not password_valid(pass1):
        return "Password should be in proper format (e.g., Password@1234)"
    elif not password_check(pass1, pass2):
        return "Passwords do not match"
    else:
        return "success"
    
################## encryption function ###################################



import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from cryptography.fernet import Fernet
from IPython.display import display
from cryptography.fernet import Fernet
# Function to convert PDF pages to images
def pdf_to_images(pdf_path, num_pages=2):
    pdf_document = fitz.open(pdf_path)
    images = []

    for page_num in range(num_pages):
        page = pdf_document[page_num]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    pdf_document.close()
    return images
def draw_bounding_boxes(image, page):
    img_with_boxes = image.copy()
    draw = ImageDraw.Draw(img_with_boxes)

    for block in page.get_text("blocks"):
        x0, y0, x1, y1 = block[:4]
        draw.rectangle([x0, y0, x1, y1], outline="red", width=2)

    return img_with_boxes
def display_pdf_text_with_boxes(pdf_path, num_pages=2):
    pdf_document = fitz.open(pdf_path)
    images = pdf_to_images(pdf_path, num_pages)

    for i, image in enumerate(images):
        page = pdf_document[i]
        img_with_boxes = draw_bounding_boxes(image, page)
        display(img_with_boxes)

    pdf_document.close()
    
def get_text_boxwise(pdf_path, num_pages=2):
    pdf_document = fitz.open(pdf_path)
    all_text_boxes = []

    for page_num in range(num_pages):
        page = pdf_document[page_num]
        text_boxes = []
        
        # Extract each text block
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]
            text_boxes.append(text.strip())  # Add text without leading/trailing spaces

        all_text_boxes.append(text_boxes)

    pdf_document.close()
    return all_text_boxes
display_pdf_text_with_boxes("dataset/first_two_pages.pdf")
text_boxes = get_text_boxwise("dataset/first_two_pages.pdf")
print("Extracted Text Boxwise:", text_boxes)
def caesar_encrypt(text, shift):
    encrypted_text = ""
    for char in text:
        if char.isalpha():
            shift_base = ord('A') if char.isupper() else ord('a')
            encrypted_char = chr((ord(char) - shift_base + shift) % 26 + shift_base)
            encrypted_text += encrypted_char
        else:
            encrypted_text += char
    return encrypted_text

def encrypt_text_boxes(text_boxes, shift=3):
    encrypted_text_boxes = []
    
    # Encrypt each text box value using Caesar cipher
    for page in text_boxes:
        encrypted_page = []
        for text in page:
            encrypted_text = caesar_encrypt(text, shift)
            encrypted_page.append(encrypted_text)
        encrypted_text_boxes.append(encrypted_page)
    
    # Display the shift used for encryption
    print("Shift used for Encryption:", shift)
    
    return encrypted_text_boxes
encrypted_boxes = encrypt_text_boxes(text_boxes, shift=3)
print("Encrypted Text Boxes:", encrypted_boxes)
def draw_wrapped_text(draw, text, box, font, fill="black"):
    max_width = box[2] - box[0]
    words = text.split()
    lines = []
    current_line = words[0]

    # Wrap text
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    # Draw text line by line
    y_text = box[1]
    line_height = font.getbbox("A")[3]  # Height based on font size

    for line in lines:
        draw.text((box[0], y_text), line, font=font, fill=fill)
        y_text += line_height
        if y_text > box[3]:  # Stop if text goes beyond the bounding box height
            break
def replace_text_with_encrypted_images(pdf_path, text_boxes, encrypted_text_boxes):
    pdf_document = fitz.open(pdf_path)
    images = pdf_to_images(pdf_path, len(text_boxes))

    for page_num, (image, encrypted_texts) in enumerate(zip(images, encrypted_text_boxes)):
        page = pdf_document[page_num]
        img_with_boxes = image.copy()
        draw = ImageDraw.Draw(img_with_boxes)

        # Start with a smaller font for fitting encrypted text
        font_size = 12
        font = ImageFont.truetype("arial.ttf", font_size)

        # Loop through each text block and replace text with encrypted text
        for idx, block in enumerate(page.get_text("blocks")):
            x0, y0, x1, y1 = block[:4]
            encrypted_text = encrypted_texts[idx]
            
            # Clear the area by drawing a white rectangle over it
            draw.rectangle([x0, y0, x1, y1], fill="white")
            
            # Draw wrapped and scaled encrypted text within the box
            draw_wrapped_text(draw, str(encrypted_text), (x0, y0, x1, y1), font=font, fill="black")
        
        # Display the modified image in Jupyter
        display(img_with_boxes)

    pdf_document.close()
replace_text_with_encrypted_images("dataset/first_two_pages.pdf", text_boxes, encrypted_boxes)



