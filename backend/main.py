from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "path": file_path}

@app.post("/generate")
def generate_content(filename: str = Form(...)):
    # Placeholder: Call your PDF parser and content generator here
    # For now, just return a dummy response
    # In production, you would call your summarizer and content generator pipeline
    return JSONResponse({
        "instagram": "Instagram copy for " + filename,
        "twitter": "Twitter thread for " + filename,
        "blog": "Blog post for " + filename,
        "podcast": "Podcast script for " + filename
    }) 