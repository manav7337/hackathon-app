import streamlit as st
import os
import json
from openai import OpenAI

# ---- Setup ----
# Option 1: If using env variable (recommended)

with open("hackathon_key_openai.txt", "r") as file:
    api_key = file.read().strip()

os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI(api_key=api_key)

# Option 2: Hardcode for quick test (not safe for production)
# client = OpenAI(api_key="your_api_key_here")

# ---- Functions ----
def summarize(text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a concise summarizer."},
            {"role": "user", "content": f"Summarize this text into 5 bullet points:\n\n{text}"}
        ],
        max_tokens=200,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


import json

def generate_quiz(text: str, difficulty: int = 5):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a teacher who creates multiple-choice quizzes. "
                    "Return output strictly in JSON. Do not include any extra text, explanations, or markdown."
                )
            },
            {
                "role": "user",
                "content": f"""
Create 5 multiple-choice questions from the following text.
Return a JSON array where each object has:
- "question": the question text
- "options": a list of 4 strings, each starting with A), B), C), D)
- "answer": the correct option letter ("A", "B", "C", or "D")

Difficulty: {difficulty}

Text:
{text}
"""
            }
        ],
        max_tokens=700,
        temperature=0.7,
    )

    quiz_json = resp.choices[0].message.content.strip()

    # ---- Auto-clean JSON fences if present ----
    if quiz_json.startswith("```"):
        quiz_json = quiz_json.strip("`").strip()
        if quiz_json.startswith("json"):
            quiz_json = quiz_json[4:].strip()

    # ---- Debugging: show raw response in Streamlit ----
    #st.text_area("Raw quiz response (debug)", quiz_json, height=200)

    try:
        quiz = json.loads(quiz_json)   # convert JSON string → Python list
    except Exception as e:
        st.error(f"⚠️ Could not parse quiz: {e}")
        quiz = []
    return quiz



def translate(text, target_language="Hindi"):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": f"Translate this into {target_language}:\n\n{text}"}
        ],
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()

# ---- Streamlit UI ----
# ---- Streamlit UI ----
st.set_page_config(page_title="AI Content Repurposer", page_icon="✨")
#st.title("AI Content Repurposer")
# ---- Custom styled title ----
st.markdown(
    """
    <h1 style='text-align: center;
               font-size: 60px;
               font-weight: bold;
               background: linear-gradient(90deg, #87CEFA, #1E90FF, #00008B);
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;
               margin-bottom: 0;'>
         AI Content Repurposer 
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    div.stButton > button {
        transition: all 0.4s ease-in-out;
    }
    div.stButton > button:active {
        transform: scale(0.85);
        background-color: #1E90FF !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .streamlit-expanderHeader {
        transition: all 0.4s ease-in-out;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    /* Gradient track */
    div[data-baseweb="slider"] > div:first-child {
        background: linear-gradient(to right, #87CEFA, #1E90FF, #00008B) !important;
        height: 4px !important;      /* keep it thin */
        border-radius: 5px !important;
    }

    /* Slider thumb (circle) */
    div[data-baseweb="slider"] div[role="slider"] {
        background: #1E90FF !important;
        border: 2px solid white !important;
        width: 16px !important;
        height: 16px !important;
        border-radius: 50% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


uploaded_file = st.file_uploader("Choose a text file", type=["txt"])

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
    st.subheader("File Preview")
    st.write(text[:500])  # preview first 500 chars

    # Summarizer
    if st.button("Summarize"):
        summary = summarize(text)
        st.subheader("Summary")
        st.write(summary)

    # Quiz generator with slider
# Quiz generator with slider
difficulty = st.slider("Select quiz difficulty", 1, 10, 5)

# Generate the quiz once and store it in session state
if st.button("Generate Interactive Quiz"):
    st.session_state.quiz = generate_quiz(text, difficulty)
    st.session_state.score = 0
    st.session_state.submitted = [False] * len(st.session_state.quiz)

# If a quiz is already stored, display it
if "quiz" in st.session_state and st.session_state.quiz:
    quiz = st.session_state.quiz
    st.subheader("Interactive Quiz")

    for i, q in enumerate(quiz):
        st.write(f"**Q{i+1}. {q['question']}**")

        # Radio input persists across reruns
        user_answer = st.radio(
            f"Select your answer for Q{i+1}:",
            q["options"],
            key=f"radio_{i}"
        )

        if st.button(f"Submit Q{i+1}", key=f"submit_{i}"):
            if not st.session_state.submitted[i]:
                correct_letter = q["answer"]
                correct_option = [opt for opt in q["options"] if opt.startswith(correct_letter)][0]

                if user_answer and user_answer.startswith(correct_letter):
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Wrong! Correct answer: {correct_option}")

                st.session_state.submitted[i] = True

    st.write(f"### Current Score: {st.session_state.score}/{len(quiz)}")


    # Translator with dropdown
    languages = ["Hindi", "Gujarati", "Tamil", "French", "Spanish", "German", "Kannada"]
    target_language = st.selectbox("Choose target language:", languages)

    if st.button("Translate"):
        translation = translate(text, target_language)
        st.subheader(f"Translation in {target_language}")
        st.write(translation)

    # ---- Process All ----
    if st.button("Process All"):
        summary = summarize(text)
        quiz = generate_quiz(text, difficulty)
        translation = translate(text, target_language)

        st.subheader("Summary")
        st.write(summary)

        st.subheader("Quiz")
        st.write(quiz)

        st.subheader(f"Translation in {target_language}")
        st.write(translation)

        # Combine results
        results = f"""SUMMARY:\n{summary}\n\nQUIZ:\n{quiz}\n\nTRANSLATION ({target_language}):\n{translation}"""

        # Download button
        st.download_button(
            label="📥 Download Results",
            data=results,
            file_name="results.txt",
            mime="text/plain",
        )



