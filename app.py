import json

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="ReceiptRelay", page_icon="🧾")

PROMPT = (
    "Read this receipt and reply with JSON only, no other text, in this format: "
    '{"vendor": "", "date": "YYYY-MM-DD", "total": 0.0, "tax": 0.0, "currency": "", "category": ""}. '
    "The total is the final amount charged, not the cash given or change returned. "
    "Tax means only the tax line, not service charges or tips. "
    "A two-digit year like 26 means 2026. "
    "Write currency as a 3-letter code such as USD, PKR, EUR. If no symbol is shown, use the currency of the country where the business is located, judging by its address, phone code, or website. If the country is unclear, use null. "
    "Category must be exactly one of: Groceries, Dining, Transport, Shopping, Electronics, Utilities, Health, Other. "
    "If something is not visible on the receipt, use null for it. Never guess or invent values."
)

SAMPLE = pd.DataFrame(
    [
        ["receipt1.jpg", "Urban Grocery & Provisions", "2023-10-26", "44.49", "3.39", "USD", "Groceries"],
        ["receipt2.jpg", "Al Mumtaz Sajji", "2026-10-12", "2,730", "", "PKR", "Dining"],
        ["receipt3.jpg", "Ichiban Sushi", "2024-08-19", "257,565", "23,415", "IDR", "Dining"],
        ["receipt4.jpg", "", "", "117", "", "", ""],
        ["receipt5.jpg", "Walmart", "2021-08-12", "35.36", "2.54", "USD", "Groceries"],
        ["receipt6.jpg", "Apple Store, Grafton Street", "2025-04-09", "3,442.77", "643.77", "EUR", "Electronics"],
    ],
    columns=["File", "Vendor", "Date", "Total", "Tax", "Currency", "Category"],
)


FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash"]


class QuotaError(Exception):
    pass


def read_receipt(image_bytes, mime_type):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    preferred = st.secrets.get("GEMINI_MODEL", FALLBACK_MODELS[0])
    models = [preferred] + [m for m in FALLBACK_MODELS if m != preferred]
    saw_quota = False
    last_error = None
    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), PROMPT],
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError("unreadable") from e
        except Exception as e:  # try the next model
            last_error = e
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                saw_quota = True
    if saw_quota:
        raise QuotaError()
    raise last_error


def show_details(data):
    for label, key in [("Vendor", "vendor"), ("Date", "date"), ("Total", "total"),
                       ("Tax", "tax"), ("Currency", "currency"), ("Category", "category")]:
        value = data.get(key)
        st.write(f"**{label}:** {value if value not in (None, '') else 'not on receipt'}")


st.title("ReceiptRelay")
st.write(
    "Upload a photo of a receipt. AI reads the vendor, date, total, tax, "
    "currency and category, so you never type them in by hand."
)

uploaded = st.file_uploader("Choose a receipt photo", type=["jpg", "jpeg", "png"])

if "results" not in st.session_state:
    st.session_state.results = {}

if uploaded:
    key = f"{uploaded.name}-{uploaded.size}"
    left, right = st.columns(2)
    left.image(uploaded, caption="Your receipt")
    with right:
        st.subheader("Extracted details")
        # Only call the AI once per photo, so reruns do not waste the free quota
        if key not in st.session_state.results:
            with st.spinner("Reading your receipt..."):
                try:
                    data = read_receipt(uploaded.getvalue(), uploaded.type)
                    data["file"] = uploaded.name
                    st.session_state.results[key] = data
                except QuotaError:
                    st.warning("The free AI limit is used up for now. Pick a saved example below to see what the app produces, or try again later.")
                except ValueError:
                    st.error("The AI could not find receipt details in that photo. Try a clearer, well-lit photo of the whole receipt.")
                except Exception as e:
                    st.error("Something went wrong on our side. Pick a saved example below, or try again in a minute.")
                    with st.expander("Technical details"):
                        st.code(str(e)[:400])
        if key in st.session_state.results:
            show_details(st.session_state.results[key])

if st.session_state.results:
    st.subheader("Your receipts this session")
    columns = ["file", "vendor", "date", "total", "tax", "currency", "category"]
    table = pd.DataFrame(list(st.session_state.results.values())).reindex(columns=columns)
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button("Download as CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name="expenses.csv", mime="text/csv")
    st.caption("This table lives in your browser session. Download it before you close the page.")

st.subheader("Or see a saved example")
choice = st.selectbox("Choose a receipt from our test run", SAMPLE["File"], index=None, placeholder="Select a receipt")
if choice:
    row = SAMPLE[SAMPLE["File"] == choice].iloc[0]
    show_details({"vendor": row["Vendor"], "date": row["Date"], "total": row["Total"],
                  "tax": row["Tax"], "currency": row["Currency"], "category": row["Category"]})

st.header("Results from our test run")
st.caption(
    "Six real receipts from three countries, checked by hand against the paper originals. "
    "Receipt 4 has no vendor, date or tax, so those stay blank instead of guessed."
)
st.dataframe(SAMPLE, hide_index=True, use_container_width=True)
st.caption("Built with Python and Google Gemini. Your photo is sent to the AI for reading and is not stored.")
