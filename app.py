import html
import json
import re

import pandas as pd
import requests
import streamlit as st
from google import genai
from google.genai import types

import diary
import health
from food_classifier import (
    ClassifierError,
    classify_food_image,
    classify_food_image_local,
    local_classifier_available,
    local_model_info,
    prepare_image,
    summarize_predictions,
)
from nutrition_data import estimate_for_portion, lookup

# -------------------- Page setup --------------------

st.set_page_config(page_title="NutriLens | AI Nutrition Assistant", page_icon="🥗", layout="wide")

# Appearance selector: switch between Light and Dark from the sidebar.
if "nutrilens_theme" not in st.session_state:
    st.session_state.nutrilens_theme = "Light"

selected_theme = st.sidebar.selectbox(
    "🎨 Appearance",
    ["Light", "Dark"],
    key="nutrilens_theme",
    help="Switch NutriLens between light and dark appearance.",
)


MODEL_NAME = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")

# Food classifier service (pretrained ViT running in Google Colab, see colab/ folder).
# Both values are optional: without CLASSIFIER_URL the app still works with Gemini only.
CLASSIFIER_URL = str(st.secrets.get("CLASSIFIER_URL", "")).strip().rstrip("/")
CLASSIFIER_TOKEN = str(st.secrets.get("CLASSIFIER_TOKEN", "")).strip()
LOW_CONFIDENCE = 0.40  # below this, warn that the classifier is unsure

theme_css = """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
:root {
 color-scheme: __COLOR_SCHEME__;
 --page: __PAGE__; --surface: __SURFACE__; --surface-soft: __SURFACE_SOFT__;
 --text: __TEXT__; --text-strong: __TEXT_STRONG__; --muted: __MUTED__;
 --border: __BORDER__; --border-strong: __BORDER_STRONG__;
 --accent-strong: __ACCENT_STRONG__; --welcome-bg: __WELCOME_BG__;
 --welcome-text: __WELCOME_TEXT__; --input-bg: __INPUT_BG__; --shadow: __SHADOW__;
}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"] {
 background:var(--page)!important;color:var(--text)!important;font-family:'DM Sans',sans-serif;
}
.block-container{max-width:1120px;padding:2rem 2rem 3.5rem}
#MainMenu,footer{visibility:hidden}
h1,h2,h3,h4,p,label,.stMarkdown,.stCaption,[data-testid="stWidgetLabel"] p{color:var(--text)!important}
.hero{background:linear-gradient(135deg,#153F2D,#278052);color:#fff!important;padding:34px;border-radius:22px;margin-bottom:22px;box-shadow:0 8px 24px rgba(0,0,0,.12)}
.hero *{color:#fff!important}
.brand{font-family:'Manrope',sans-serif;font-size:36px;font-weight:800;letter-spacing:-.7px}
.hero p{color:#E4F2E7!important;font-size:16px;line-height:1.7;margin:8px 0 0}
.welcome{background:var(--welcome-bg);border:1px solid var(--border);padding:20px 23px;border-radius:16px;color:var(--welcome-text)!important;line-height:1.7;margin-bottom:28px}
.welcome *{color:var(--welcome-text)!important}
.step{color:#278052!important;font-size:11px;font-weight:800;letter-spacing:1.6px;margin-bottom:6px}
.heading{font-family:'Manrope',sans-serif;color:var(--text-strong)!important;font-size:26px;font-weight:800;margin-bottom:5px}
.description{color:var(--muted)!important;margin-bottom:18px;font-size:14px}
[data-testid="stFileUploader"]{background:var(--surface);border:1px dashed var(--border-strong);border-radius:15px;padding:14px}
[data-testid="stFileUploader"] *,[data-testid="stFileUploaderDropzone"] *{color:var(--text)!important}
.stTextInput input,.stTextArea textarea,[data-baseweb="select"]>div,[data-testid="stNumberInput"] input{color:var(--text)!important;background:var(--input-bg)!important;border-color:var(--border-strong)!important}
input::placeholder,textarea::placeholder{color:var(--muted)!important}
[data-testid="stWidgetLabel"] p{color:var(--text)!important;font-weight:600}
.metric{background:var(--surface);border:1px solid var(--border);border-radius:17px;padding:20px 17px;min-height:130px;margin-bottom:10px;box-shadow:0 3px 12px var(--shadow)}
.metric-label{font-size:13px;font-weight:700;color:var(--muted)!important;margin-bottom:12px}
.metric-value{color:var(--accent-strong)!important;font-family:'Manrope',sans-serif;font-weight:800;font-size:30px;line-height:1.25}
.metric-unit{color:var(--muted)!important;font-size:12px;margin-top:5px}
.report{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:25px;margin:12px 0 20px;line-height:1.8;color:var(--text)!important;box-shadow:0 3px 14px var(--shadow)}
.report h2,.report p,.report strong,.report div,.report span{color:var(--text)!important}
.report h2{font-family:'Manrope',sans-serif;color:var(--text-strong)!important;font-size:27px;font-weight:800;margin:8px 0 14px}
.report strong{color:var(--accent-strong)!important}
.stButton>button,[data-testid="stFormSubmitButton"] button{border-radius:12px;min-height:46px;font-weight:700;background:var(--surface);color:var(--text)!important;border:1px solid var(--border-strong)}
.stButton>button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#23764E!important;color:#fff!important;border-color:#23764E!important}
.stButton>button[kind="primary"]:hover{background:#195F3D!important;border-color:#195F3D!important}
[data-testid="stAlert"]{border-radius:12px}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{color:var(--text)!important}
[data-testid="stChatInput"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:14px!important}
[data-testid="stChatInput"] textarea{color:var(--text)!important;background:var(--input-bg)!important}
[data-testid="stChatMessage"]{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px}
button[data-baseweb="tab"]{color:var(--muted)!important;font-weight:600}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--accent-strong)!important}
[data-testid="stProgress"] p{color:var(--text)!important}
[data-testid="stSidebar"]{background:var(--surface-soft)!important}
[data-testid="stSidebar"] *{color:var(--text)!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{color:var(--text)!important}
.footer{text-align:center;color:var(--muted)!important;font-size:12px;padding-top:28px}
@media(max-width:640px){.block-container{padding:1rem 1rem 2rem}.brand{font-size:29px}.hero{padding:24px}.heading{font-size:22px}.metric{padding:16px 13px;min-height:112px}.metric-value{font-size:24px}.report{padding:18px}}

/* NutriLens Studio visual upgrade */
.stApp,[data-testid="stAppViewContainer"]{
 background:
 radial-gradient(ellipse at 12% 8%,rgba(47,166,106,.11),transparent 32%),
 radial-gradient(ellipse at 88% 28%,rgba(91,173,139,.09),transparent 30%),
 var(--page)!important;
}
.block-container{max-width:1240px;padding:2.2rem 2.2rem 5rem;animation:nlPageIn .65s ease both}
@keyframes nlPageIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes nlFloat{0%,100%{transform:translate(0,0)}50%{transform:translate(16px,-12px)}}
@keyframes nlShimmer{0%{background-position:0% 50%}100%{background-position:200% 50%}}
@keyframes nlFadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.hero{
 position:relative;isolation:isolate;overflow:hidden;min-height:260px;
 display:flex;flex-direction:column;justify-content:center;
 padding:clamp(30px,5vw,58px);margin:0 0 24px;border-radius:25px;color:#fff!important;
 background:linear-gradient(90deg,rgba(7,30,20,.94),rgba(8,42,27,.78) 55%,rgba(9,38,27,.32)),
 url('https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=1800&q=85') center/cover,
 linear-gradient(135deg,#123b29,#23764e);
 box-shadow:0 20px 55px rgba(0,0,0,.18)
}
.hero:before,.hero:after{content:"";position:absolute;z-index:-1;pointer-events:none;border-radius:50%;filter:blur(2px)}
.hero:before{width:310px;height:310px;right:5%;top:-170px;background:rgba(111,221,159,.28);animation:nlFloat 8s ease-in-out infinite}
.hero:after{width:220px;height:220px;right:27%;bottom:-165px;background:rgba(41,154,103,.28);animation:nlFloat 10s ease-in-out infinite reverse}
.hero *{color:#fff!important}
.hero-kicker{display:inline-flex;width:max-content;padding:7px 12px;border:1px solid rgba(255,255,255,.25);border-radius:999px;background:rgba(255,255,255,.10);font-size:11px;font-weight:700;letter-spacing:1.5px}
.brand{font-family:'Manrope',sans-serif;font-size:clamp(36px,5vw,58px);font-weight:800;letter-spacing:-1.8px;line-height:1.08;margin-top:18px}
.brand-accent{color:#A6E8C1!important}
.hero p{max-width:660px;color:#E2F3E8!important;font-size:16px;line-height:1.8;margin:13px 0 0}
.hero-foot{display:flex;flex-wrap:wrap;gap:9px;margin-top:22px}
.hero-chip{padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:12px;color:#fff!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:20px!important;box-shadow:0 8px 28px var(--shadow);transition:box-shadow .25s ease}
[data-testid="stVerticalBlockBorderWrapper"]:hover{box-shadow:0 13px 36px var(--shadow)}
[data-testid="stFileUploader"]{background:var(--surface-soft);border:1.5px dashed var(--border-strong);border-radius:17px;padding:16px;transition:border-color .2s ease}
[data-testid="stFileUploader"]:hover{border-color:#2FA66A}
[data-testid="stImage"] img{border-radius:18px;box-shadow:0 12px 30px var(--shadow)}
.metric{border-radius:19px;box-shadow:0 7px 22px var(--shadow);transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;animation:nlFadeUp .55s ease both}
.metric:before{content:"";position:absolute;left:0;top:0;width:100%;height:3px;background:linear-gradient(90deg,#238653,#8ADBA9,#238653);background-size:200% 100%;animation:nlShimmer 5s linear infinite}
.metric:hover{transform:translateY(-5px);border-color:var(--border-strong);box-shadow:0 14px 30px var(--shadow)}
.metric-value{font-size:clamp(26px,3vw,34px);letter-spacing:-.8px}
.report{border-radius:20px;box-shadow:0 8px 28px var(--shadow);animation:nlFadeUp .6s ease both}
.stButton>button,[data-testid="stFormSubmitButton"] button{border-radius:13px;transition:transform .18s ease,box-shadow .18s ease}
.stButton>button:hover,[data-testid="stFormSubmitButton"] button:hover{transform:translateY(-2px);box-shadow:0 8px 20px var(--shadow)}
.stButton>button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:linear-gradient(110deg,#176B43,#2FA66A,#176B43)!important;background-size:200% 100%!important;color:#fff!important;border:0!important;box-shadow:0 8px 20px rgba(35,118,78,.2)}
[data-testid="stChatInput"]{border-radius:16px!important;box-shadow:0 8px 24px var(--shadow)}
[data-testid="stChatMessage"]{border-radius:16px}
@media(max-width:760px){.block-container{padding:1rem 1rem 4rem}.hero{min-height:220px;padding:25px}.brand{font-size:38px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
</style>"""

theme_palettes = {
    "Light": {
        "__COLOR_SCHEME__": "light", "__PAGE__": "#F5F8F4",
        "__SURFACE__": "#FFFFFF", "__SURFACE_SOFT__": "#EAF2EA",
        "__TEXT__": "#263B2E", "__TEXT_STRONG__": "#193D2B",
        "__MUTED__": "#647368", "__BORDER__": "#DDE8DE",
        "__BORDER_STRONG__": "#A9C9AF", "__ACCENT_STRONG__": "#175C38",
        "__WELCOME_BG__": "#E9F4E9", "__WELCOME_TEXT__": "#28543A",
        "__INPUT_BG__": "#FFFFFF", "__SHADOW__": "rgba(25,61,43,.05)",
    },
    "Dark": {
        "__COLOR_SCHEME__": "dark", "__PAGE__": "#101813",
        "__SURFACE__": "#19251D", "__SURFACE_SOFT__": "#202F25",
        "__TEXT__": "#E5EEE7", "__TEXT_STRONG__": "#F2F7F3",
        "__MUTED__": "#B1C0B5", "__BORDER__": "#34483A",
        "__BORDER_STRONG__": "#526B59", "__ACCENT_STRONG__": "#8DD6A6",
        "__WELCOME_BG__": "#20382A", "__WELCOME_TEXT__": "#DCEFE1",
        "__INPUT_BG__": "#19251D", "__SHADOW__": "rgba(0,0,0,.22)",
    },
}

for token, value in theme_palettes[selected_theme].items():
    theme_css = theme_css.replace(token, value)

st.markdown(theme_css, unsafe_allow_html=True)

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
    """Parse a JSON object from Gemini, tolerating Markdown fences/prose."""
    if not text:
        raise ValueError("Gemini returned an empty response.")

    candidate = str(text).strip()
    candidate = re.sub(r"^\s*```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s*```\s*$", "", candidate)

    # First try the complete response as-is.
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Then extract the outermost JSON object if explanatory text surrounds it.
    first = candidate.find("{")
    last = candidate.rfind("}")
    if first >= 0 and last > first:
        parsed = json.loads(candidate[first:last + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Gemini's response was incomplete JSON. Please retry.")

def get_predictions(image_bytes):
    """Run the configured local or remote classifier. Returns (predictions, notice).

    A classifier problem never stops the app: Gemini can still analyse the image,
    so we return (None, notice) and show the notice to the user.
    """
    try:
        if CLASSIFIER_URL:
            # Optional: model running in Google Colab behind an ngrok URL.
            return classify_food_image(image_bytes, CLASSIFIER_URL, CLASSIFIER_TOKEN), None
        if local_classifier_available():
            # Model running on this computer (needs torch + transformers installed).
            return classify_food_image_local(image_bytes), None
    except ClassifierError as error:
        return None, ("warning", f"{error} Continuing with Gemini only.")
    return None, ("info", "Food classifier is not set up, so only Gemini was used. "
                          "Install torch and transformers (see README) to enable it.")

def model_caption():
    """Describe which model made the prediction."""
    pretrained = ("Predicted by a pretrained model (yfh/food, ViT fine-tuned on Food-101 by its author). "
                  "We did not train it, and it only knows 101 food categories.")
    if CLASSIFIER_URL:
        return pretrained + " It ran in Google Colab."
    info = local_model_info()
    if info["source"] != "custom":
        return pretrained
    report = info["report"] or {}
    text = f"Predicted by our own model: {report.get('base_model', 'a pretrained Vision Transformer')} fine-tuned on Food-101 (transfer learning)."
    try:
        text += f" Accuracy measured on {int(report['eval_images'])} held-out test images: {float(report['validation_accuracy']):.1%}."
    except (KeyError, TypeError, ValueError):
        pass
    return text + " It only knows 101 food categories."

def render_classifier_panel(data):
    """Show the notice (if any) and the top-3 classifier predictions."""
    notice = st.session_state.get("classifier_notice")
    if notice:
        getattr(st, notice[0])(notice[1])

    predictions = data.get("classifier_predictions")
    if not predictions:
        return

    top = predictions[0]
    # The Food-101 classifier always chooses from its fixed 101 labels.
    # Its top label is only a suggestion, never the final meal identification.
    st.markdown(
        '<div class="step">MODEL SUGGESTIONS · FOOD-101 CLASSIFIER</div>'
        '<div class="description">These are visual guesses from the pretrained model, not confirmed food identification.</div>',
        unsafe_allow_html=True,
    )
    for item in predictions:
        st.progress(
            min(max(item["score"], 0.0), 1.0),
            text=f'{html.escape(str(item["label"]).replace("_", " ").title())} — {item["score"]:.1%}',
        )

    if top["score"] < LOW_CONFIDENCE:
        st.warning(
            "Low classifier confidence. Do not treat the top suggestion as the food name. "
            "This dish may not match the model's 101 categories; use the Gemini image analysis below."
        )
    st.caption(model_caption())

def _safe_post(url, **kwargs):
    """requests.post that never leaks the Telegram bot token inside an error message."""
    try:
        return requests.post(url, **kwargs)
    except requests.RequestException:
        raise RuntimeError("Could not reach Telegram. Check your internet connection and try again.") from None

def analyze_food(image_bytes, mime_type, extra_instruction="", predictions=None):
    """Identify the meal and estimate nutrition using Gemini structured output."""
    client = get_gemini_client()
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type or "image/jpeg",
    )

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
        "You are NutriLens, an image-based food and nutrition assistant. "
        "Identify the visible food and estimate nutrition for the whole visible serving. "
        "Return only the fields in the supplied JSON schema. Keep every text field concise. "
        "Use realistic approximate values; do not claim laboratory precision or invent hidden ingredients. "
        "If the image is not food or cannot be identified, set food_name to "
        "'Food could not be identified', set all nutrition numbers to 0, and explain briefly."
    )
    if extra_instruction.strip():
        prompt += "\nUser-provided dish or portion details: " + extra_instruction.strip()[:500]
    if predictions:
        prompt += (
            "\nClassifier suggestions (only visual hints, may be wrong): "
            + summarize_predictions(predictions)
            + ". Do not force these labels if the image shows another food."
        )

    last_error = "Gemini did not return a complete nutrition report. Please try again."

    for attempt in range(2):
        try:
            request_prompt = prompt
            if attempt == 1:
                request_prompt += (
                    "\nIMPORTANT: Return a compact, complete JSON object. "
                    "Keep summary and suggestion to one short sentence each. "
                    "Do not include Markdown or any text outside the JSON."
                )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[request_prompt, image_part],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )

            # The SDK may expose parsed structured output. Prefer it over
            # reparsing response.text, which can be empty or truncated.
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if hasattr(parsed, "model_dump"):
                    data = parsed.model_dump()
                elif isinstance(parsed, dict):
                    data = parsed
                else:
                    data = dict(parsed)
            else:
                raw = getattr(response, "text", None)
                if not raw:
                    feedback = getattr(response, "prompt_feedback", None)
                    finish = getattr(response, "candidates", None)
                    detail = ""
                    if finish:
                        try:
                            detail = f" Finish reason: {finish[0].finish_reason}."
                        except Exception:
                            pass
                    last_error = "Gemini returned no usable text." + detail
                    continue
                data = _clean_json(raw)

            if not isinstance(data, dict):
                raise ValueError("Gemini returned data in an unexpected format.")

            # Validate and normalize all required values before rendering.
            for key in ("calories", "protein_g", "carbs_g", "fat_g"):
                value = data.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f"Nutrition field '{key}' was missing or invalid.")

            ingredients = data.get("ingredients", [])
            if not isinstance(ingredients, list):
                ingredients = []
            data["ingredients"] = [str(item)[:80] for item in ingredients[:10]]
            data["food_name"] = str(data.get("food_name") or "Identified meal")[:120]
            data["portion"] = str(data.get("portion") or "Visible serving; estimated")[:160]
            data["summary"] = str(data.get("summary") or "Nutrition values are estimates.")[:500]
            data["suggestion"] = str(data.get("suggestion") or "Adjust the estimate to your actual portion.")[:500]

            confidence = str(data.get("confidence", "Medium")).capitalize()
            data["confidence"] = confidence if confidence in {"High", "Medium", "Low"} else "Medium"

            # Energy consistency check (Atwater factors):
            # protein = 4 kcal/g, carbohydrate = 4 kcal/g, fat = 9 kcal/g.
            # Keep Gemini's original estimate for transparency, but use the
            # macro-derived value for the dashboard and diary when they differ
            # materially. This prevents contradictory displayed totals.
            gemini_calories = float(data["calories"])
            macro_calories = (
                float(data["protein_g"]) * 4.0
                + float(data["carbs_g"]) * 4.0
                + float(data["fat_g"]) * 9.0
            )
            difference = abs(gemini_calories - macro_calories)
            tolerance = max(50.0, macro_calories * 0.10)

            data["gemini_calories"] = round(gemini_calories)
            data["macro_calculated_calories"] = round(macro_calories)
            data["calorie_adjusted"] = difference > tolerance

            if data["calorie_adjusted"]:
                data["calories"] = round(macro_calories)
            else:
                # Small differences are expected from rounding and food-label
                # conventions; retain Gemini's estimate in that case.
                data["calories"] = round(gemini_calories)

            return data

        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            last_error = f"Gemini returned an incomplete or invalid nutrition report: {exc}"
        except Exception as exc:
            last_error = friendly_error(exc)
            if attempt == 1:
                raise RuntimeError(last_error) from exc

    raise ValueError(last_error)

def format_value(value):

    return "Unavailable" if value is None else f"{value:g}"

def build_telegram_summary(data):

    return "\n".join([

        "🥗 NUTRILENS — NUTRITION REPORT", "",

        f"🍽️ Food: {data['food_name']}",

        *([f"🧠 Classifier (top 3): {summarize_predictions(data['classifier_predictions'])}"]
          if data.get("classifier_predictions") else []),

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

        response = _safe_post(

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

# -------------------- Diary, profile and diet coach helpers --------------------

def _index(options, value, default=0):
    """Position of `value` in `options` (used to pre-select saved form values)."""
    return options.index(value) if value in options else default

def build_diary_summary(entries, day_totals, target):
    lines = ["🥗 NUTRILENS — TODAY'S DIARY", ""]
    for item in entries:
        lines.append(f"• {item['meal']}: {item['food']} — {round(item['calories'])} kcal")
    total_line = f"🔥 Total: {day_totals['calories']} kcal"
    if target:
        total_line += f" (daily target {target['target']} kcal)"
    lines += ["", total_line,
              f"💪 Protein: {day_totals['protein_g']:g} g",
              f"🌾 Carbohydrates: {day_totals['carbs_g']:g} g",
              f"🥑 Fat: {day_totals['fat_g']:g} g", "",
              "Values are estimates, not medical measurements."]
    return "\n".join(lines)

def get_diet_advice(profile, target, today_entries, week, extra=""):
    """Ask Gemini for short, practical diet advice based on the user's own numbers."""
    client = get_gemini_client()
    day_totals = diary.totals(today_entries)
    foods = "; ".join(f"{e['meal']}: {e['food']} (~{round(e['calories'])} kcal)" for e in today_entries) or "nothing logged yet"
    week_text = ", ".join(f"{d['day'][5:]}: {d['calories']} kcal" for d in week)
    prompt = (
        "You are NutriLens, a friendly nutrition coach inside a student project. Give practical, "
        "non-judgemental advice using ONLY the numbers below. All values are estimates.\n\n"
        f"Profile: {profile['sex']}, age {profile['age']}, BMI {target['bmi']} ({target['bmi_category']}), "
        f"activity: {profile['activity']}.\n"
        f"Goal: {profile['goal']}. Daily calorie target: {target['target']} kcal.\n"
        f"Food preferences or restrictions (respect these): {profile.get('preferences') or 'none stated'}.\n"
        f"Today's log: {foods}.\n"
        f"Today's totals: {day_totals['calories']} kcal, protein {day_totals['protein_g']:g} g, "
        f"carbs {day_totals['carbs_g']:g} g, fat {day_totals['fat_g']:g} g.\n"
        f"Last 7 days (calories): {week_text}.\n"
        f"The user also asks: {extra.strip() or 'nothing extra'}.\n\n"
        "Write, in simple language and under 220 words:\n"
        "1. One sentence on how today and this week compare with the target.\n"
        "2. Three practical suggestions for the rest of today or tomorrow.\n"
        "3. One healthier swap based on something they actually logged (skip if nothing was logged).\n"
        "4. One short reminder that these are estimates.\n"
        "Do not diagnose conditions. Do not suggest eating below the daily target. If the user mentions a "
        "medical condition, tell them to speak to a doctor or dietitian."
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=700),
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

if "classifier_notice" not in st.session_state:

    st.session_state.classifier_notice = None

# The diary lives in a small local SQLite file (nutrilens.db) next to app.py.
try:
    diary.init_db()
    DIARY_ERROR = None
except Exception as error:
    DIARY_ERROR = str(error)

if "profile" not in st.session_state:

    st.session_state.profile = None if DIARY_ERROR else diary.load_profile()

if "diet_advice" not in st.session_state:

    st.session_state.diet_advice = None

# -------------------- Header and welcome --------------------
# Introduce the app and explain what the user can do.

st.markdown("""

<div class="hero">
<div class="hero-kicker">✦ AI-POWERED FOOD INTELLIGENCE</div>
<div class="brand">Nutri<span class="brand-accent">Lens.</span> 🥗</div>
<p>See your food differently. Turn a simple meal photo into food insights, nutrition estimates and smarter everyday choices.</p>
<div class="hero-foot">
<span class="hero-chip">✦ Food recognition</span>
<span class="hero-chip">◉ Nutrition insights</span>
<span class="hero-chip">♡ Daily wellness</span>
</div>
</div>

<div class="welcome"><strong>👋 Welcome to NutriLens!</strong><br>

Upload a meal photo to explore its visible ingredients, estimate calories and macros, and save or share your nutrition report.</div>

""", unsafe_allow_html=True)

st.markdown('<div class="step">STEP 01</div><div class="heading">📸 Analyze your meal</div><div class="description">Upload a clear photo of your food to estimate its nutrition.</div>', unsafe_allow_html=True)

with st.container(border=True):

    uploaded_file = st.file_uploader("Choose your food photo", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:

        st.image(uploaded_file.getvalue(), caption="Your uploaded meal", width="stretch")

    extra_instruction = st.text_input("Optional food or portion details", placeholder="Example: One medium plate of vegetable biryani")

    if st.button("🔍 Analyze My Meal", type="primary", width="stretch", disabled=uploaded_file is None):

        with st.spinner("NutriLens is analyzing your meal..."):

            try:

                # 1) Validate and shrink the photo locally (Pillow).
                image_bytes, mime = prepare_image(uploaded_file.getvalue())

                # 2) Classify with the pretrained ViT running in Colab (optional step).
                predictions, notice = get_predictions(image_bytes)

                # 3) Gemini estimates nutrition, using the classifier output as a hint.
                result = analyze_food(image_bytes, mime, extra_instruction, predictions)

                result["classifier_predictions"] = predictions

                st.session_state.classifier_notice = notice

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

    render_classifier_panel(data)

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

    if data.get("calorie_adjusted"):
        st.info(
            "Calorie consistency check: Gemini estimated "
            f"{data['gemini_calories']} kcal, but the protein, carbohydrate, "
            f"and fat values calculate to {data['macro_calculated_calories']} kcal "
            "using the standard 4/4/9 method. NutriLens displays the "
            "macro-calculated value so the report is internally consistent. "
            "All values remain approximate."
        )
    else:
        st.caption(
            "Calories and macronutrients are AI estimates. Small differences "
            "can occur because of rounding and food composition."
        )

    ingredients = ", ".join(data["ingredients"]) or "Not specified"
    food_name_html = html.escape(str(data["food_name"]))
    portion_html = html.escape(str(data["portion"]))
    ingredients_html = html.escape(ingredients)
    summary_html = html.escape(str(data["summary"]))
    suggestion_html = html.escape(str(data["suggestion"]))
    confidence_html = html.escape(str(data["confidence"]))

    st.markdown(
        f'<div class="report"><div class="step">AI FOOD ANALYSIS</div>'
        f'<h2>{food_name_html}</h2><p><strong>Estimated portion:</strong> {portion_html}</p>'
        f'<p><strong>Visible ingredients:</strong> {ingredients_html}</p>'
        f'<p><strong>Summary:</strong> {summary_html}</p>'
        f'<p><strong>Suggestion:</strong> {suggestion_html}</p>'
        f'<p><strong>Confidence:</strong> {confidence_html}</p></div>',
        unsafe_allow_html=True,
    )

    st.caption("Nutrition values are estimates based on the visible image. Actual values depend on portion size, ingredients, and preparation.")

    st.markdown("---")

    st.markdown('<div class="step">STEP 03</div><div class="heading">📲 Send your report to Telegram</div><div class="description">Send this meal analysis directly to your Telegram chat.</div>', unsafe_allow_html=True)

    if st.button("✈️ Send Summary to Telegram", type="primary", width="stretch"):

        try:

            send_telegram_message(build_telegram_summary(data))

            st.success("Your nutrition report was sent to Telegram!")

        except Exception as error:

            st.error(f"Telegram could not send the report: {error}")

    st.markdown("---")

    st.markdown('<div class="step">STEP 04</div><div class="heading">📒 Add to your food diary</div><div class="description">Save this meal to today\'s diary so NutriLens can track your daily intake.</div>', unsafe_allow_html=True)

    top_predictions = data.get("classifier_predictions") or []
    top_label = top_predictions[0]["label"] if top_predictions else None
    table_record = lookup(top_label) if top_label else None

    diary_options = ["AI estimate for the whole visible serving (Gemini)"]
    if table_record:
        diary_options.append(f"Reference table: {top_label} × portion in grams")
    diary_choice = st.radio("Which estimate should be saved?", diary_options)
    diary_meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])

    if diary_choice.startswith("Reference table"):
        grams = st.number_input("Portion (grams)", min_value=10, max_value=2000,
                                value=int(table_record["serving_g"]), step=10, key=f"diary_grams_{top_label}")
        new_entry = {"food": top_label, "source": "table", **estimate_for_portion(top_label, grams)}
    else:
        new_entry = {"food": data["food_name"], "source": "gemini", "grams": None,
                     "calories": data["calories"], "protein_g": data["protein_g"],
                     "carbs_g": data["carbs_g"], "fat_g": data["fat_g"]}

    st.caption(f"Will save ≈ {new_entry['calories']:g} kcal · protein {new_entry['protein_g']:g} g · "
               f"carbs {new_entry['carbs_g']:g} g · fat {new_entry['fat_g']:g} g (estimates).")

    if st.button("➕ Add to today's diary", type="primary", width="stretch",
                 disabled=new_entry["calories"] <= 0 or DIARY_ERROR is not None):

        try:

            diary.add_entry(new_entry["food"], diary_meal, new_entry["calories"], new_entry["protein_g"],
                            new_entry["carbs_g"], new_entry["fat_g"], new_entry["source"], new_entry["grams"])

            st.success(f"Added {new_entry['food']} (about {new_entry['calories']:g} kcal) to today's diary. Scroll down to see your totals.")

        except Exception as error:

            st.error(f"Could not save to the diary: {error}")

    st.markdown("---")

    st.markdown('<div class="step">STEP 05 · OPTIONAL</div><div class="heading">💬 Ask NutriLens</div><div class="description">Ask follow-up questions about your analyzed meal.</div>', unsafe_allow_html=True)

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

# -------------------- Diary, goals and diet coach --------------------
# Works even before a meal has been analysed.

st.markdown("---")

st.markdown('<div class="step">MY NUTRILENS</div><div class="heading">📊 Diary, goals and diet coach</div><div class="description">Track what you eat, set a daily calorie target and get AI diet advice.</div>', unsafe_allow_html=True)

if DIARY_ERROR:

    st.error(f"The food diary is unavailable: {DIARY_ERROR}")

else:

    tab_diary, tab_profile, tab_coach = st.tabs(["📒 Today's diary", "👤 My profile & goal", "🥗 Diet coach"])

    # The profile tab runs first so the other tabs see any change made in this run.
    with tab_profile:

        saved = st.session_state.profile or {}
        sex_options = ["Female", "Male"]
        activity_options = list(health.ACTIVITY_LEVELS)
        goal_options = list(health.GOALS)

        with st.form("profile_form"):

            col_a, col_b = st.columns(2)
            sex = col_a.selectbox("Sex (used by the calorie formula)", sex_options, index=_index(sex_options, saved.get("sex")))
            age = col_b.number_input("Age", min_value=10, max_value=100, value=int(saved.get("age", 22)))
            height_cm = col_a.number_input("Height (cm)", min_value=100.0, max_value=230.0, value=float(saved.get("height_cm", 165.0)), step=1.0)
            weight_kg = col_b.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(saved.get("weight_kg", 60.0)), step=0.5)
            activity = st.selectbox("Activity level", activity_options, index=_index(activity_options, saved.get("activity"), 1))
            goal = st.selectbox("Goal", goal_options, index=_index(goal_options, saved.get("goal"), 1))
            preferences = st.text_input("Food preferences or restrictions (optional)", value=saved.get("preferences", ""),
                                        placeholder="Example: vegetarian, no peanuts")
            profile_saved = st.form_submit_button("💾 Save profile", type="primary")

        if profile_saved:

            new_profile = {"sex": sex, "age": int(age), "height_cm": float(height_cm), "weight_kg": float(weight_kg),
                           "activity": activity, "goal": goal, "preferences": preferences.strip()}

            try:

                diary.save_profile(new_profile)

            except Exception as error:

                st.error(f"Could not save the profile: {error}")

            else:

                st.session_state.profile = new_profile
                st.session_state.diet_advice = None
                st.success("Profile saved.")

        target = health.daily_target(st.session_state.profile) if st.session_state.profile else None

        if target:

            stat_cols = st.columns(4)
            stat_cols[0].metric("BMI", f"{target['bmi']}", target["bmi_category"], delta_color="off")
            stat_cols[1].metric("BMR (at rest)", f"{target['bmr']} kcal")
            stat_cols[2].metric("Maintenance", f"{target['maintenance']} kcal")
            stat_cols[3].metric("Daily target", f"{target['target']} kcal")

            if not target["adult"]:

                st.warning("These formulas are meant for adults. If you are under 18, please ask a doctor or dietitian for a target.")

            if target["floor_applied"]:

                st.info("Your target was raised to a commonly used safe minimum. Please do not eat below it without medical advice.")

            st.caption("Calculated with the Mifflin-St Jeor equation. A general estimate, not medical advice.")

        else:

            st.caption("Save your details to get a daily calorie target.")

    with tab_diary:

        todays = diary.entries_for_day()
        day_totals = diary.totals(todays)

        metric_cols = st.columns(4)
        metric_cols[0].metric("🔥 Calories today", f"{day_totals['calories']} kcal")
        metric_cols[1].metric("💪 Protein", f"{day_totals['protein_g']:g} g")
        metric_cols[2].metric("🌾 Carbs", f"{day_totals['carbs_g']:g} g")
        metric_cols[3].metric("🥑 Fat", f"{day_totals['fat_g']:g} g")

        if target:

            eaten, goal_kcal = day_totals["calories"], target["target"]
            st.progress(min(eaten / goal_kcal, 1.0), text=f"{eaten} of {goal_kcal} kcal daily target")

            if eaten > goal_kcal:

                st.warning(f"About {eaten - goal_kcal} kcal over today's target.")

            else:

                st.caption(f"About {goal_kcal - eaten} kcal left for today.")

        else:

            st.info("Save your profile in the next tab to see a daily calorie target.")

        if todays:

            table = pd.DataFrame(todays)[["id", "meal", "food", "grams", "calories", "protein_g", "carbs_g", "fat_g", "source"]]
            st.dataframe(table, hide_index=True, width="stretch")

            labels = {e["id"]: f"{e['meal']}: {e['food']} ({round(e['calories'])} kcal)" for e in todays}
            remove_id = st.selectbox("Remove an entry", list(labels), format_func=lambda entry_id: labels[entry_id])

            if st.button("🗑️ Remove selected entry"):

                diary.delete_entry(remove_id)
                st.rerun()

        else:

            st.caption("Nothing logged today yet. Analyze a meal and press “Add to today's diary”.")

        st.markdown("**Last 7 days (calories)**")
        st.bar_chart(pd.DataFrame(diary.daily_totals(7)).set_index("day")["calories"])

        action_cols = st.columns(2)
        everything = diary.all_entries()

        if everything:

            action_cols[0].download_button("⬇️ Download diary (CSV)", pd.DataFrame(everything).to_csv(index=False).encode("utf-8"),
                                           "nutrilens_diary.csv", "text/csv")

        if action_cols[1].button("✈️ Send today's diary to Telegram", disabled=not todays):

            try:

                send_telegram_message(build_diary_summary(todays, day_totals, target))
                st.success("Today's diary was sent to Telegram!")

            except Exception as error:

                st.error(f"Telegram could not send the diary: {error}")

    with tab_coach:

        if not target:

            st.info("Save your profile first, so the advice can use your goal and daily target.")

        elif not target["adult"]:

            st.warning("Diet advice here is designed for adults. Please ask a doctor or dietitian instead.")

        else:

            extra_request = st.text_input("Anything specific? (optional)", placeholder="Example: ideas for a high-protein vegetarian dinner")

            if st.button("✨ Get my diet advice", type="primary"):

                try:

                    with st.spinner("NutriLens is preparing your advice..."):

                        st.session_state.diet_advice = get_diet_advice(
                            st.session_state.profile, target, diary.entries_for_day(), diary.daily_totals(7), extra_request)

                except Exception as error:

                    st.error(friendly_error(error))

            if st.session_state.diet_advice:

                st.markdown(st.session_state.diet_advice)

            st.caption("General wellness information based on estimates. Not medical advice. See a doctor or dietitian for health conditions.")

st.markdown('<div class="footer">Made with 🥗 and AI · NutriLens<br>Nutrition information is an estimate, not a medical diagnosis.</div>', unsafe_allow_html=True)
