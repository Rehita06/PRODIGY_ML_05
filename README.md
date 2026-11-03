# NutriLens 🥗

**AI-powered food recognition and nutrition analysis.**

NutriLens is a Streamlit-based application that helps users turn a food photo into useful nutrition insights. It combines image-based food classification with Google Gemini to generate an estimated food description, ingredients, and nutritional information in an easy-to-use interface.

> **Note:** Nutrition values and image predictions are estimates. They are intended for general informational use and should not replace professional dietary or medical advice.

---

## ✨ Features

- **Food image analysis** — upload a meal image for AI-assisted food identification.
- **Food classification** — uses a pretrained Vision Transformer (ViT) model fine-tuned on the Food-101 dataset (`yfh/food`) to suggest likely food categories.
- **Gemini-powered nutrition insights** — uses the Google Gemini API to generate a structured food and nutrition report.
- **Nutrition estimates** — presents estimated calories, protein, carbohydrates, and fat.
- **Calorie consistency check** — compares the reported calorie estimate with the energy calculated from macronutrients using the 4/4/9 method.
- **Food diary and health features** — includes supporting modules for food diary and health-related app functionality.
- **Diet assistant/chat** — provides an interactive way to ask food and nutrition questions.
- **Light and dark themes** — switch the app appearance from the sidebar.
- **Optional Telegram integration** — supports sending information through a Telegram bot when credentials are configured.
- **Responsive Streamlit interface** — designed with a clean, modern layout.

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Interactive web application |
| Google Gemini API (`google-genai`) | Food and nutrition analysis |
| Hugging Face Transformers | Pretrained Vision Transformer model |
| PyTorch | Deep-learning model runtime |
| Pillow | Image handling |
| Pandas | Data handling |
| Requests | HTTP requests and optional integrations |

## 🧠 How It Works

1. Upload a food image in the NutriLens interface.
2. The food classifier analyzes the image and returns likely food-category predictions.
3. Gemini uses the available image and classification context to prepare a structured food and nutrition report.
4. NutriLens displays estimated calories and macronutrients.
5. A consistency check compares calories against the macronutrient estimate (protein × 4 + carbohydrates × 4 + fat × 9).

**Important model limitation:** Food-101 contains a fixed set of 101 food categories. It does not cover every regional dish or mixed meal. For foods outside its label set, the classifier may return an incorrect or low-confidence suggestion. Treat its output as a suggestion, not a verified identification.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Rehita06/PRODIGY_ML_05.git
cd PRODIGY_ML_05
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install streamlit google-genai requests pandas pillow transformers torch
```

If the repository contains a `requirements.txt` file, you can install the listed dependencies instead:

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

Create a folder named `.streamlit` in the project root, then create a file named `secrets.toml` inside it:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash"

# Optional: configure a remote food-classifier service
CLASSIFIER_URL = ""
CLASSIFIER_TOKEN = ""

# Optional: Telegram bot integration
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
```

- Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/).
- `GEMINI_MODEL` is optional; the application defaults to `gemini-2.5-flash`.
- `CLASSIFIER_URL` and `CLASSIFIER_TOKEN` are optional. Leave them empty if you are not using a remote classifier service.
- Telegram credentials are optional and only needed for the Telegram integration.

**Keep your credentials private.** Do not commit `.streamlit/secrets.toml`, `.env`, API keys, bot tokens, or other secrets to GitHub.

### 5. Run the application

From the project root, run:

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`). Open that address in your browser.

---

## 📁 Project Structure

The application uses a modular Python structure. A typical project layout is:

```text
PRODIGY_ML_05/
│
├── app.py                  # Main Streamlit application
├── food_classifier.py      # Food image classification logic
├── nutrition_data.py       # Nutrition data and estimation helpers
├── diary.py                # Food diary functionality
├── health.py               # Health-related app functionality
├── requirements.txt        # Python dependencies (if included)
├── .streamlit/
│   └── secrets.toml        # Local credentials (do not upload)
└── README.md
```

If your local repository uses different filenames or additional folders, keep the README structure in sync with the files actually committed.

## 🔐 Security

- Store API keys and tokens in Streamlit secrets.
- Keep `.streamlit/secrets.toml` out of version control.
- Never paste credentials into source code or public issues.
- If a credential is accidentally pushed, revoke or rotate it immediately.

A recommended `.gitignore` includes:

```gitignore
.venv/
__pycache__/
*.py[cod]
.streamlit/secrets.toml
.env
*.log
.cache/
```

## ⚠️ Limitations

- Food recognition depends on the classifier's supported categories and image quality.
- Food-101 is not a comprehensive dataset for Indian dishes, regional foods, or complex mixed meals.
- Nutrition values depend on the image, portion-size assumptions, and AI estimates; actual recipes and serving sizes can differ significantly.
- The application requires a valid Gemini API key for Gemini-powered analysis.
- The first local model run may need to download pretrained model files and can take time. PyTorch model inference may also require substantial memory and disk space.

## 🔮 Future Improvements

- Improve recognition of Indian and regional cuisines with a more representative dataset.
- Add portion-size estimation for more accurate nutrition calculations.
- Expand the nutrition database and support ingredient-level editing.
- Evaluate model performance across diverse dishes and lighting conditions.
- Add user profiles and personalized nutrition goals.
- Add automated tests and deployment workflows.

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome.

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes: `git commit -m "Add your feature"`.
4. Push the branch: `git push origin feature/your-feature`.
5. Open a Pull Request.

## 👩‍💻 Author

**Rehita06**

GitHub: [@Rehita06](https://github.com/Rehita06)

## 📄 License

No license is specified here. Unless a license is added to the repository, the code is not automatically granted an open-source license. Add a `LICENSE` file if you want to define how others may use, modify, and distribute this project.

---

<p align="center">
  Made with 💚 using Python, Streamlit, and AI
</p>
