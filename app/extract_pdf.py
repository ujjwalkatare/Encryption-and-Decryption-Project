# # from PyPDF2 import PdfReader, PdfWriter
# # import fitz  # PyMuPDF
# # from PIL import Image, ImageDraw, ImageFont
# # from cryptography.fernet import Fernet
# # from IPython.display import display

# # def split_first_two_pages(input_pdf_path, output_pdf_path):
# #     # Open the input PDF
# #     reader = PdfReader(input_pdf_path)
# #     writer = PdfWriter()

# #     # Add the first two pages to the writer
# #     for page_num in range(2):  # 0 and 1 for the first two pages
# #         writer.add_page(reader.pages[page_num])

# #     # Save the new PDF with the first two pages
# #     with open(output_pdf_path, "wb") as output_pdf:
# #         writer.write(output_pdf)
# #     print(f"The first two pages have been saved to {output_pdf_path}")

# # # Example usage
# # split_first_two_pages("question_paper_pdf_dataset.pdf", "first_two_pages.pdf")

# # # Function to convert PDF pages to images
# # def pdf_to_images(pdf_path, num_pages=2):
# #     pdf_document = fitz.open(pdf_path)
# #     images = []

# #     for page_num in range(num_pages):
# #         page = pdf_document[page_num]
# #         pix = page.get_pixmap()
# #         img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
# #         images.append(img)

# #     pdf_document.close()
# #     return images
# # # Function to add bounding boxes to text in an image
# # def draw_bounding_boxes(image, page):
# #     img_with_boxes = image.copy()
# #     draw = ImageDraw.Draw(img_with_boxes)

# #     for block in page.get_text("blocks"):
# #         x0, y0, x1, y1 = block[:4]
# #         draw.rectangle([x0, y0, x1, y1], outline="red", width=2)

# #     return img_with_boxes

# # # Example usage
# # def display_pdf_text_with_boxes(pdf_path, num_pages=2):
# #     pdf_document = fitz.open(pdf_path)
# #     images = pdf_to_images(pdf_path, num_pages)

# #     for i, image in enumerate(images):
# #         page = pdf_document[i]
# #         img_with_boxes = draw_bounding_boxes(image, page)
# #         display(img_with_boxes)

# #     pdf_document.close()

    
# # def get_text_boxwise(pdf_path, num_pages=2):
# #     pdf_document = fitz.open(pdf_path)
# #     all_text_boxes = []

# #     for page_num in range(num_pages):
# #         page = pdf_document[page_num]
# #         text_boxes = []
        
# #         # Extract each text block
# #         for block in page.get_text("blocks"):
# #             x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]
# #             text_boxes.append(text.strip())  # Add text without leading/trailing spaces

# #         all_text_boxes.append(text_boxes)

# #     pdf_document.close()
# #     return all_text_boxes
# # # Use the function to display the first two pages with bounding boxes
# # display_pdf_text_with_boxes("first_two_pages.pdf")
# # def caesar_encrypt(text, shift):
# #     encrypted_text = ""
# #     for char in text:
# #         if char.isalpha():
# #             shift_base = ord('A') if char.isupper() else ord('a')
# #             encrypted_char = chr((ord(char) - shift_base + shift) % 26 + shift_base)
# #             encrypted_text += encrypted_char
# #         else:
# #             encrypted_text += char
# #     return encrypted_text

# # def encrypt_text_boxes(text_boxes, shift=3):
# #     encrypted_text_boxes = []
    
# #     # Encrypt each text box value using Caesar cipher
# #     for page in text_boxes:
# #         encrypted_page = []
# #         for text in page:
# #             encrypted_text = caesar_encrypt(text, shift)
# #             encrypted_page.append(encrypted_text)
# #         encrypted_text_boxes.append(encrypted_page)
    
# #     # Display the shift used for encryption
# #     print("Shift used for Encryption:", shift)
    
# #     return encrypted_text_boxes



# # def draw_wrapped_text(draw, text, box, font, fill="black"):
# #     max_width = box[2] - box[0]
# #     words = text.split()
# #     lines = []
# #     current_line = words[0]

# #     # Wrap text
# #     for word in words[1:]:
# #         test_line = f"{current_line} {word}"
# #         if draw.textlength(test_line, font=font) <= max_width:
# #             current_line = test_line
# #         else:
# #             lines.append(current_line)
# #             current_line = word
# #     lines.append(current_line)

# #     # Draw text line by line
# #     y_text = box[1]
# #     line_height = font.getbbox("A")[3]  # Height based on font size

# #     for line in lines:
# #         draw.text((box[0], y_text), line, font=font, fill=fill)
# #         y_text += line_height
# #         if y_text > box[3]:  # Stop if text goes beyond the bounding box height
# #             break
# # # Function to replace text with encrypted text in the image
# # def replace_text_with_encrypted_images(pdf_path, text_boxes, encrypted_text_boxes):
# #     pdf_document = fitz.open(pdf_path)
# #     images = pdf_to_images(pdf_path, len(text_boxes))

# #     for page_num, (image, encrypted_texts) in enumerate(zip(images, encrypted_text_boxes)):
# #         page = pdf_document[page_num]
# #         img_with_boxes = image.copy()
# #         draw = ImageDraw.Draw(img_with_boxes)

# #         # Start with a smaller font for fitting encrypted text
# #         font_size = 12
# #         font = ImageFont.truetype("arial.ttf", font_size)

# #         # Loop through each text block and replace text with encrypted text
# #         for idx, block in enumerate(page.get_text("blocks")):
# #             x0, y0, x1, y1 = block[:4]
# #             encrypted_text = encrypted_texts[idx]
            
# #             # Clear the area by drawing a white rectangle over it
# #             draw.rectangle([x0, y0, x1, y1], fill="white")
            
# #             # Draw wrapped and scaled encrypted text within the box
# #             draw_wrapped_text(draw, str(encrypted_text), (x0, y0, x1, y1), font=font, fill="black")
        
# #         # Display the modified image in Jupyter
# #         display(img_with_boxes)

# #     pdf_document.close()
# # replace_text_with_encrypted_images("first_two_pages.pdf", text_boxes, encrypted_boxes)
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from cryptography.fernet import Fernet
from IPython.display import display
import os

# def split_first_two_pages(input_pdf_path, output_pdf_path):
#     # Open the input PDF
#     reader = PdfReader(input_pdf_path)
#     writer = PdfWriter()

#     # Add the first two pages to the writer
#     for page_num in range(2):  # 0 and 1 for the first two pages
#         writer.add_page(reader.pages[page_num])

#     # Save the new PDF with the first two pages
#     with open(output_pdf_path, "wb") as output_pdf:
#         writer.write(output_pdf)
#     print(f"The first two pages have been saved to {output_pdf_path}")

# # Example usage
# split_first_two_pages("dataset/question_paper_pdf_dataset.pdf", "first_two_pages.pdf")

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

# Function to add bounding boxes to text in an image
def draw_bounding_boxes(image, page):
    img_with_boxes = image.copy()
    draw = ImageDraw.Draw(img_with_boxes)

    for block in page.get_text("blocks"):
        x0, y0, x1, y1 = block[:4]
        draw.rectangle([x0, y0, x1, y1], outline="red", width=2)

    return img_with_boxes

# Example usage
def display_pdf_text_with_boxes(pdf_path, num_pages=2):
    pdf_document = fitz.open(pdf_path)
    images = pdf_to_images(pdf_path, num_pages)

    for i, image in enumerate(images):
        page = pdf_document[i]
        img_with_boxes = draw_bounding_boxes(image, page)
        display(img_with_boxes)

    pdf_document.close()

# Function to extract text boxes from PDF
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
# Use the function to display the first two pages with bounding boxes
display_pdf_text_with_boxes("first_two_pages.pdf")

text_boxes = get_text_boxwise("first_two_pages.pdf")
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

# Function to replace text with encrypted text in the image
# def replace_text_with_encrypted_images(pdf_path, text_boxes, encrypted_text_boxes):
#     pdf_document = fitz.open(pdf_path)
#     images = pdf_to_images(pdf_path, len(text_boxes))

#     for page_num, (image, encrypted_texts) in enumerate(zip(images, encrypted_text_boxes)):
#         page = pdf_document[page_num]
#         img_with_boxes = image.copy()
#         draw = ImageDraw.Draw(img_with_boxes)

#         # Start with a smaller font for fitting encrypted text
#         font_size = 12
#         font = ImageFont.truetype("arial.ttf", font_size)

#         # Loop through each text block and replace text with encrypted text
#         for idx, block in enumerate(page.get_text("blocks")):
#             x0, y0, x1, y1 = block[:4]
#             encrypted_text = encrypted_texts[idx]
            
#             # Clear the area by drawing a white rectangle over it
#             draw.rectangle([x0, y0, x1, y1], fill="white")
            
#             # Draw wrapped and scaled encrypted text within the box
#             draw_wrapped_text(draw, str(encrypted_text), (x0, y0, x1, y1), font=font, fill="black")
        
#         # Display the modified image in Jupyter
#         display(img_with_boxes)

#     pdf_document.close()
    
    
#     replace_text_with_encrypted_images("first_two_pages.pdf", text_boxes, encrypted_boxes)
def replace_text_with_encrypted_images(pdf_path, text_boxes, encrypted_text_boxes,encrypted_file_path):
    # function logic

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
    replace_text_with_encrypted_images(pdf_path, text_boxes, encrypted_text_boxes,encrypted_file_path)

    
    
def encrypt(text, shift=3):
    """Encrypt the given text using Caesar Cipher with a shift key."""
    encrypted_text = ""

    for char in text:
        # Encrypt uppercase letters
        if char.isupper():
            encrypted_text += chr((ord(char) + shift - 65) % 26 + 65)
        # Encrypt lowercase letters
        elif char.islower():
            encrypted_text += chr((ord(char) + shift - 97) % 26 + 97)
        # Keep non-alphabet characters as is
        else:
            encrypted_text += char

    return encrypted_text
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using PyMuPDF."""
    document = fitz.open(pdf_path)
    text_blocks = []

    for page in document:
        # Extract blocks of text from each page
        blocks = page.get_text("blocks")
        text_blocks.extend(blocks)
    
    document.close()
    return text_blocks
def encrypt_text_blocks(text_blocks, shift=3):
    """Encrypt each text block using Caesar Cipher."""
    encrypted_blocks = []
    
    for block in text_blocks:
        # Encrypt the text (block[4] contains the actual text of the block)
        encrypted_text = encrypt(block[4], shift)  # Encrypt the text using Caesar Cipher
        encrypted_blocks.append(encrypted_text)
    
    return encrypted_blocks


# Example usage
# text_boxes = get_text_boxwise("first_two_pages.pdf")
# encrypted_boxes = encrypt_text_boxes(text_boxes)
# replace_text_with_encrypted_images("first_two_pages.pdf", text_boxes, encrypted_boxes)
