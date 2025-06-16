# 🏥 Ghana AI Doctor Agent

Welcome to the **Ghana AI Doctor Agent** – a professional-grade AI medical consultation system tailored for Ghana! This project combines the latest AI technology with local medical expertise to provide accessible, culturally relevant, and secure medical guidance to users across Ghana.

---

## 👨‍⚕️ Meet Dr. Kwame Asante

- **Name:** Dr. Kwame Asante  
- **Position:** Senior Physician  
- **Hospital:** Korle Bu Teaching Hospital, Accra  
- **Experience:** 15 years in tropical medicine & general practice  
- **Specialization:** Ghana-specific medical conditions

---

## 🏗️ Technical Architecture

### Backend (FastAPI + Python)
- **AI Integration:** Google Gemini 2.0 Flash (latest model)
- **Database:** MongoDB for consultation history
- **API Endpoints:** `/api/consult`, `/api/consultations/{session_id}`, `/api/health`
- **Session Management:** Persistent chat history for each session
- **Security:** CORS, API key management, patient data protection

### Frontend (React)
- **Modern Medical UI:** Clean, professional, and mobile-responsive
- **Patient Info Form:** Collects age, gender, and location (Ghana default)
- **Real-time Chat:** Doctor-patient conversation interface
- **Ghana Branding:** Flag, colors, and cultural context

---

## 🎨 User Experience Flow

1. **Patient Information:**  
   - Optional form for age, gender, and location (default: Ghana)
   - Option to skip and start consultation directly

2. **Professional Consultation:**  
   - Chat interface with Dr. Kwame Asare
   - Typing indicators and emergency notices

3. **Medical Conversation:**  
   - Describe symptoms naturally
   - AI provides Ghana-specific medical assessment and advice
   - First aid and emergency guidance

4. **Medical Disclaimers:**  
   - Every consultation includes clear disclaimers and emergency contacts

---

## 🇬🇭 Ghana-Specific Features

- **Local Medical Knowledge:** Malaria, typhoid, cholera, and more
- **Climate Awareness:** Tropical disease context
- **Healthcare System:** References to local hospitals and clinics
- **Cultural Sensitivity:** Ghanaian health beliefs and communication style
- **Language:** Greets with "Akwaaba!" and uses professional, Ghanaian tone

---

## 🔧 Advanced Technical Features

- **AI Integration:**  
  - Latest Gemini 2.0 Flash model  
  - Optimized medical prompting  
  - Session-based conversation memory  
  - Robust error handling and fallbacks

- **Data Management:**  
  - MongoDB consultation storage  
  - Session ID tracking  
  - Patient information privacy  
  - Consultation history retrieval

- **Security & Privacy:**  
  - CORS configuration  
  - API key management  
  - Secure session handling  
  - Medical disclaimer compliance

---

## 📱 Mobile-First Design

- **Responsive:** Works perfectly on phones and tablets
- **Touch Friendly:** Large buttons, easy scrolling
- **Fast Loading:** Optimized for slow connections
- **Professional Styling:** Ghanaian colors, clear message design, and loading indicators

---

## 🚀 Getting Started

### 1. **Clone the Repository**
```sh
git clone <your-repo-url>
cd AI-DOCTOR
```

### 2. **Backend Setup**
- **Python 3.10 recommended**
- Create and activate a virtual environment:
  ```sh
  python -m venv .venv
  .venv\Scripts\activate  # On Windows
  ```
- Install dependencies:
  ```sh
  pip install -r backend/requirements.txt
  ```
- Create a `.env` file in the `backend` folder:
  ```
  MONGO_URL=mongodb://localhost:27017
  DB_NAME=ai-doctor
  GEMINI_API_KEY=your_gemini_api_key
  ```
- Start MongoDB locally or use MongoDB Atlas.
- Run the backend:
  ```sh
  uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
  ```

### 3. **Frontend Setup**
- Open a new terminal and go to the frontend folder:
  ```sh
  cd frontend
  ```
- Install dependencies:
  ```sh
  npm install
  ```
- Create a `.env` file in `frontend`:
  ```
  REACT_APP_BACKEND_URL=http://localhost:8000
  ```
- Start the frontend:
  ```sh
  npm start
  ```
- Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🛡️ Production Deployment

- **Backend:** Deploy with a production ASGI server (e.g., Gunicorn + Uvicorn), use managed MongoDB, and set secure environment variables.
- **Frontend:** Build with `npm run build` and deploy to Vercel, Netlify, or your preferred static host.
- **Security:** Use HTTPS, restrict CORS, and never expose secrets.
- **Monitoring:** Set up logging, error monitoring, and database backups.

---

## 🧪 Testing

- **Backend:** Run and extend `backend_test.py` for API endpoint tests.
- **Frontend:** Test user flows and error handling.
- **Manual QA:** Try sample conversations and edge cases.

---

## 📝 API Endpoints

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| POST   | `/api/consult`                  | Start or continue a consultation   |
| GET    | `/api/consultations/{session}`  | Get session chat history           |
| GET    | `/api/health`                   | Health check for backend           |

---

## 🏆 Key Features

- 24/7 AI medical consultations
- Ghana-specific medical knowledge
- Secure, private, and professional
- Persistent session memory
- Mobile-first, user-friendly design

---

## 📣 Disclaimers

- This AI system provides **preliminary medical guidance only**.
- It is **not a replacement for professional medical care**.
- For emergencies, **call 193 or visit your nearest hospital**.

---

## 🙌 Acknowledgements

- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [MongoDB](https://www.mongodb.com/), and [Google Gemini](https://ai.google.dev/).
- Inspired by the healthcare needs of Ghana.

---

## 🇬🇭 Ready to Help Ghana Get Better Healthcare Access!

**Congratulations!**  
You now have a world-class AI doctor system, ready to serve patients across Ghana.

---

**Questions or feedback? Open an issue or contact the maintainer.**