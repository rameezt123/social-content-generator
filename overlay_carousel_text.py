import os
import re
from PIL import Image, ImageDraw, ImageFont

INPUT_FILE = "instagram_carousel.txt"
IMG_DIR = "dalle_images"
OUTPUT_DIR = "final_slides"
IMG_SIZE = (1080, 1080)
OVERLAY_HEIGHT_RATIO = 1/3  # Bottom third
OVERLAY_COLOR = (0, 0, 0, 180)
LINE_SPACING = 10
MAX_FONT_SIZE = 200
MIN_FONT_SIZE = 24
PADDING = 20  # Minimal padding
FONT_PATH = "DejaVuSans-Bold.ttf"  # Must be in project directory
DEBUG = True

# Font selection helper
def get_font(font_size):
    if os.path.exists(FONT_PATH):
        return ImageFont.truetype(FONT_PATH, font_size)
    else:
        print(f"[WARNING] Font file {FONT_PATH} not found. Using default font (may be tiny).")
        return ImageFont.load_default()

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
        slides.append({
            "headline": headline_match.group(1).strip() if headline_match else "",
            "copy": copy_match.group(1).strip() if copy_match else ""
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

def fit_text_block(draw, headline, copy, max_width, max_height):
    font_size = MAX_FONT_SIZE
    while font_size >= MIN_FONT_SIZE:
        font = get_font(font_size)
        # Wrap headline and copy
        headline_lines = wrap_text_by_pixel(draw, headline, font, max_width)
        copy_lines = wrap_text_by_pixel(draw, copy, font, max_width)
        # Measure total height
        total_height = 0
        for line in headline_lines + copy_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            total_height += bbox[3] - bbox[1] + LINE_SPACING
        total_height -= LINE_SPACING  # Remove last spacing
        if total_height <= max_height:
            print(f"[DEBUG] Using font size {font_size} for text block height {total_height}px")
            return font, headline_lines, copy_lines, total_height, font_size
        font_size -= 4
    # Fallback to smallest font
    font = get_font(MIN_FONT_SIZE)
    headline_lines = wrap_text_by_pixel(draw, headline, font, max_width)
    copy_lines = wrap_text_by_pixel(draw, copy, font, max_width)
    total_height = 0
    for line in headline_lines + copy_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total_height += bbox[3] - bbox[1] + LINE_SPACING
    total_height -= LINE_SPACING
    print(f"[DEBUG] Fallback to min font size {MIN_FONT_SIZE} for text block height {total_height}px")
    return font, headline_lines, copy_lines, total_height, MIN_FONT_SIZE

def overlay_text_on_image(img_path, headline, copy, out_path):
    img = Image.open(img_path).convert('RGBA')
    draw = ImageDraw.Draw(img, 'RGBA')
    overlay_height = int(IMG_SIZE[1] * OVERLAY_HEIGHT_RATIO)
    overlay_top = IMG_SIZE[1] - overlay_height
    # Draw semi-transparent overlay
    overlay = Image.new('RGBA', (IMG_SIZE[0], overlay_height), OVERLAY_COLOR)
    img.paste(overlay, (0, overlay_top), overlay)
    # Text area (full overlay, minimal padding)
    text_area_left = PADDING
    text_area_top = overlay_top + PADDING
    text_area_width = IMG_SIZE[0] - 2 * PADDING
    text_area_height = overlay_height - 2 * PADDING
    # Debug: draw rectangles
    if DEBUG:
        draw.rectangle([0, overlay_top, IMG_SIZE[0], IMG_SIZE[1]], outline=(255,0,0), width=3)
        draw.rectangle([text_area_left, text_area_top, text_area_left+text_area_width, text_area_top+text_area_height], outline=(0,255,0), width=3)
    # Fit text block
    font, headline_lines, copy_lines, total_text_height, font_size = fit_text_block(
        draw, headline, copy, text_area_width, text_area_height)
    # Center text block vertically
    y = text_area_top + (text_area_height - total_text_height) // 2
    # Draw headline
    for line in headline_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = text_area_left + (text_area_width - line_width) // 2
        draw.text((x, y), line, font=font, fill=(255,255,255))
        y += bbox[3] - bbox[1] + LINE_SPACING
    # Draw copy
    for line in copy_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = text_area_left + (text_area_width - line_width) // 2
        draw.text((x, y), line, font=font, fill=(255,255,255))
        y += bbox[3] - bbox[1] + LINE_SPACING
    img = img.convert('RGB')
    img.save(out_path)
    print(f"Saved {out_path}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    slides = parse_carousel(INPUT_FILE)
    for idx, slide in enumerate(slides, 1):
        img_path = os.path.join(IMG_DIR, f"dalle_slide_{idx}.png")
        out_path = os.path.join(OUTPUT_DIR, f"final_slide_{idx}.png")
        overlay_text_on_image(img_path, slide["headline"], slide["copy"], out_path)
    print(f"All slides saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 