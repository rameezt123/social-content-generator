from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import sys
import tempfile
from typing import Dict, Any
import openai

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
    allow_credentials=True,
    allow_methods=["*"],
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
    content = response.choices[0].message.content
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
    return response.choices[0].message.content.strip()

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
    return response.choices[0].message.content.strip()

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
    return response.choices[0].message.content.strip()

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
    return response.choices[0].message.content.strip()

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and return the filename"""
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
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