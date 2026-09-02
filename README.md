# PhishGuard 🛡️

PhishGuard is a phishing website detector I built that combines a trained machine learning model with a Chrome extension, so it can warn you in real time as you browse instead of just being a notebook that sits on my laptop.

The idea is simple: you visit a page, the extension quietly sends the URL to a small local API, the API runs it through a model trained on thousands of real phishing and legitimate sites, and if something looks off, you get a warning banner right there on the page.

## How it's put together

There are three moving parts:

- **The Chrome extension** — the part you actually see. It watches the page you're on, asks the API "is this safe?", and shows a warning banner or updates the popup depending on the answer.
- **The Flask API** — sits in the middle. Takes a URL, breaks it down into 30 numerical clues (does it use HTTPS? is it a shortened link? does it use an IP address instead of a domain? etc.), and passes those to the model.
- **The model itself** — a Random Forest classifier I trained on the UCI Phishing Websites dataset (about 11,000 labeled URLs). I actually trained five different models and compared them before settling on Random Forest, which came out on top at around 97% accuracy.

```
Chrome Extension  →  Flask API  →  ML Model
(what you see)        (app.py)     (phishing_model.pkl)
```

## What's in each folder

```
Phishing Project/
├── phishing.csv                  # The dataset I trained on
├── phishing_detection.ipynb      # Where I trained and compared the models
├── phishing_model.pkl            # The final trained model
├── scaler.pkl                    # Scaling rules the model needs before predicting
├── feature_names.json            # Keeps track of which 30 features, in what order
│
├── phishing_api/                 # The backend
│   ├── app.py                    # The actual Flask API
│   ├── requirements.txt          # Python packages this needs
│   └── (copies of the model files above)
│
└── phishing_extension/           # The Chrome extension
    ├── manifest.json
    ├── background.js             # Runs quietly, badges the toolbar icon
    ├── content.js                # Puts the warning banner on the page itself
    ├── popup.html / popup.js     # What you see when you click the icon
    └── icons/
```

## The models I tried

I didn't just pick the first model that worked — I trained and compared five:

- Logistic Regression
- **Random Forest — this is the one that made the cut, ~97.3% accuracy**
- XGBoost
- Gradient Boosting
- A small Neural Network (MLP)

Random Forest gave the best balance of accuracy and reliability, so that's what's shipped in the API.

## Getting it running

### The API

```bash
cd phishing_api
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
python app.py
```

Once it's running, check `http://localhost:5000/health` — it should tell you the model loaded fine.

### The extension

1. Open `chrome://extensions` in Chrome.
2. Flip on **Developer mode** (top right corner).
3. Click **Load unpacked**, and point it at the `phishing_extension` folder.
4. That's it — you'll see the PhishGuard icon in your toolbar. Just make sure the API is still running in the background, since the extension can't do anything without it.

## The API, if you want to use it directly

**`GET /health`** — quick check that the API and model are alive.

**`POST /predict`** — send it a URL, get back a verdict:
```json
{ "url": "http://example.com" }
```
```json
{
  "url": "http://example.com",
  "label": "Legitimate",
  "confidence": 91.2,
  "is_phishing": false,
  "method": "ml-model",
  "flags": []
}
```

**`POST /predict/batch`** — same idea, but send a list of up to 100 URLs at once.

## Something I want to be upfront about

A handful of the 30 features the model was trained on — things like how many links on a page point elsewhere, how old the domain is, its search-engine ranking — aren't really things you can figure out just by looking at a URL string. They normally need to scrape the actual page or call outside services like WHOIS. Since the API only looks at the URL itself in real time, those particular features get passed in as neutral placeholders rather than real values.

In practice, this means the model still gets the right answer most of the time, but its confidence on some perfectly safe sites can come out lower than you'd expect. It's on my list to fix by having the extension pull real page data (like the actual links on the page) and send that along too — that would let the model use its strongest features properly instead of guessing at them.

## Built with

Python, scikit-learn, pandas, and Flask on the backend. Plain JavaScript and a Chrome Manifest V3 extension on the frontend.

## About this project

This started as my final-year university project. Feel free to poke around, use it to learn from, or build on top of it.
