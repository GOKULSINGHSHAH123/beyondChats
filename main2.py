import requests
import time
import re
import json
import os
import google.generativeai as genai
from urllib.parse import urlparse, unquote
import os
from dotenv import load_dotenv

load_dotenv() 

api_key = os.getenv("GEMINI_API_KEY")  #This is free api key that why given env file

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

# === ✨ STEP 1: Fetch Reddit Posts & Comments ===
def fetch_reddit_data(username, content_type="comments", delay=1.5):
    base_url = f"https://www.reddit.com/user/{username}/{content_type}/.json"
    headers = {"User-Agent": "PersonaBuilder/1.0 (by /u/AIResearchIntern)"}
    after = None
    all_data = []
    max_items = 400

    while len(all_data) < max_items:
        params = {'after': after} if after else {}
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            if response.status_code == 429:
                print("⚠️ Rate limit hit. Waiting 30 seconds...")
                time.sleep(30)
                continue
            response.raise_for_status()
            data = response.json()

            children = data.get('data', {}).get('children', [])
            if not children:
                break

            for child in children:
                item = child['data']
                if content_type == "comments":
                    text = item.get('body', '').strip()
                    source = f"Comment in r/{item.get('subreddit', 'unknown')}"
                else:
                    title = item.get('title', '').strip()
                    body = item.get('selftext', '').strip()
                    text = f"{title}\n\n{body}".strip()
                    source = f"Post in r/{item.get('subreddit', 'unknown')}"
                if text:
                    all_data.append({
                        "text": text,
                        "source": source,
                        "url": f"https://reddit.com{item.get('permalink', '')}",
                        "timestamp": item.get('created_utc', 0)
                    })

            after = data['data'].get('after')
            if not after:
                break
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Error fetching {content_type}: {str(e)}")
            break

    print(f"✅ Total {content_type} fetched: {len(all_data)}")
    return all_data

# === 📦 STEP 2: Chunk Reddit Data ===
def chunk_data(data_list, chunk_size=25):
    for i in range(0, len(data_list), chunk_size):
        chunk = data_list[i:i + chunk_size]
        indexed_chunk = []
        for idx, item in enumerate(chunk, start=i):
            indexed_chunk.append(f"[{idx}] ({item['source']}) {item['text']}")
        yield indexed_chunk

# === 🧠 STEP 3: Generate Chunk Summaries with Gemini ===
def generate_summaries(data_chunks):
    summaries = []
    for i, chunk in enumerate(data_chunks):
        joined_chunk = "\n\n".join(chunk)
        prompt = f"""
**Task**: Analyze a Reddit user's content to identify personality traits and behavioral patterns. 
**Output Format**: JSON with these keys: traits, communication_style, topics, motivations, frustrations

**Content Batch**:
{joined_chunk}

**Instructions**:
1. Identify 3-5 key personality traits with citation indexes
2. Describe communication style with 2-3 adjectives and citations
3. List 5 most frequent topics/interests with citations
4. Identify 3 main motivations with citations
5. Note 2-3 frustrations with citations

IMPORTANT: Respond ONLY with valid JSON. Do not include any other text.
"""
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            try:
                summary_data = json.loads(response_text)
                summaries.append(summary_data)
                print(f"✅ Summary {i+1} generated")
            except json.JSONDecodeError:
                print(f"⚠️ JSON parse failed for chunk {i+1}. Using fallback.")
                summaries.append({"raw_text": response_text})
        except Exception as e:
            print(f"❌ Gemini error in chunk {i+1}: {str(e)}")
            summaries.append({})
    return summaries

# === 🎭 Persona With Citations ===
def generate_final_persona(summaries, username, combined_data):
    context = "Analysis summaries:\n"
    for i, summary in enumerate(summaries):
        context += f"\n--- Summary {i+1} ---\n"
        context += summary["raw_text"] if "raw_text" in summary else json.dumps(summary, indent=2)

    sample_text = "\n\nSample Content Excerpts:\n"
    for i, item in enumerate(combined_data[:5]):
        sample_text += f"[Sample {i+1}] {item['text'][:200]}...\n"

    final_prompt = f"""
**Task**: Create comprehensive user persona from analysis of Reddit activity

**Username**: {username}
{context}
{sample_text}

**Output Format**:
**Name**: [Realistic generated name]
**Age**: [Estimated age range]
**Occupation**: [Inferred occupation]
**Location**: [Probable location or "Unknown"]
**Digital Tier**: [e.g., Tech Early Adopter, Casual User]
**Personality Archetype**: [e.g., The Analyst, The Helper]

**Behavioral Traits**:
- [Trait 1] [citation indexes]
- [Trait 2] [citation indexes]

**Communication Style**:
[Description] [citation indexes]

**Core Interests**:
1. [Interest 1] [citation indexes]
2. [Interest 2] [citation indexes]

**Motivations & Goals**:
- [Motivation 1] [citation indexes]
- [Motivation 2] [citation indexes]

**Pain Points & Frustrations**:
- [Frustration 1] [citation indexes]
- [Frustration 2] [citation indexes]

**Signature Quote**:
"[Generated quote representing their personality]"

IMPORTANT: Include citation indexes like [12][45]
"""
    response = model.generate_content(final_prompt)
    return response.text

# === 🎭 Persona Without Citations ===
def generate_raw_persona(summaries, username, combined_data):
    context = "Analysis summaries:\n"
    for i, summary in enumerate(summaries):
        context += f"\n--- Summary {i+1} ---\n"
        context += summary["raw_text"] if "raw_text" in summary else json.dumps(summary, indent=2)

    sample_text = "\n\nSample Content Excerpts:\n"
    for i, item in enumerate(combined_data[:5]):
        sample_text += f"[Sample {i+1}] {item['text'][:200]}...\n"

    final_prompt = f"""
**Task**: Create a concise Reddit user persona based on the analysis summaries and content excerpts.

**Username**: {username}
{context}
{sample_text}

**Output Format**:
**Name**: [Realistic name]
**Age**: [Estimated age range]
**Occupation**: [Likely profession]
**Location**: [Probable region]
**Personality Type**: [e.g., The Thinker, The Explorer]

**Traits**:
- Trait 1
- Trait 2

**Communication Style**:
[Short sentence]

**Interests**:
- Interest 1
- Interest 2

**Goals**:
- Goal 1
- Goal 2

**Frustrations**:
- Frustration 1
- Frustration 2

**Signature Quote**:
"A quote reflecting their personality"

IMPORTANT: Do NOT include citation indexes.
"""
    response = model.generate_content(final_prompt)
    return response.text

# === 🔍 Citation Helper ===
def extract_citations(text):
    return list(set(re.findall(r'\[(\d+)\]', text)))

# === 💾 Save Persona with Citations ===
def save_persona(username, persona_output, combined_data):
    filename = f"persona_{username}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Reddit User Persona Analysis: {username}\n")
        f.write("="*50 + "\n\n")
        f.write(persona_output)

        citations = extract_citations(persona_output)
        if citations:
            f.write("\n\n" + "="*50 + "\nCITATION REFERENCES\n" + "="*50 + "\n")
            for idx in sorted(set(int(c) for c in citations if c.isdigit())):
                if idx < len(combined_data):
                    item = combined_data[idx]
                    f.write(f"\n[{idx}] Source: {item['source']}\n")
                    f.write(f"Text: {item['text'][:300]}{'...' if len(item['text']) > 300 else ''}\n")
                    f.write(f"URL: {item['url']}\n")
    print(f"\n✅ Persona saved to {filename}")
    return filename

# === 💾 Save Raw Persona ===
def save_raw_persona(username, persona_output):
    filename = f"persona_{username}_raw.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Raw Reddit Persona for {username}\n")
        f.write("="*50 + "\n\n")
        f.write(persona_output)
    print(f"\n✅ Raw persona saved to {filename}")
    return filename

# === MAIN ===
def extract_username(url):
    path = urlparse(url).path
    username = unquote(path.split('/')[-2] if path.endswith('/') else path.split('/')[-1])
    return username.replace("user/", "").strip()

if __name__ == "__main__":
    default_url = "https://www.reddit.com/user/kojied/"
    user_input = input(f"Enter Reddit profile URL [Enter for default: {default_url}]: ").strip()
    target_url = user_input if user_input else default_url
    username = extract_username(target_url)

    print(f"\n🔍 Analyzing Reddit profile: {username}")
    print("⏳ This may take 3-5 minutes...\n")

    print("📥 Fetching comments...")
    comments = fetch_reddit_data(username, "comments")
    print("📥 Fetching posts...")
    posts = fetch_reddit_data(username, "submitted")
    combined = comments + posts

    if not combined:
        print("❌ No Reddit data found. Exiting.")
        exit()

    print("\n🧠 Analyzing content...")
    chunks = list(chunk_data(combined))
    summaries = generate_summaries(chunks)

    print("\n🎭 Generating persona with citations...")
    persona_with_citations = generate_final_persona(summaries, username, combined)
    save_persona(username + "_cited", persona_with_citations, combined)

    print("\n🧑‍🎤 Generating raw persona without citations...")
    persona_raw = generate_raw_persona(summaries, username, combined)
    save_raw_persona(username, persona_raw)

    print("\n✅ All personas generated successfully!")
