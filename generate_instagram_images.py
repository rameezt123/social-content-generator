import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import re

UNSPLASH_ACCESS_KEY = "BBNgEUjHpGS-4LxREr1OsW7lmlv433nOl5dK59LDcW4"
INPUT_FILE = "instagram_carousel.txt"
OUTPUT_DIR = "instagram_slides"
IMG_SIZE = (1080, 1080)
OVERLAY_HEIGHT_RATIO = 0.5  # Bottom 50% of image
OVERLAY_COLOR = (0, 0, 0, 180)  # Semi-transparent black
PADDING = 60
HEADLINE_MAX_FONT = 180
COPY_MAX_FONT = 90
MIN_FONT = 24
LINE_SPACING = 10
BRAND_TEXT = "@yourbrand"
BRAND_COLOR = (255, 221, 51)
BRAND_FONT_SIZE = 36

# Font selection helper
from PIL import ImageFont

def get_font(font_size, bold=False):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arialbd.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(path, font_size)
        except Exception:
            continue
    return ImageFont.load_default()

def fetch_unsplash_image(query):
    url = f"https://api.unsplash.com/photos/random?query={requests.utils.quote(query)}&orientation=squarish&client_id={UNSPLASH_ACCESS_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img_url = resp.json()['urls']['regular']
        img_resp = requests.get(img_url, timeout=10)
        img_resp.raise_for_status()
        return Image.open(BytesIO(img_resp.content)).convert('RGB')
    except Exception as e:
        print(f"[Warning] Could not fetch Unsplash image for '{query}': {e}. Using blank background.")
        return Image.new('RGB', IMG_SIZE, color=(30, 30, 30))

def parse_carousel(file_path):
    slides = []
    with open(file_path, 'r') as f:
        content = f.read()
    slide_blocks = re.split(r"---+", content)
    for block in slide_blocks:
        block = block.strip()
        if not block:
            continue
        headline_match = re.search(r'Headline: "([^"]+)"', block)
        copy_match = re.search(r'\*Copy:\*\s*(.*)', block)
        image_desc_match = re.search(r'\*Image Description:\*\s*(.*)', block)
        slides.append({
            "headline": headline_match.group(1).strip() if headline_match else "",
            "copy": copy_match.group(1).strip() if copy_match else "",
            "image_desc": image_desc_match.group(1).strip() if image_desc_match else "science"
        })
    return slides

def wrap_text_by_pixel(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def fit_text_block(draw, text, max_width, max_height, max_font_size, min_font_size=MIN_FONT, bold=False):
    font_size = max_font_size
    while font_size >= min_font_size:
        font = get_font(font_size, bold=bold)
        lines = wrap_text_by_pixel(draw, text, font, max_width)
        total_height = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1]
            total_height += line_height + LINE_SPACING
        if total_height - LINE_SPACING <= max_height:
            return font, lines, total_height - LINE_SPACING
        font_size -= 4
    # Fallback to smallest font
    font = get_font(min_font_size, bold=bold)
    lines = wrap_text_by_pixel(draw, text, font, max_width)
    total_height = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        total_height += line_height + LINE_SPACING
    return font, lines, total_height - LINE_SPACING

def create_slide_image(headline, copy, image_desc, slide_num):
    img = fetch_unsplash_image(image_desc)
    img = img.resize(IMG_SIZE)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img, 'RGBA')
    # Overlay area
    overlay_top = int(IMG_SIZE[1] * (1 - OVERLAY_HEIGHT_RATIO))
    overlay_height = int(IMG_SIZE[1] * OVERLAY_HEIGHT_RATIO)
    overlay_rect = [0, overlay_top, IMG_SIZE[0], IMG_SIZE[1]]
    # Draw semi-transparent overlay
    overlay = Image.new('RGBA', (IMG_SIZE[0], overlay_height), OVERLAY_COLOR)
    img.paste(overlay, (0, overlay_top), overlay)
    # Text area (with padding)
    text_area_left = PADDING
    text_area_top = overlay_top + PADDING
    text_area_width = IMG_SIZE[0] - 2 * PADDING
    text_area_height = overlay_height - 2 * PADDING
    # Split text area: 60% for headline, 40% for copy
    headline_height_max = int(text_area_height * 0.6)
    copy_height_max = text_area_height - headline_height_max
    # Fit headline
    font_headline, headline_lines, headline_block_height = fit_text_block(
        draw, headline, text_area_width, headline_height_max, HEADLINE_MAX_FONT, bold=True)
    # Fit copy
    font_copy, copy_lines, copy_block_height = fit_text_block(
        draw, copy, text_area_width, copy_height_max, COPY_MAX_FONT, bold=False)
    # Center headline in its area
    y = text_area_top + (headline_height_max - headline_block_height) // 2
    for line in headline_lines:
        bbox = draw.textbbox((0, 0), line, font=font_headline)
        line_width = bbox[2] - bbox[0]
        x = text_area_left + (text_area_width - line_width) // 2
        draw.text((x, y), line, font=font_headline, fill=(255,255,255))
        y += bbox[3] - bbox[1] + LINE_SPACING
    # Center copy in its area
    y = text_area_top + headline_height_max + (copy_height_max - copy_block_height) // 2
    for line in copy_lines:
        bbox = draw.textbbox((0, 0), line, font=font_copy)
        line_width = bbox[2] - bbox[0]
        x = text_area_left + (text_area_width - line_width) // 2
        draw.text((x, y), line, font=font_copy, fill=(230,230,230))
        y += bbox[3] - bbox[1] + LINE_SPACING
    # Draw brand at the bottom right
    brand_font = get_font(BRAND_FONT_SIZE, bold=True)
    brand_bbox = draw.textbbox((0, 0), BRAND_TEXT, font=brand_font)
    brand_width = brand_bbox[2] - brand_bbox[0]
    draw.text((IMG_SIZE[0] - brand_width - PADDING, IMG_SIZE[1] - PADDING - BRAND_FONT_SIZE), BRAND_TEXT, font=brand_font, fill=BRAND_COLOR)
    img = img.convert('RGB')
    img.save(os.path.join(OUTPUT_DIR, f"slide_{slide_num}.png"))

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    slides = parse_carousel(INPUT_FILE)
    for idx, slide in enumerate(slides, 1):
        create_slide_image(slide["headline"], slide["copy"], slide["image_desc"], idx)
    print(f"Generated {len(slides)} Instagram slide images in '{OUTPUT_DIR}' directory.")

if __name__ == "__main__":
    main() 