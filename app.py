import json
import re

import requests
import streamlit as st
from google import genai
from google.genai import types

# -------------------- Page setup --------------------

st.set_page_config(page_title="NutriLens | AI Nutrition Assistant", page_icon="🥗", layout="wide")

MODEL_NAME = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")

st.markdown("""

<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
.stApp {background:#F5F8F4;font-family:'DM Sans',sans-serif}
.block-container {max-width:1120px;padding-top:1.5rem;padding-bottom:3rem}
#MainMenu,footer,header {visibility:hidden}
.hero {background:linear-gradient(135deg,#153F2D,#278052);color:white;padding:32px;border-radius:22px;margin-bottom:22px}
.brand {font-family:'Manrope',sans-serif;font-size:34px;font-weight:800}
.hero p {color:#E4F2E7;font-size:16px;line-height:1.7;margin-bottom:0}
.welcome {background:#E9F4E9;border:1px solid #D6E8D6;padding:19px 22px;border-radius:16px;color:#28543A;line-height:1.7;margin-bottom:25px}
.step {color:#378357;font-size:12px;font-weight:700;letter-spacing:1.5px;margin-bottom:5px}
.heading {font-family:'Manrope',sans-serif;color:#193D2B;font-size:25px;font-weight:800;margin-bottom:5px}
.description {color:#718075;margin-bottom:17px;font-size:14px}
.metric {background:white;border:1px solid #DDE8DE;border-radius:16px;padding:19px 16px;min-height:126px;margin-bottom:10px}
.metric-label {font-size:13px;font-weight:600;color:#647368;margin-bottom:12px}
.metric-value {color:#175C38;font-family:'Manrope',sans-serif;font-weight:800;font-size:28px;line-height:1.25}
.metric-unit {color:#7A867D;font-size:12px;margin-top:5px}
.report {background:white;border:1px solid #DDE8DE;border-radius:17px;padding:23px;margin:10px 0 20px 0;line-height:1.8}
.stButton>button {border-radius:11px;min-height:44px;font-weight:700}
.stButton>button[kind="primary"] {background:#23764E;color:white;border-color:#23764E}
[data-testid="stFileUploader"] {background:white;border:1px dashed #A9C9AF;border-radius:14px;padding:12px}
.footer {text-align:center;color:#879188;font-size:12px;padding-top:24px}
@media(max-width:640px){.brand{font-size:28px}.hero{padding:23px}.metric-value{font-size:23px}}
</style>

""", unsafe_allow_html=True)

# -------------------- Gemini helpers --------------------

def get_gemini_client():

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:

        raise ValueError("GEMINI_API_KEY is missing from .streamlit/secrets.toml.")

    return genai.Client(api_key=api_key)

def friendly_error(error):

    msg = str(error)

    low = msg.lower()

    if "429" in msg or "resource_exhausted" in low or "quota" in low:

        return "Gemini API quota reached. Check your API usage or try again when the quota resets."

    if "503" in msg or "unavailable" in low:

        return "Gemini is temporarily busy. Please try again shortly."

    if "401" in msg or "api key" in low:

        return "Please check your Gemini API key in .streamlit/secrets.toml."

    if "404" in msg or "not found" in low:

        return "The configured Gemini model may not be available. Check GEMINI_MODEL in secrets.toml."

    return f"Unable to complete the request: {msg}"

def _clean_json(text):

    """Extract JSON even if the model surrounds it with Markdown fences."""

    text = (text or "").strip()

    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s*```$", "", text)

    start, end = text.find("{"), text.rfind("}")

    if start >= 0 and end > start:

        text = text[start:end + 1]

    return json.loads(text)

def analyze_food(image_bytes, mime_type, extra_instruction=""):
    """Identify the visible meal and return estimated nutrition in a fixed schema."""
    client = get_gemini_client()
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type or "image/jpeg",
    )

    # Constrain the response format so the model is less likely to return
    # incomplete or malformed JSON.
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "food_name": types.Schema(type=types.Type.STRING),
            "portion": types.Schema(type=types.Type.STRING),
            "calories": types.Schema(type=types.Type.NUMBER),
            "protein_g": types.Schema(type=types.Type.NUMBER),
            "carbs_g": types.Schema(type=types.Type.NUMBER),
            "fat_g": types.Schema(type=types.Type.NUMBER),
            "ingredients": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
            ),
            "summary": types.Schema(type=types.Type.STRING),
            "suggestion": types.Schema(type=types.Type.STRING),
            "confidence": types.Schema(
                type=types.Type.STRING,
                enum=["High", "Medium", "Low"],
            ),
        },
        required=[
            "food_name", "portion", "calories", "protein_g", "carbs_g",
            "fat_g", "ingredients", "summary", "suggestion", "confidence",
        ],
    )

    prompt = (
        "Identify the food in this image and estimate nutrition for the entire visible serving. "
        "Return realistic estimates, not exact measurements. Keep text fields short. "
        "If the image is clearly not food, use food_name='Food could not be identified', "
        "set nutrition numbers to 0, and explain why in summary. "
        "Do not invent hidden ingredients."
    )
    if extra_instruction.strip():
        prompt += "\nUser-provided food or portion details: " + extra_instruction.strip()

    last_error = "Gemini did not return a complete nutrition report. Please try again."

    # Retry once if the model returns an empty or invalid response.
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )

            raw = (response.text or "").strip()
            if not raw:
                last_error = "Gemini returned an empty response. Please try again."
                continue

            data = _clean_json(raw)
            for key in ("calories", "protein_g", "carbs_g", "fat_g"):
                value = data.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f"Nutrition field '{key}' was missing or not numeric.")

            if not isinstance(data.get("ingredients"), list):
                data["ingredients"] = []
            data["ingredients"] = [str(item) for item in data["ingredients"][:10]]
            data["food_name"] = str(data.get("food_name", "Identified meal"))
            data["portion"] = str(data.get("portion", "Visible serving; estimated"))
            data["summary"] = str(data.get("summary", "Nutrition values are estimates."))
            data["suggestion"] = str(data.get("suggestion", "Adjust the estimate to your actual portion."))

            confidence = str(data.get("confidence", "Medium")).capitalize()
            data["confidence"] = confidence if confidence in {"High", "Medium", "Low"} else "Medium"
            return data

        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            last_error = f"Gemini returned an incomplete or invalid nutrition report: {exc}"
        except Exception as exc:
            # API, quota, and connectivity errors should be reported to the UI.
            if attempt == 1:
                raise
            last_error = str(exc)

    raise ValueError(last_error)

def format_value(value):

    return "Unavailable" if value is None else f"{value:g}"

def build_telegram_summary(data):

    return "\n".join([

        "🥗 NUTRILENS — NUTRITION REPORT", "",

        f"🍽️ Food: {data['food_name']}",

        f"⚖️ Estimated portion: {data['portion']}",

        f"🥬 Visible ingredients: {', '.join(data['ingredients']) or 'Not specified'}", "",

        "📊 ESTIMATED NUTRITION",

        f"🔥 Calories: {format_value(data['calories'])} kcal",

        f"💪 Protein: {format_value(data['protein_g'])} g",

        f"🌾 Carbohydrates: {format_value(data['carbs_g'])} g",

        f"🥑 Fat: {format_value(data['fat_g'])} g", "",

        f"📝 Summary: {data['summary']}",

        f"💡 Suggestion: {data['suggestion']}",

        f"🔎 Confidence: {data['confidence']}", "",

        "Values are estimates based on the visible image."

    ])

def send_telegram_message(message):

    token = st.secrets.get("TELEGRAM_BOT_TOKEN")

    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:

        raise ValueError("Telegram credentials are missing from .streamlit/secrets.toml.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Telegram limits each message to 4096 characters.

    for start in range(0, len(message), 3900):

        response = requests.post(

            url,

            json={"chat_id": str(chat_id), "text": message[start:start + 3900]},

            timeout=20,

        )

        try:

            result = response.json()

        except ValueError:

            raise RuntimeError(f"Telegram returned an unexpected response (HTTP {response.status_code}).")

        if not response.ok or not result.get("ok"):

            raise RuntimeError(result.get("description", "Telegram message failed."))

def ask_gemini(question, analysis, history):

    client = get_gemini_client()

    conversation = (

        "You are NutriLens, a helpful food and nutrition assistant. Answer the user's question "

        "using the meal analysis below. Nutrition estimates are approximate; do not invent exact values.\n\n"

        + build_telegram_summary(analysis)

        + "\n\nRecent conversation:\n"

    )

    for item in history[-8:]:

        conversation += f"{item['role'].capitalize()}: {item['content']}\n"

    conversation += f"\nUser: {question}\nAssistant:"

    response = client.models.generate_content(

        model=MODEL_NAME,

        contents=conversation,

        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=700),

    )

    if not response.text:

        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()

# -------------------- Session state --------------------
# Store the latest analysis and chat messages between Streamlit reruns.

if "latest_food_analysis" not in st.session_state:

    st.session_state.latest_food_analysis = None

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []

# -------------------- Header and welcome --------------------
# Introduce the app and explain what the user can do.

st.markdown("""

<div class="hero"><div class="brand">🥗 NutriLens</div>

<p>Your AI-powered food and nutrition companion. Discover what's on your plate and understand its estimated nutritional value — one meal at a time.</p></div>

<div class="welcome"><strong>👋 Welcome to NutriLens!</strong><br>

Upload a photo of your meal to identify the visible food, estimate calories and macros, and prepare a report you can send directly to Telegram.</div>

""", unsafe_allow_html=True)

st.markdown('<div class="step">STEP 01</div><div class="heading">📸 Analyze your meal</div><div class="description">Upload a clear photo of your food to estimate its nutrition.</div>', unsafe_allow_html=True)

with st.container(border=True):

    uploaded_file = st.file_uploader("Choose your food photo", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:

        st.image(uploaded_file.getvalue(), caption="Your uploaded meal", use_container_width=True)

    extra_instruction = st.text_input("Optional food or portion details", placeholder="Example: One medium plate of vegetable biryani")

    if st.button("🔍 Analyze My Meal", type="primary", use_container_width=True, disabled=uploaded_file is None):

        with st.spinner("NutriLens is analyzing your meal..."):

            try:

                result = analyze_food(uploaded_file.getvalue(), uploaded_file.type or "image/jpeg", extra_instruction)

                st.session_state.latest_food_analysis = result

                st.session_state.chat_history = []

                st.rerun()

            except Exception as error:

                st.error(friendly_error(error))

# -------------------- Nutrition report --------------------
# Show nutrition metrics, the full report, Telegram sharing, and follow-up chat.

data = st.session_state.latest_food_analysis

if data:

    st.markdown("---")

    st.markdown('<div class="step">STEP 02</div><div class="heading">🍽️ Your nutrition report</div><div class="description">Estimated nutritional values for your uploaded meal.</div>', unsafe_allow_html=True)

    columns = st.columns(4)

    for column, (label, value, unit) in zip(columns, [

        ("🔥 Calories", data["calories"], "kcal"),

        ("💪 Protein", data["protein_g"], "grams"),

        ("🌾 Carbohydrates", data["carbs_g"], "grams"),

        ("🥑 Fat", data["fat_g"], "grams"),

    ]):

        with column:

            st.markdown(

                f'<div class="metric"><div class="metric-label">{label}</div>'

                f'<div class="metric-value">{format_value(value)}</div>'

                f'<div class="metric-unit">{unit}</div></div>',

                unsafe_allow_html=True,

            )

    ingredients = ", ".join(data["ingredients"]) or "Not specified"

    st.markdown(

        f'<div class="report"><div class="step">AI FOOD ANALYSIS</div>'

        f'<h2>{data["food_name"]}</h2><p><strong>Estimated portion:</strong> {data["portion"]}</p>'

        f'<p><strong>Visible ingredients:</strong> {ingredients}</p>'

        f'<p><strong>Summary:</strong> {data["summary"]}</p>'

        f'<p><strong>Suggestion:</strong> {data["suggestion"]}</p>'

        f'<p><strong>Confidence:</strong> {data["confidence"]}</p></div>',

        unsafe_allow_html=True,

    )

    st.caption("Nutrition values are estimates based on the visible image. Actual values depend on portion size, ingredients, and preparation.")

    st.markdown("---")

    st.markdown('<div class="step">STEP 03</div><div class="heading">📲 Send your report to Telegram</div><div class="description">Send this meal analysis directly to your Telegram chat.</div>', unsafe_allow_html=True)

    if st.button("✈️ Send Summary to Telegram", type="primary", use_container_width=True):

        try:

            send_telegram_message(build_telegram_summary(data))

            st.success("Your nutrition report was sent to Telegram!")

        except Exception as error:

            st.error(f"Telegram could not send the report: {error}")

    st.markdown("---")

    st.markdown('<div class="step">STEP 04 · OPTIONAL</div><div class="heading">💬 Ask NutriLens</div><div class="description">Ask follow-up questions about your analyzed meal.</div>', unsafe_allow_html=True)

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    question = st.chat_input("Ask about your meal or its nutrients...")

    if question:

        st.session_state.chat_history.append({"role": "user", "content": question})

        try:

            with st.spinner("NutriLens is preparing an answer..."):

                answer = ask_gemini(question, data, st.session_state.chat_history[:-1])

            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            st.rerun()

        except Exception as error:

            st.error(friendly_error(error))

st.markdown('<div class="footer">Made with 🥗 and AI · NutriLens<br>Nutrition information is an estimate, not a medical diagnosis.</div>', unsafe_allow_html=True)
