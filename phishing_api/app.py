"""
Phishing Detection Flask API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import re
import urllib.parse
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ── Load model, scaler and feature names ──
model         = None
scaler        = None
feature_names = None

if os.path.exists("phishing_model.pkl"):
    model = joblib.load("phishing_model.pkl")
    print("✅ Model loaded!")

if os.path.exists("scaler.pkl"):
    scaler = joblib.load("scaler.pkl")
    print("✅ Scaler loaded!")

if os.path.exists("feature_names.json"):
    with open("feature_names.json") as f:
        feature_names = json.load(f)
    print("✅ Feature names loaded:", feature_names)


def extract_url_features(url: str) -> dict:
    """Extract features from URL using EXACT column names from training data."""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or parsed.path
        path   = parsed.path
    except Exception:
        domain, path = url, ""

    ip_pattern = re.compile(r'(\d{1,3}\.){3}\d{1,3}')
    using_ip   = -1 if ip_pattern.search(domain) else 1

    url_len = len(url)
    if url_len < 54:   long_url = 1
    elif url_len < 75: long_url = 0
    else:              long_url = -1

    shorteners = ['bit.ly','tinyurl','goo.gl','t.co','ow.ly']
    short_url  = -1 if any(s in url.lower() for s in shorteners) else 1

    symbol_at     = -1 if '@' in url else 1
    redirecting   = -1 if '//' in url[7:] else 1
    prefix_suffix = -1 if '-' in domain else 1

    dots = domain.count('.')
    if dots <= 1:   sub_domains = 1
    elif dots == 2: sub_domains = 0
    else:           sub_domains = -1

    https           = 1 if url.startswith('https') else -1
    domain_reg_len  = 1
    favicon         = 1
    non_std_port    = -1 if ':' in domain.split('/')[-1] else 1
    https_domain    = -1 if 'https' in domain.lower() else 1
    request_url     = 1 if path.count('/') < 4 else -1
    anchor_url      = 0
    links_in_script = 0
    server_form     = 0
    info_email      = -1 if 'mailto:' in url.lower() else 1
    abnormal_url    = -1 if domain not in url else 1
    website_fwd     = 1
    status_bar      = 1
    disable_right   = 1
    popup           = 1
    iframe          = 1
    age_of_domain   = 0
    dns_recording   = 0
    website_traffic = 0
    page_rank       = 0
    google_index    = 0
    links_pointing  = 0
    stats_report    = 0

    # All possible feature mappings
    all_features = {
        'UsingIP':             using_ip,
        'LongURL':             long_url,
        'ShortURL':            short_url,
        'Symbol@':             symbol_at,
        'Redirecting//':       redirecting,
        'PrefixSuffix-':       prefix_suffix,
        'SubDomains':          sub_domains,
        'HTTPS':               https,
        'DomainRegLen':        domain_reg_len,
        'Favicon':             favicon,
        'NonStdPort':          non_std_port,
        'HTTPSDomainURL':      https_domain,
        'RequestURL':          request_url,
        'AnchorURL':           anchor_url,
        'LinksInScriptTags':   links_in_script,
        'ServerFormHandler':   server_form,
        'InfoEmail':           info_email,
        'AbnormalURL':         abnormal_url,
        'WebsiteForwarding':   website_fwd,
        'StatusBarCust':       status_bar,
        'DisableRightClick':   disable_right,
        'UsingPopupWindow':    popup,
        'IframeRedirection':   iframe,
        'AgeofDomain':         age_of_domain,
        'DNSRecording':        dns_recording,
        'WebsiteTraffic':      website_traffic,
        'PageRank':            page_rank,
        'GoogleIndex':         google_index,
        'LinksPointingToPage': links_pointing,
        'StatsReport':         stats_report,
    }

    # Return ONLY the features the model was trained on, in correct order
    if feature_names:
        return {k: all_features.get(k, 0) for k in feature_names}
    return all_features


def rule_based_score(url: str) -> dict:
    suspicion = 0
    flags     = []

    if re.search(r'(\d{1,3}\.){3}\d{1,3}', url):
        suspicion += 25
        flags.append("IP address used instead of domain")
    if any(s in url for s in ['bit.ly','tinyurl','goo.gl','t.co']):
        suspicion += 20
        flags.append("URL shortener detected")
    if '@' in url:
        suspicion += 15
        flags.append("@ symbol in URL")
    if not url.startswith('https'):
        suspicion += 15
        flags.append("No HTTPS")
    if len(url) > 75:
        suspicion += 10
        flags.append("Unusually long URL")
    if '-' in urllib.parse.urlparse(url).netloc:
        suspicion += 10
        flags.append("Hyphen in domain name")
    if url.count('.') > 3:
        suspicion += 10
        flags.append("Excessive subdomains")

    suspicion   = min(suspicion, 100)
    is_phishing = suspicion >= 40

    return {
        "label":      "Phishing" if is_phishing else "Legitimate",
        "confidence": suspicion if is_phishing else 100 - suspicion,
        "method":     "rule-based",
        "flags":      flags,
    }


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name":    "Phishing Detection API",
        "version": "1.0",
        "status":  "running"
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status":       "ok",
        "model_loaded": model is not None,
        "timestamp":    datetime.utcnow().isoformat()
    })


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    url = data.get('url')

    if url:
        features_dict = extract_url_features(url)
    elif 'features' in data:
        features_dict = data['features']
    else:
        return jsonify({"error": "Provide url or features"}), 400

    if model is not None:
        try:
            df_input = pd.DataFrame([features_dict])
            if scaler is not None:
                df_input = pd.DataFrame(
                    scaler.transform(df_input),
                    columns=df_input.columns
                )
            pred   = model.predict(df_input)[0]
            prob   = model.predict_proba(df_input)[0]
            label  = "Legitimate" if pred == 1 else "Phishing"
            conf   = round(float(max(prob)) * 100, 2)
            method = "ml-model"
            flags  = []
        except Exception as e:
            print("ML error:", str(e))
            result = rule_based_score(url or "")
            label  = result['label']
            conf   = result['confidence']
            method = "rule-based (fallback)"
            flags  = result['flags']
    else:
        result = rule_based_score(url or "")
        label  = result['label']
        conf   = result['confidence']
        method = result['method']
        flags  = result['flags']

    return jsonify({
        "url":         url,
        "label":       label,
        "confidence":  conf,
        "is_phishing": label == "Phishing",
        "method":      method,
        "flags":       flags,
    })


@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    data = request.get_json(force=True)
    urls = data.get('urls', [])
    if not urls:
        return jsonify({"error": "urls list required"}), 400

    results = []
    for url in urls[:100]:
        features_dict = extract_url_features(url)
        if model is not None:
            try:
                df_input = pd.DataFrame([features_dict])
                if scaler is not None:
                    df_input = pd.DataFrame(
                        scaler.transform(df_input),
                        columns=df_input.columns
                    )
                pred  = model.predict(df_input)[0]
                prob  = model.predict_proba(df_input)[0]
                label = "Legitimate" if pred == 1 else "Phishing"
                conf  = round(float(max(prob)) * 100, 2)
            except Exception:
                r     = rule_based_score(url)
                label = r['label']
                conf  = r['confidence']
        else:
            r     = rule_based_score(url)
            label = r['label']
            conf  = r['confidence']

        results.append({
            "url":         url,
            "label":       label,
            "confidence":  conf,
            "is_phishing": label == "Phishing",
        })

    return jsonify({
        "total":   len(results),
        "results": results,
    })


if __name__ == '__main__':
    print("🔒 Phishing Detection API starting...")
    print("📡 Running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
