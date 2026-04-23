Title
Health AI — AI-Powered Symptom Checker & Urgency Detector

Problem Statement

Every day, millions of people experience symptoms like fever, chest pain, or headaches and face one critical question:
"Is this serious enough to see a doctor, or will it go away on its own?"*

Description

Health AI is a full-stack web application that uses Google Gemini AI to analyze symptoms in natural language and return structured, actionable health guidance in seconds.

What It Does

Step      Action 
1:User types or speaks their symptoms
2:React frontend sends symptoms to Flask backend
3:Flask validates input and calls Gemini AI
4:Gemini reasons through symptoms and returns JSON 
5:App displays conditions, risk meter, advice, specialists 

Core Features
AI Symptom Analysis      — Gemini AI predicts 2-3 possible conditions
                               with probability scores (not hardcoded rules)
Urgency Risk Meter       — Animated color bar showing:
                               🟢 Low | 🟡 Medium | 🔴 High | 🚨 Emergency
Emergency Alert          — Pulsing red alert with direct 📞 call button
                               for heart attack, stroke, breathing emergency
Voice Input              — Speak symptoms instead of typing
                               (Browser Speech Recognition API)
Specialist Suggestions   — Recommends exact doctor type based on
                               predicted condition, with highlighted card
PDF Report Export        — Download formatted health report
                               for doctor visits or records
Mobile Responsive        — Works on phone, tablet, and desktop
Input Validation         — Front + backend validation with clear errors
Medical Disclaimer       — Always visible, professionally integrated


Architecture
╔══════════════════════════════════════════════════════════════╗
║                        USER LAYER                            ║
║                                                              ║
║              Browser (Desktop / Mobile / Tablet)             ║
╚══════════════════════════════╤══════════════════════════════╝
                               │
                               ▼
╔══════════════════════════════════════════════════════════════╗
║                      FRONTEND LAYER                          ║
║                    React + Vite (Vercel)                     ║
║                                                              ║
║   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     ║
║   │SymptomInput  │   │  ResultCard  │   │    RiskMeter │     ║
║   │  + Voice     │   │  + Prob Bar  │   │   + Animation│     ║
║   └──────────────┘   └──────────────┘   └──────────────┘     ║
║                                                              ║
║   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     ║
║   │  Disclaimer  │   │  Emergency   │   │  Specialist  │     ║
║   │   Banner     │   │    Alert     │   │    List      │     ║
║   └──────────────┘   └──────────────┘   └──────────────┘     ║
║                                                              ║
║                    App.jsx (Main Controller)                 ║
╚══════════════════════════════╤══════════════════════════════╝
                               │
                               │  HTTP POST /predict
                               │  HTTP GET  /specialists
                               │  (Axios)
                               ▼
╔══════════════════════════════════════════════════════════════╗
║                      BACKEND LAYER                           ║
║                   Flask + Python (Render)                     ║
║                                                               ║
║   ┌─────────────────────────────────────────────────────┐      ║
║   │                    app.py                           │     ║
║   │                                                     │     ║
║   │  POST /predict    → Validate → Call Gemini → JSON   │     ║
║   │  GET  /specialists → Return doctors list            │     ║
║   │  GET  /           → Health check                    │     ║
║   │                                                     │     ║
║   │  Middleware: Flask-CORS, python-dotenv              │     ║
║   └─────────────────────────────────────────────────────┘     ║
╚══════════════════════════════╤══════════════════════════════╝
                               │
                               │  HTTPS API Request
                               │  (google-generativeai SDK)
                               ▼
╔══════════════════════════════════════════════════════════════╗
║                        AI LAYER                              ║
║                 Google Gemini 1.5 Flash API                  ║
║                      (Free Tier)                             ║
║                                                              ║
║   Input  → Patient symptoms in natural language              ║
║                                                              ║
║   Output → Structured JSON:                                  ║
║            • conditions[] with name, probability,            ║
║              description, specialist                         ║
║            • urgency (Low/Medium/High/Emergency)             ║
║            • urgency_reason                                  ║ 
║            • general_advice                                  ║
║            • seek_emergency (true/false)                     ║
╚══════════════════════════════════════════════════════════════╝

Flow Diagram

                           ┌─────────┐
                           │  USER   │
                           └────┬────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Opens Health AI     │
                    │     Web Application     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Reads Disclaimer &    │
                    │   Understands Purpose   │
                    └────────────┬────────────┘
                                │
               ┌────────────────▼──────────────────┐
               │         Enters Symptoms           │
               │                                   │
               │   Option A: Type in textare       │                 
               │   Option B: 🎤 Voice input        │
               └─────────────────┬─────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Clicks "Analyze       │
                    │    Symptoms" Button     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Frontend Validates     │
                    │  • Not empty            │
                    │  • Min 3 characters     │
                    │  • Max 500 characters   │
                    └─────┬──────────┬────────┘
                         │             │
                     VALID│     INVALID│
                          │           │
                          │    ┌─────▼──────┐
                          │    │ Show Error │
                          │    │  Message   │
                          │    └────────────┘
                          │
           ┌────────────▼──────────  ────────┐
           │   Axios POST to Flask Backend   │
           │   { "symptoms": "user input" }  │
           └──────────────┬──────────────────┘
                          │
           ┌──────────────▼──────────────────┐
           │    Flask Backend Validates      │
           │    Input Again (Security)       │
           └──────────────┬──────────────────┘
                          │
           ┌──────────────▼──────────────────┐
           │    Builds Prompt + System       │
           │    Instructions for Gemini      │
           └──────────────┬──────────────────┘
                          │
           ┌──────────────▼──────────────────┐
           │    Sends to Gemini AI API       │
           │    model: gemini-1.5-flash      │
           └──────────────┬──────────────────┘
                          │
           ┌──────────────▼──────────────────┐
           │    Gemini Analyzes Symptoms     │
           │    Returns Structured JSON      │
           └──────────────┬──────────────────┘
                               │
           ┌──────────────▼──────────────────┐
           │    Flask Parses JSON            │
           │    Returns to Frontend          │
           └──────────────┬──────────────────┘
                          │
                ┌─────────▼──────────┐
                │  seek_emergency?   │
                └──── ┬──────────┬───┘
                     │           │
                  YES│         NO │
                    │             │
          ┌──────────▼──┐        ┌────▼────────────────┐
          │  🚨 SHOW    │       │  Show Normal Results │
          │  EMERGENCY  │       │                       │
          │  ALERT +    │       │  🎯 Risk Meter       │
          │  CALL 112   │       │  🔬 Conditions List  │
          └─────────────┘       │  💡 General Advice  │
                                │  👨‍⚕️ Find Specialist │
                                │  📄 Download PDF    │
                                └──────────┬──────────┘
                                          │
                                ┌──────────▼───────────┐
                                │  User Reads Results  │
                                └──────┬───────────----┘
                                          │
                      ┌──────────────▼──────────────────┐
                      │         User Decision           │
                      │                                 │
                      │  • Download PDF report          │
                      │  • View specialist list         │
                      │  • Call emergency services      │
                      │  • Check different symptoms     │
                      │  • Book doctor appointment      │
                      └─────────────────────────────────┘

Project Structure
health-ai/
├── backend/
│   ├── app.py              ← Flask server + Gemini integration
│   ├── requirements.txt    ← Python dependencies
│   └── .env                ← Gemini API key (never commit)
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Disclaimer.jsx       ← Medical disclaimer banner
    │   │   ├── EmergencyAlert.jsx   ← Red pulsing emergency alert
    │   │   ├── ResultCard.jsx       ← Condition card with prob bar
    │   │   ├── RiskMeter.jsx        ← Animated urgency meter
    │   │   ├── SpecialistList.jsx   ← Doctor recommendations grid
    │   │   └── SymptomInput.jsx     ← Textarea + voice + chips
    │   ├── App.jsx         ← Main app controller
    │   ├── App.css         ← Complete dark theme styles
    │   └── main.jsx        ← React entry point
    ├── .env                ← Backend URL config
    └── index.html          ← HTML shell
