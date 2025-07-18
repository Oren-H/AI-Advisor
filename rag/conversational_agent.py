import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

course_info_json = """
[
  {
    "course_code": "COMS 4771",
    "title": "Machine Learning",
    "dept": "COMS",
    "credits": 3.0,
    "times": "Tue/Thu 1:10-2:25 PM",
    "instructor": "John Paisley",
    "prerequisites": "Linear Algebra, Probability",
    "description": "Theoretical foundations and algorithms for machine learning, including supervised and unsupervised learning.",
    "link": "https://bulletin.columbia.edu/coms4771"
  },
  {
    "course_code": "COMS 4111",
    "title": "Introduction to Databases",
    "dept": "COMS",
    "credits": 3.0,
    "times": "Mon/Wed 2:40-3:55 PM",
    "instructor": "Eugene Wu",
    "prerequisites": "Data Structures",
    "description": "Covers relational databases, SQL, and database design.",
    "link": "https://bulletin.columbia.edu/coms4111"
  },
  {
    "course_code": "STAT 4201",
    "title": "Probability Theory",
    "dept": "STAT",
    "credits": 4.0,
    "times": "Tue/Thu 10:10-11:25 AM",
    "instructor": "Tian Zheng",
    "prerequisites": "Calculus III",
    "description": "Rigorous introduction to probability, random variables, and distributions.",
    "link": "https://bulletin.columbia.edu/stat4201"
  },
  {
    "course_code": "COMS 3157",
    "title": "Advanced Programming",
    "dept": "COMS",
    "credits": 3.0,
    "times": "Mon/Wed 4:10-5:25 PM",
    "instructor": "Stephen Edwards",
    "prerequisites": "Data Structures",
    "description": "C programming, Unix tools, and software engineering practices.",
    "link": "https://bulletin.columbia.edu/coms3157"
  },
  {
    "course_code": "APMA 4300",
    "title": "Numerical Methods",
    "dept": "APMA",
    "credits": 3.0,
    "times": "Fri 1:10-3:40 PM",
    "instructor": "David Keyes",
    "prerequisites": "Linear Algebra, Calculus II",
    "description": "Numerical solutions to mathematical problems, including linear systems and differential equations.",
    "link": "https://bulletin.columbia.edu/apma4300"
  }
]
"""

SYSTEM_PROMPT_TEMPLATE = """You are **Classify**, an AI peer-advisor that helps Columbia students compare and choose classes.

## Your Mission
1. **Parse the five course objects in COURSE_INFO**.
2. **Summarize** the key details (title, level of math/theory, schedule, professor, prerequisites, credits).
3. **Highlight differences** (e.g. depth of math, project vs. proof focus, workload, grading style).
4. Offer **tailored suggestions** or next steps based on the user's goals, schedule, background, and preferences.
5. If the user's request is vague or contradictory, **ask a brief clarifying question** before giving recommendations.
6. Use **concise, friendly prose**—imagine you're a knowledgeable junior helping a first-year friend.
7. When helpful, format information with:
   * bullet lists (•) for per-course summaries,
   * **bold** for crucial distinctions,
   * *italics* for caveats or tips,
   * inline links supplied in the data (do **not** invent URLs).

## Constraints
- **Do not** output the raw COURSE_INFO block.
- Rely only on the five courses provided; if the user asks about something else, politely say you only have those five right now.
- Keep responses under **≈250 words** unless the user explicitly asks for more detail.
- Never fabricate prerequisites, meeting times, or professor names.

## Example call structure (for reference only—do not print):
SYSTEM: (this prompt)
ASSISTANT: 👍
COURSE_INFO:
[
  {
    "course_code": "COMS 4771",
    "title": "Machine Learning",
    "dept": "COMS",
    "credits": 3.0,
    "times": "Tue/Thu 1:10-2:25 PM",
    "instructor": "John Paisley",
    "prerequisites": "Linear Algebra, Probability",
    "description": "Theoretical foundations and algorithms …",
    "link": "https://..."
  },
  …(4 more)…
]
USER: "Find me an ML course that's super mathy"

## Begin the conversation now.
"""
user_query = "Find me an ML course that's super mathy"
messages = [
    {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
    # Optionally: {"role": "assistant", "content": "👍"}  # tiny ack keeps first turn short
    {"role": "system", "content": f"COURSE_INFO:\n{course_info_json}"},
    {"role": "user", "content": user_query},
]
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
)
print(response.choices[0].message.content)