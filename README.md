# AI Chat Vision Bot --- NutriLens

NutriLens is an AI-powered food vision and nutrition chatbot built with
**Python**, **Streamlit**, and the **Google Gemini API**. Upload a meal
photo to receive an AI-generated food description and estimated
nutrition information, send the report to Telegram, and ask follow-up
questions about the meal.

> **Note:** Nutrition values generated from an image are estimates, not
> exact measurements or medical advice.

## Features

-   Upload JPG, JPEG, PNG, or WEBP meal photos.
-   Estimate calories, protein, carbohydrates, and fat.
-   Display the identified food, estimated portion, visible ingredients,
    summary, and suggestion.
-   Ask follow-up questions about the analyzed meal.
-   Send a nutrition report to Telegram.
-   Use the app through a Streamlit web interface.

## Tech Stack

-   Python
-   Streamlit
-   Google Gen AI SDK (`google-genai`)
-   Gemini API
-   Requests
-   Telegram Bot API

## Project Structure

``` text
NutriLens/
├── app.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml
```

## Requirements

-   Python
-   A Google Gemini API key
-   A Telegram bot token and chat ID for Telegram sharing

## Installation and Setup

### 1. Install dependencies

Create `requirements.txt` with:

``` text
streamlit
google-genai
requests
```

Install the packages:

``` bash
python -m pip install -r requirements.txt
```

### 2. Configure credentials

Create `.streamlit/secrets.toml`:

``` toml
GEMINI_API_KEY = "your_gemini_api_key"
GEMINI_MODEL = "gemini-2.5-flash"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"
```

Replace the placeholder values with your own credentials. Use a Gemini
model available to your account.

**Security:** Never commit `.streamlit/secrets.toml` to a public
repository. Add the following to `.gitignore`:

``` gitignore
.streamlit/secrets.toml
.venv/
__pycache__/
*.pyc
```

### 3. Run the application

From the project directory, run:

``` bash
python -m streamlit run app.py
```

Open the local URL shown in the terminal.

## How to Use

1.  Open NutriLens in your browser.
2.  Upload a clear photo of a meal.
3.  Optionally provide food or portion details.
4.  Select **Analyze My Meal**.
5.  Review the estimated nutrition report.
6.  Select **Send Summary to Telegram** to share it.
7.  Ask follow-up questions in the chat section.

## How It Works

1.  Streamlit accepts the uploaded image.
2.  Gemini analyzes the image and estimates the meal's nutrition.
3.  The app validates the returned nutrition fields.
4.  Streamlit displays the food details and nutrition report.
5.  The Telegram Bot API sends the report when requested.
6.  Gemini answers follow-up questions using the meal analysis as
    context.

## Troubleshooting

### Gemini API quota reached

Check usage and rate limits in [Google AI
Studio](https://aistudio.google.com/) and the [Gemini API rate-limit
documentation](https://ai.google.dev/gemini-api/docs/rate-limits). Avoid
repeatedly submitting requests while the quota is exhausted.

### Gemini model unavailable

Check that `GEMINI_MODEL` in `.streamlit/secrets.toml` names a model
available to your API key.

### Missing credentials

Check the spelling and values in `.streamlit/secrets.toml`. Never share
API keys or bot tokens in public posts or issue reports.

### Telegram report failed

Verify the bot token and chat ID. Start a conversation with your bot and
ensure it can send messages to the selected chat.

### Incomplete nutrition response

Try a clear image with the full meal visible. Add portion details when
known. Hidden ingredients and uncertain serving sizes can affect
estimates.

## Limitations

-   Nutrition values are estimates based on the visible image.
-   Exact ingredients, cooking methods, and portion weights may not be
    identifiable from a photo.
-   Gemini requests depend on API availability, rate limits, and account
    quota.
-   Telegram sharing requires valid credentials.
-   This project provides general information, not medical or
    professional dietary advice.

## Future Improvements

-   Add manual portion-size adjustment.
-   Save and compare meal reports.
-   Add daily nutrition summaries.
-   Improve handling of uncertain food identification.
-   Add deployment instructions for a hosted version.

## Author

**Project:** AI Chat Vision Bot --- NutriLens\
**Built with:** Python, Streamlit, Gemini API, and Telegram Bot API
