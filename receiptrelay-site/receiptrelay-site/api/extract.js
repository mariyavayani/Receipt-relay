// Vercel serverless function: receives a receipt image, asks Gemini to read it, returns JSON.
const PROMPT =
  "Read this receipt and reply with JSON only, no other text, in this format: " +
  '{"vendor": "", "date": "YYYY-MM-DD", "total": 0.0, "tax": 0.0, "currency": "", "category": ""}. ' +
  "The total is the final amount charged, not the cash given or change returned. " +
  "Tax means only the tax line, not service charges or tips. " +
  "A two-digit year like 26 means 2026. " +
  "Write currency as a 3-letter code such as USD, PKR, EUR. If no symbol is shown, use the currency of the country where the business is located, judging by its address, phone code, or website. If the country is unclear, use null. " +
  "Category must be exactly one of: Groceries, Dining, Transport, Shopping, Electronics, Utilities, Health, Other. " +
  "If something is not visible on the receipt, use null for it. Never guess or invent values.";

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ error: "Use POST." });

  const key = process.env.GEMINI_API_KEY;
  if (!key) return res.status(500).json({ error: "The server has no GEMINI_API_KEY set." });

  const { image, mime } = req.body || {};
  if (!image || typeof image !== "string") return res.status(400).json({ error: "No image received." });
  if (image.length > 4000000) return res.status(413).json({ error: "Image is too large. Try a smaller photo." });

  const model = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;

  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": key },
      body: JSON.stringify({
        contents: [{ parts: [{ inline_data: { mime_type: mime || "image/jpeg", data: image } }, { text: PROMPT }] }],
        generationConfig: { responseMimeType: "application/json" },
      }),
    });
    const data = await r.json();
    if (!r.ok) {
      return res.status(r.status).json({ error: (data.error && data.error.message) || "Gemini request failed." });
    }
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text || "";
    const clean = text.replace(/```json|```/g, "").trim();
    return res.status(200).json(JSON.parse(clean));
  } catch (e) {
    return res.status(500).json({ error: "Could not read that receipt. Please try another photo." });
  }
};
