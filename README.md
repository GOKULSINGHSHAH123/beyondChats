🔍 Reddit User Persona Generator
This project generates a detailed user persona from a given Reddit profile URL by scraping their posts and comments, summarizing behavioral patterns using Gemini LLM, and saving the output in a citation-backed .txt file and a raw persona file.

📌 Features
Scrapes up to 400 posts and comments from a Reddit user

Uses Google Gemini (via google.generativeai) to analyze Reddit activity

Generates:

🧠 A cited persona (with reference indexes)

✍️ A raw persona (clean format without citations)

Saves output in .txt files, suitable for the assignment requirement

🧰 Tech Stack
Python 3

requests, re, json, google.generativeai

Gemini 2.0 Flash LLM

🚀 Setup Instructions
Clone the repository
git clone https://github.com/GOKULSINGHSHAH123/beyondChats.git
cd reddit-persona-generator


Install dependencies
pip install -r requirements.txt


Set up your Gemini API key

genai.configure(api_key="YOUR_GEMINI_API_KEY")


▶️ How to Run
python reddit_persona.py
When prompted, enter the Reddit profile URL (e.g. https://www.reddit.com/user/kojied/)
Or simply press Enter to use the default user



📁 Output
After execution, the following files will be generated:

Filename	Description
persona_<username>_cited.txt	Persona with citation indexes and sources
persona_<username>_raw.txt	Clean persona (no citation brackets)


📄 Sample Output
✔️ persona_kojied_cited.txt

✔️ persona_kojied_raw.txt

Each cited file includes reference numbers (e.g., [12]) that correspond to specific posts/comments scraped from Reddit.


📎 Notes for BeyondChats Assignment
✅ Meets the assignment requirements:

 Python script to scrape Reddit + generate persona

 Text files output with citations

 Uses LLM (Gemini) for analysis

 Executable with only one command

 Easy to adapt for any Reddit profile


 💡 Example Reddit URLs
Use any public Reddit user like:

https://www.reddit.com/user/kojied/

https://www.reddit.com/user/Hungry-Move-6603/

