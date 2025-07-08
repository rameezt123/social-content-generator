import sys
import json
import openai

# Set your OpenAI API key
OPENAI_MODEL = "gpt-4o"

# --- Content Generation Functions ---
def generate_podcast_script(summary, api_key):
    prompt = f"""
You are a creative podcast scriptwriter. Using the following scientific article summary, write a compelling podcast script for a 10-minute episode. Make it engaging, conversational, and informative. Include an intro, main discussion, and outro.\n\nSUMMARY:\n{json.dumps(summary, indent=2)}\n\nSCRIPT:
"""
    return call_openai(prompt, api_key)

def generate_instagram_carousel(summary, api_key):
    prompt = f"""
You are a social media strategist. Using the following scientific article summary, create copy for a 5-slide Instagram carousel. For each slide, provide a headline, 1-2 sentences of copy, and a description of an image that would accompany the slide.\n\nSUMMARY:\n{json.dumps(summary, indent=2)}\n\nCAROUSEL:
"""
    return call_openai(prompt, api_key)

def generate_twitter_thread(summary, api_key):
    prompt = f"""
You are a science communicator on Twitter. Using the following scientific article summary, write a Twitter thread of 8 tweets. Make each tweet concise, engaging, and informative.\n\nSUMMARY:\n{json.dumps(summary, indent=2)}\n\nTHREAD:
"""
    return call_openai(prompt, api_key)

def generate_blog_post(summary, api_key):
    prompt = f"""
You are a science blogger. Using the following scientific article summary, write a 1000-word blog post. Make it accessible, engaging, and well-structured, with an introduction, main body, and conclusion.\n\nSUMMARY:\n{json.dumps(summary, indent=2)}\n\nBLOG POST:
"""
    return call_openai(prompt, api_key)

def call_openai(prompt, api_key):
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --- Main Workflow ---
def main():
    if len(sys.argv) < 3:
        print("Usage: python content_generator.py <summary_json> <openai_api_key>")
        sys.exit(1)
    summary_path = sys.argv[1]
    api_key = sys.argv[2]
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    print("Generating podcast script...")
    podcast_script = generate_podcast_script(summary, api_key)
    with open('podcast_script.txt', 'w') as f:
        f.write(podcast_script)

    print("Generating Instagram carousel copy...")
    insta_carousel = generate_instagram_carousel(summary, api_key)
    with open('instagram_carousel.txt', 'w') as f:
        f.write(insta_carousel)

    print("Generating Twitter thread...")
    twitter_thread = generate_twitter_thread(summary, api_key)
    with open('twitter_thread.txt', 'w') as f:
        f.write(twitter_thread)

    print("Generating blog post...")
    blog_post = generate_blog_post(summary, api_key)
    with open('blog_post.txt', 'w') as f:
        f.write(blog_post)

    print("All content generated!")

if __name__ == "__main__":
    main() 