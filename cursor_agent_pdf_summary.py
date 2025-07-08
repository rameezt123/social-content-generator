import os
import sys
import json
import csv
from typing import Any, Dict
import pdfplumber
import openai

# Extract and clean text from PDF
def extract_and_clean_text(pdf_path: str) -> str:
    """Extract and clean text from a PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    # Basic cleaning: remove excessive whitespace
    text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])
    return text

# Use OpenAI's API to get a structured summary (v1.x syntax)
def get_structured_summary(text: str, openai_api_key: str) -> Dict[str, Any]:
    """Send text to OpenAI's GPT-4o model and get a structured summary."""
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
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1024,
        temperature=0.2,
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

# Save output to JSON or CSV
def save_output(data: Dict[str, Any], output_path: str):
    if output_path.endswith('.json'):
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    elif output_path.endswith('.csv'):
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)
    else:
        raise ValueError('Output file must be .json or .csv')

def main():
    if len(sys.argv) < 4:
        print("Usage: python cursor_agent_pdf_summary.py <pdf_path> <openai_api_key> <output_path>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    openai_api_key = sys.argv[2]
    output_path = sys.argv[3]

    print(f"Extracting and cleaning text from {pdf_path}...")
    text = extract_and_clean_text(pdf_path)

    print("Sending text to OpenAI GPT-4o for structured summary...")
    summary = get_structured_summary(text, openai_api_key)

    print(f"Saving output to {output_path}...")
    save_output(summary, output_path)
    print("Done.")

if __name__ == "__main__":
    main() 