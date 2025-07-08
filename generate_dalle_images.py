import sys
import os
import openai
import re
import requests

INPUT_FILE = "instagram_carousel.txt"
OUTPUT_DIR = "dalle_images"
IMG_SIZE = 1080

# Parse the carousel file for image descriptions
def parse_carousel(file_path):
    slides = []
    with open(file_path, 'r') as f:
        content = f.read()
    slide_blocks = re.split(r"---+", content)
    for block in slide_blocks:
        block = block.strip()
        if not block:
            continue
        image_desc_match = re.search(r'\*Image Description:\*\s*(.*)', block)
        slides.append({
            "image_desc": image_desc_match.group(1).strip() if image_desc_match else "science"
        })
    return slides

def generate_dalle_image(prompt, api_key, idx):
    client = openai.OpenAI(api_key=api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    img_resp = requests.get(image_url)
    out_path = os.path.join(OUTPUT_DIR, f"dalle_slide_{idx}.png")
    with open(out_path, "wb") as f:
        f.write(img_resp.content)
    print(f"Saved {out_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_dalle_images.py <openai_api_key>")
        sys.exit(1)
    api_key = sys.argv[1]
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    slides = parse_carousel(INPUT_FILE)
    for idx, slide in enumerate(slides, 1):
        generate_dalle_image(slide["image_desc"], api_key, idx)

if __name__ == "__main__":
    main() 