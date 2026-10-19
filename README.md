# ReceiptRelay

**An AI-powered web app that turns a photo of any receipt into organized expense data in seconds.**

**Live app:** https://receipt-relay-mv.streamlit.app
**Code:** https://github.com/mariyavayani/Receipt-relay

---

## Problem

Freelancers and small business owners collect dozens of paper and emailed receipts every month, and most enter the details into a spreadsheet by hand. This is slow, easy to get wrong, and tedious enough that people put it off until tax time, when receipts are lost, faded, or forgotten. Existing expense tools often cost money, need accounts, or struggle with messy photos and receipts from different countries and currencies. As a result, small earners lose hours of their time, miss deductible expenses, and have no clear picture of where their money goes.

## Solution

ReceiptRelay lets anyone upload a receipt photo and get the vendor, date, total, tax, currency, and category back in seconds. The results appear on screen and collect into a table that can be downloaded as a CSV spreadsheet and opened in Excel or Google Sheets.

**Features**
- Upload a JPG or PNG receipt photo and see the extracted details immediately
- Works with receipts from different countries and currencies
- Leaves fields blank instead of guessing when information is missing from the receipt
- Session table of all receipts uploaded, with a **Download as CSV** button
- Saved examples from our test run, so the app is never a dead end if the free AI quota runs out
- Automatic fallback to backup AI models, and clear messages when something goes wrong

## Technology stack

| Purpose | Tool |
|---|---|
| Language | Python 3.11 |
| Web interface | Streamlit |
| AI model | Google Gemini (vision-language model) |
| AI SDK | `google-genai` |
| Data table and CSV export | pandas |
| Hosting | Streamlit Community Cloud |
| Source control | GitHub |

## Setup steps

**Requirements:** Python 3.10 or newer and a free Gemini API key from [Google AI Studio](https://aistudio.google.com).

1. Clone the repository:
   ```
   git clone https://github.com/mariyavayani/Receipt-relay.git
   cd Receipt-relay
   ```
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a file at `.streamlit/secrets.toml` and add your key:
   ```
   GEMINI_API_KEY = "your-key-here"
   GEMINI_MODEL = "gemini-3.8-flash"
   ```
   `GEMINI_MODEL` is optional. Never commit this file or share your key.
4. Run the app:
   ```
   streamlit run app.py
   ```
5. Open the local address shown in the terminal, usually http://localhost:8501.

**Deploying:** push the code to GitHub, create an app on [Streamlit Community Cloud](https://share.streamlit.io) pointing at `app.py`, and paste the same two lines into the app's **Secrets** settings.

**Optional batch script:** `make_csv.py` reads every image in a local `receipts/` folder and writes `expenses.csv`.

## AI methodology

ReceiptRelay uses Google's Gemini, a pretrained vision-language model, through prompting. We did not train or fine-tune any model. The user uploads a receipt photo, the app sends it to Gemini with an instruction asking for JSON only (vendor, date, total, tax, currency, category), and the app parses the reply, shows it on screen, and adds it to a table. Because the model reads the image directly, no separate OCR step is needed.

**Implementation**
- `app.py`: the Streamlit app. It uploads the photo, calls Gemini, parses the JSON reply, and builds the results table and CSV download.
- `requirements.txt`: the Python libraries to install (`streamlit`, `google-genai`).
- `make_csv.py`: an optional script that processes a whole folder of receipts into `expenses.csv`.
- The API key is read from Streamlit Secrets and never stored in the code.

**Pipeline:** upload photo, send image and instruction to Gemini, receive JSON, clean and parse it, display and export.

**Prompt design.** The prompt is the core of the method, and every rule in it came from a failure we found in testing:
- Return `null` for anything not visible and never guess. A receipt with no vendor or date made the model invent values.
- The total is the final amount charged, not the cash given or change.
- Tax means only the tax line, not service charges or tips.
- A two-digit year like 26 means 2026. The model once misread "12 Oct 26" as 2023.
- Categories come from a fixed list (Groceries, Dining, Transport, Shopping, Electronics, Utilities, Health, Other), and currency is a 3-letter code, inferred from the business's location when no symbol is printed.

**Evaluation.** We tested on six real receipts from three countries (USD, PKR, IDR, EUR), including a hand-held photo, a crumpled receipt, and one with missing information. We compared each output with the paper original and refined the prompt after each round of errors. This is a small test: it shows the approach works on varied inputs, but it is not a statistical measure of accuracy.

**Reliability.** The app tries backup Gemini models if one is unavailable or out of quota, calls the model only once per photo, and shows clear messages instead of raw errors.

## Models and APIs used

- **Model:** Google Gemini. The primary model is set by the `GEMINI_MODEL` setting (`gemini-3.8-flash`), with `gemini-2.5-flash-lite` and `gemini-2.5-flash` as backups. Models are used as provided, with no fine-tuning.
- **API:** Google Gemini API (Google AI Studio), called through the official `google-genai` Python SDK. Each upload is one `generate_content` request containing the image and a text instruction, authenticated with an API key stored as a secret.

## Screenshots

https://drive.google.com/drive/folders/1FcDVCyS1TI7chtUyig37GQmUlKQlxcYN?usp=sharing


| Live app reading a receipt | Results table and CSV download |
|---|---|
| ![App reading a receipt](screenshots/app-result.png) | ![Spreadsheet output](screenshots/spreadsheet.png) |


## Limitations

- The model can misread blurry, cut-off, or handwritten receipts, so important entries should be checked before use for accounting or tax.
- Uploaded photos are sent to Google's Gemini API for processing. The app does not store them, but receipts can contain personal details.
- The results table lives in the visitor's browser session and is lost when the page is closed, so users should download the CSV first.
- The app runs on a free tier with daily limits, so heavy use may hit the quota.

## Future improvements

- Duplicate receipt detection
- Monthly spending summary by category
- Google Sheets export
- Receipt intake by email forwarding
- Per-field confidence scores, with low-confidence entries flagged for review

## Team

| Name | Role | Contributions |
|---|---|---|
| Mariya Vayani | Solo developer | Project idea and scope, prompt design and testing on real receipts, Python and Streamlit app, deployment on Streamlit Community Cloud, documentation |

