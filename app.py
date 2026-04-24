import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# ======================
# Load Environment
# ======================
load_dotenv()

app = Flask(__name__)
CORS(app)

# ======================
# Gemini Config
# ======================
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("⚠️ GEMINI_API_KEY not found in .env")
else:
    print("✅ Gemini API Key Loaded")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

# ======================
# Severity Weights
# ======================
SEVERITY_WEIGHTS = {
    "mild": 1,
    "moderate": 2,
    "severe": 3
}

# ======================
# Optimized Prompt
# ======================
SYSTEM_PROMPT = """
Return ONLY valid JSON.

{
 "conditions":[
   {
    "name":"",
    "probability":0,
    "description":"",
    "specialist":""
   }
 ],
 "urgency":"",
 "urgency_reason":"",
 "general_advice":"",
 "seek_emergency":false
}

Rules:
- Give top 2 likely conditions
- urgency = Low / Medium / High / Emergency
- No markdown
- VERY IMPORTANT: Pay close attention to the severity of each symptom (MILD, MODERATE, SEVERE).
- A "SEVERE" symptom (weight=3) MUST drastically increase the urgency to High or Emergency and raise the condition's probability.
- A "MILD" symptom (weight=1) should keep the urgency Low or Medium and result in a lower probability score.
- The difference between predicting MILD vs SEVERE for the same symptom MUST result in distinctly different urgency levels and probability scores.
"""

# ======================
# Confidence Threshold
# ======================
CONFIDENCE_THRESHOLD = 0.70


def apply_confidence_threshold(result):
    """
    Extracts max confidence from conditions, normalizes it,
    and flags the result as inconclusive if below threshold.
    Always attaches confidence_percent to the result.
    """
    conditions = result.get("conditions", [])

    if conditions:
        max_confidence = max(c.get("probability", 0) for c in conditions)
        confidence_score = round(max_confidence / 100, 2)  # normalize to 0.0–1.0
    else:
        confidence_score = 0.0

    result["confidence"] = confidence_score
    result["confidence_percent"] = f"{round(confidence_score * 100)}%"

    if confidence_score < CONFIDENCE_THRESHOLD:
        result["is_inconclusive"] = True
        result["inconclusive_message"] = (
            "Inconclusive result — confidence too low. Please consult a doctor."
        )
    else:
        result["is_inconclusive"] = False

    return result


def build_weighted_symptom_input(symptoms_with_severity: list) -> tuple[str, list]:
    """
    Step 2 & 3: Assign weights and build weighted symptom input string.

    Accepts a list of dicts: [{"symptom": "fever", "severity": "moderate"}, ...]
    Returns:
      - weighted_prompt_str: descriptive string for the AI model
      - symptom_summary: list of dicts with symptom, severity, weight for response display
    """
    symptom_summary = []
    weighted_parts = []

    for item in symptoms_with_severity:
        symptom = item.get("symptom", "").strip()
        severity = item.get("severity", "mild").lower()

        if not symptom:
            continue

        # Clamp severity to known keys
        if severity not in SEVERITY_WEIGHTS:
            severity = "mild"

        weight = SEVERITY_WEIGHTS[severity]  # Step 2: assign weight

        # Step 3: Build weighted description for the model
        # Weight multiplier is conveyed via descriptive language
        if weight == 3:
            intensity_label = "SEVERE"
        elif weight == 2:
            intensity_label = "MODERATE"
        else:
            intensity_label = "MILD"

        # Repeat symptom proportional to weight to influence model attention (Step 4)
        repeated_symptom = " ".join([symptom] * weight)
        weighted_parts.append(f"{repeated_symptom} [{intensity_label}, weight={weight}]")

        symptom_summary.append({
            "symptom": symptom,
            "severity": severity,
            "weight": weight
        })

    weighted_prompt_str = ", ".join(weighted_parts)
    return weighted_prompt_str, symptom_summary


# ======================
# Routes
# ======================

@app.route("/")
def home():
    return jsonify({
        "status": "Health AI Running Successfully"
    })


@app.route("/predict", methods=["POST"])
def predict():
    """
    Accepts either:
      1. Legacy format: { "symptoms": "fever, headache" }
      2. New severity format: { "symptoms": [{"symptom": "fever", "severity": "severe"}, ...] }
    """
    symptoms = ""  # ensure defined for fallback error handling

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No input received"}), 400

        raw_symptoms = data.get("symptoms")

        if raw_symptoms is None or raw_symptoms == "" or raw_symptoms == []:
            return jsonify({"error": "Please enter symptoms"}), 400

        # ── Step 1 & 4: Handle severity-aware input ──────────────────────────
        if isinstance(raw_symptoms, list):
            # New format: list of {symptom, severity} dicts
            weighted_input, symptom_summary = build_weighted_symptom_input(raw_symptoms)

            if not weighted_input:
                return jsonify({"error": "No valid symptoms provided"}), 400

            symptoms = weighted_input  # used in fallback scope
            prompt = (
                f"{SYSTEM_PROMPT}\n"
                f"Symptoms with severity weights (higher weight = more serious):\n"
                f"{weighted_input}"
            )

        else:
            # Legacy format: plain string
            symptoms = raw_symptoms.strip()

            if len(symptoms) < 3:
                return jsonify({"error": "Enter more details"}), 400

            # Treat all as moderate by default when no severity given
            legacy_items = [
                {"symptom": s.strip(), "severity": "moderate"}
                for s in symptoms.split(",") if s.strip()
            ]
            _, symptom_summary = build_weighted_symptom_input(legacy_items)

            prompt = f"{SYSTEM_PROMPT}\nSymptoms: {symptoms}"

        # ── Call Gemini ───────────────────────────────────────────────────────
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Remove markdown fences if present
        text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        result["symptoms_received"] = symptoms

        # Step 5: Attach severity summary to response for display on results screen
        result["symptom_severity_breakdown"] = symptom_summary

        # Apply confidence threshold check
        result = apply_confidence_threshold(result)

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({
            "error": "AI returned invalid JSON"
        }), 500

    except Exception as e:
        error_text = str(e)

        # Quota exceeded fallback
        if "429" in error_text or "quota" in error_text.lower():

            symptoms_lower = symptoms.lower()

            # Emergency detection
            if "chest pain" in symptoms_lower or "left arm" in symptoms_lower:
                result = {
                    "conditions": [
                        {
                            "name": "Possible Heart Emergency",
                            "probability": 92,
                            "description": "Symptoms may indicate serious heart issue.",
                            "specialist": "Cardiologist"
                        }
                    ],
                    "urgency": "Emergency",
                    "urgency_reason": "Chest pain can be serious.",
                    "general_advice": "Call emergency services immediately.",
                    "seek_emergency": True,
                    "fallback_mode": True
                }

            # Fever fallback
            elif "fever" in symptoms_lower:
                result = {
                    "conditions": [
                        {
                            "name": "Viral Fever",
                            "probability": 78,
                            "description": "Common infection causing fever.",
                            "specialist": "General Physician"
                        },
                        {
                            "name": "Flu",
                            "probability": 65,
                            "description": "Body pain and fever may indicate flu.",
                            "specialist": "General Physician"
                        }
                    ],
                    "urgency": "Low",
                    "urgency_reason": "Usually manageable but monitor symptoms.",
                    "general_advice": "Rest, hydrate, consult doctor if worse.",
                    "seek_emergency": False,
                    "fallback_mode": True
                }

            # Default fallback
            else:
                result = {
                    "conditions": [
                        {
                            "name": "General Illness",
                            "probability": 70,
                            "description": "Needs medical evaluation.",
                            "specialist": "General Physician"
                        }
                    ],
                    "urgency": "Medium",
                    "urgency_reason": "Symptoms unclear.",
                    "general_advice": "Consult a doctor.",
                    "seek_emergency": False,
                    "fallback_mode": True
                }

            result["symptom_severity_breakdown"] = []  # empty in fallback
            result = apply_confidence_threshold(result)
            return jsonify(result)

        return jsonify({
            "error": error_text
        }), 500


@app.route("/specialists")
def specialists():
    return jsonify({
        "specialists": [
            {"type": "General Physician", "icon": "🩺", "treats": "Fever, cold, flu"},
            {"type": "Cardiologist", "icon": "❤️", "treats": "Chest pain, heart issues"},
            {"type": "Neurologist", "icon": "🧠", "treats": "Headache, numbness"},
            {"type": "Dermatologist", "icon": "🧴", "treats": "Skin allergy, acne"},
            {"type": "Pulmonologist", "icon": "🫁", "treats": "Breathing issues"},
            {"type": "Gastroenterologist", "icon": "🍽️", "treats": "Stomach pain"},
            {"type": "ENT Specialist", "icon": "👂", "treats": "Ear, throat, sinus"},
            {"type": "Orthopedist", "icon": "🦴", "treats": "Joint pain"}
        ]
    })


# ======================
# Run App
# ======================
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
