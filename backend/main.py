from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import sys
import tempfile
from typing import Dict, Any, List
import openai
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Allow CORS for local frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Alternative local port
        "https://social-content-generator-frontend.onrender.com",  # Production frontend
        "https://*.onrender.com",  # Any Render subdomain
    ],
    allow_credentials=False,  # Changed to False to allow all origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Get API key from environment variable
def get_openai_api_key():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return api_key

# Extract and clean text from PDF (copied from your existing script)
def extract_and_clean_text(pdf_path: str) -> str:
    """Extract and clean text from a PDF file using pdfplumber."""
    import pdfplumber
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    # Basic cleaning: remove excessive whitespace
    text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])
    return text

# Use OpenAI to get a structured summary
def get_structured_summary(text: str, openai_api_key: str) -> Dict[str, Any]:
    """Send text to OpenAI GPT-4o and get a structured summary."""
    client = openai.OpenAI(api_key=openai_api_key)
    system_prompt = (
        "You are an expert scientific summarizer. "
        "Given the following scientific article text, produce a structured summary in JSON format with the following fields: "
        "'title', 'authors', 'main_findings', 'key_points', 'conclusions', and 'notable_quotes'. "
        "Be concise and accurate. Respond only with the JSON."
    )
    user_prompt = f"Article Text:\n{text[:12000]}\n\n"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    # Extract JSON from response
    import re
    import ast
    content = response.choices[0].message.content if response.choices[0].message.content is not None else ""
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            try:
                return ast.literal_eval(match.group(0))
            except Exception:
                return {"error": "Could not parse JSON from response."}
    return {"error": "No JSON found in response.", "raw_response": content}

# Content generation functions using OpenAI
def generate_podcast_script(summary, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
You are a creative podcast scriptwriter. Using the following scientific article summary, write a compelling podcast script for a 10-minute episode. Make it engaging, conversational, and informative. Include an intro, main discussion, and outro.

SUMMARY:
{json.dumps(summary, indent=2)}

SCRIPT:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content is not None else ""

def generate_instagram_carousel(summary, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
You are a social media strategist. Using the following scientific article summary, create copy for a 5-slide Instagram carousel. For each slide, provide a headline, 1-2 sentences of copy, and a description of an image that would accompany the slide.

SUMMARY:
{json.dumps(summary, indent=2)}

CAROUSEL:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content is not None else ""

def generate_twitter_thread(summary, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
You are a science communicator on Twitter. Using the following scientific article summary, write a Twitter thread of 8 tweets. Make each tweet concise, engaging, and informative.

SUMMARY:
{json.dumps(summary, indent=2)}

THREAD:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content is not None else ""

def generate_blog_post(summary, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
You are a science blogger. Using the following scientific article summary, write a 1000-word blog post. Make it accessible, engaging, and well-structured, with an introduction, main body, and conclusion.

SUMMARY:
{json.dumps(summary, indent=2)}

BLOG POST:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content is not None else ""

def generate_instagram_slides_data(summary, api_key):
    """Generate structured data for Instagram carousel slides"""
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
You are a social media strategist. Using the following scientific article summary, create 5 Instagram carousel slides.
Return ONLY a JSON array with 5 objects, each containing:
- "title": A catchy headline (max 40 characters)
- "subtitle": A brief subtitle (max 60 characters) 
- "body": Main content (max 200 characters)
- "background_color": A hex color code for the background

Make it engaging, educational, and visually appealing.

SUMMARY:
{json.dumps(summary, indent=2)}

Return ONLY the JSON array:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        content = response.choices[0].message.content if response.choices[0].message.content is not None else ""
        # Extract JSON array
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return json.loads(content)
    except Exception as e:
        print(f"Error parsing Instagram slides data: {e}")
        # Return default slides if parsing fails
        return [
            {"title": "Key Finding", "subtitle": "Main discovery", "body": "Important research finding", "background_color": "#FF6B6B"},
            {"title": "Why It Matters", "subtitle": "Real-world impact", "body": "How this affects daily life", "background_color": "#4ECDC4"},
            {"title": "The Science", "subtitle": "Behind the research", "body": "Scientific explanation", "background_color": "#45B7D1"},
            {"title": "Key Takeaways", "subtitle": "What to remember", "body": "Main points to remember", "background_color": "#96CEB4"},
            {"title": "Learn More", "subtitle": "Next steps", "body": "Where to find more information", "background_color": "#FFEAA7"}
        ]

def create_instagram_slide(slide_data, slide_number):
    """Create a single Instagram slide image"""
    # Instagram dimensions: 1080x1080 pixels
    width, height = 1080, 1080
    
    # Create image with background color
    bg_color = slide_data.get("background_color", "#FF6B6B")
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Use default font to avoid font loading issues
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    
    # Calculate text positions
    title = slide_data.get("title", f"Slide {slide_number}")
    subtitle = slide_data.get("subtitle", "")
    body = slide_data.get("body", "")
    
    # Draw title (centered, top)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = 150
    draw.text((title_x, title_y), title, fill="white", font=title_font)
    
    # Draw subtitle (centered, below title)
    if subtitle:
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        subtitle_y = title_y + 100
        draw.text((subtitle_x, subtitle_y), subtitle, fill="white", font=subtitle_font)
    
    # Draw body text (centered, middle)
    if body:
        # Wrap text to fit width
        max_width = width - 100
        words = body.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=body_font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw wrapped text
        body_y = height // 2 - (len(lines) * 40) // 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=body_font)
            line_width = bbox[2] - bbox[0]
            line_x = (width - line_width) // 2
            draw.text((line_x, body_y + i * 40), line, fill="white", font=body_font)
    
    # Add slide number indicator
    slide_text = f"{slide_number}/5"
    slide_bbox = draw.textbbox((0, 0), slide_text, font=body_font)
    slide_width = slide_bbox[2] - slide_bbox[0]
    slide_x = width - slide_width - 50
    slide_y = height - 80
    draw.text((slide_x, slide_y), slide_text, fill="white", font=body_font)
    
    return image

def generate_instagram_images(summary, api_key):
    """Generate Instagram carousel images and return as bytes"""
    try:
        # Get slide data
        slides_data = generate_instagram_slides_data(summary, api_key)
        
        # Create images
        images = []
        for i, slide_data in enumerate(slides_data, 1):
            image = create_instagram_slide(slide_data, i)
            images.append(image)
        
        # Create ZIP file with all images
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for i, image in enumerate(images, 1):
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                zip_file.writestr(f'instagram_slide_{i}.png', img_buffer.getvalue())
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating Instagram images: {e}")
        return None

def parse_instagram_carousel(carousel_text):
    """Parse the Instagram carousel copy into a list of slides with headline, copy, and image description."""
    import re
    slides = []
    slide_blocks = re.split(r"---+", carousel_text)
    for block in slide_blocks:
        block = block.strip()
        if not block:
            continue
        # More flexible regex for headline, copy, and image description
        headline_match = re.search(r'Headline:\s*["“]?([^"\n]+)["”]?', block, re.IGNORECASE)
        copy_match = re.search(r'Copy:\s*(.*)', block, re.IGNORECASE)
        image_desc_match = re.search(r'Image Description:\s*(.*)', block, re.IGNORECASE)
        slides.append({
            "headline": headline_match.group(1).strip() if headline_match else "",
            "copy": copy_match.group(1).strip() if copy_match else "",
            "image_desc": image_desc_match.group(1).strip() if image_desc_match else ""
        })
    # Debug: print parsed slides
    print("Parsed Instagram slides:", slides)
    return slides

def create_instagram_slide_from_copy(slide, slide_num):
    """Create an Instagram slide image using the actual copy (headline, copy, image description)."""
    # For now, use a simple background color
    width, height = 1080, 1080
    image = Image.new('RGB', (width, height), (70, 130, 180))
    draw = ImageDraw.Draw(image)
    # Headline
    headline = slide.get("headline", "")
    copy = slide.get("copy", "")
    # Draw headline (top)
    font_headline = ImageFont.load_default()
    y = 80
    draw.text((60, y), headline, fill="white", font=font_headline)
    y += 80
    # Draw copy (below headline)
    font_copy = ImageFont.load_default()
    draw.text((60, y), copy, fill="white", font=font_copy)
    # Optionally, add slide number
    slide_text = f"{slide_num}/5"
    draw.text((width - 120, height - 80), slide_text, fill="white", font=font_copy)
    return image

def generate_instagram_images_from_copy(carousel_text):
    """Generate Instagram images from the actual Instagram carousel copy text."""
    slides = parse_instagram_carousel(carousel_text)
    images = []
    for idx, slide in enumerate(slides, 1):
        image = create_instagram_slide_from_copy(slide, idx)
        images.append(image)
    # Create ZIP file with all images
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for i, image in enumerate(images, 1):
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            zip_file.writestr(f'instagram_slide_{i}.png', img_buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and return the filename"""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename) if file.filename else None
    if not file_path:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file name"}
        )
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "path": file_path}

@app.post("/generate")
def generate_content(filename: str = Form(...)):
    """Generate social media content from uploaded PDF"""
    try:
        # Get API key
        api_key = get_openai_api_key()
        
        # Construct file path
        if not filename:
            return JSONResponse(
                status_code=400,
                content={"error": "Filename is required"}
            )
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": f"File {filename} not found"}
            )
        
        # Extract and clean text from PDF
        print(f"Extracting text from {file_path}...")
        text = extract_and_clean_text(file_path)
        
        # Get structured summary
        print("Getting structured summary...")
        summary = get_structured_summary(text, api_key)
        
        if "error" in summary:
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to generate summary: {summary['error']}"}
            )
        
        # Generate content for each platform
        print("Generating content...")
        instagram = generate_instagram_carousel(summary, api_key)
        twitter = generate_twitter_thread(summary, api_key)
        blog = generate_blog_post(summary, api_key)
        podcast = generate_podcast_script(summary, api_key)
        
        return JSONResponse({
            "instagram": instagram,
            "twitter": twitter,
            "blog": blog,
            "podcast": podcast,
            "summary": summary
        })
        
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate content: {str(e)}"}
        )

@app.post("/generate-instagram-images")
def generate_instagram_images_endpoint(filename: str = Form(...)):
    """Generate Instagram carousel images from uploaded PDF using the actual Instagram copy."""
    try:
        # Get API key
        api_key = get_openai_api_key()
        # Construct file path
        if not filename:
            return JSONResponse(
                status_code=400,
                content={"error": "Filename is required"}
            )
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": f"File {filename} not found"}
            )
        # Extract and clean text from PDF
        print(f"Extracting text from {file_path}...")
        text = extract_and_clean_text(file_path)
        # Get structured summary
        print("Getting structured summary...")
        summary = get_structured_summary(text, api_key)
        if "error" in summary:
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to generate summary: {summary['error']}"}
            )
        # Generate Instagram carousel copy (the actual text)
        print("Generating Instagram carousel copy...")
        carousel_copy = generate_instagram_carousel(summary, api_key)
        # Generate images from the actual copy
        print("Generating Instagram images from copy...")
        images_zip = generate_instagram_images_from_copy(carousel_copy)
        if images_zip is None:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to generate Instagram images"}
            )
        # Return the ZIP file using StreamingResponse
        return StreamingResponse(
            io.BytesIO(images_zip),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=instagram_carousel.zip"}
        )
    except Exception as e:
        print(f"Error generating Instagram images: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate Instagram images: {str(e)}"}
        )

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Social Content Generator API", "status": "running", "docs": "/docs"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Backend is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
