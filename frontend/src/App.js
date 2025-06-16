import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;
console.log("ENV:", process.env.REACT_APP_BACKEND_URL);

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [isLoading, setIsLoading] = useState(false);
  const [showPatientForm, setShowPatientForm] = useState(true);
  const [patientInfo, setPatientInfo] = useState({
    age: '',
    gender: '',
    location: 'Ghana'
  });
  const [typingText, setTypingText] = useState(''); // Current typed text
  const [typingIndex, setTypingIndex] = useState(0); // Index of character being typed
  const [currentResponse, setCurrentResponse] = useState(''); // Full response to type
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typingText]);

  useEffect(() => {
    loadConsultationHistory();
  }, []);

  const loadConsultationHistory = async () => {
    try {
      const response = await axios.get(`${API}/consultations/${sessionId}`);
      if (response.data.consultations && response.data.consultations.length > 0) {
        const formattedMessages = response.data.consultations.flatMap(consultation => [
          {
            type: 'patient',
            content: consultation.patient_message,
            timestamp: consultation.timestamp
          },
          {
            type: 'doctor',
            content: consultation.doctor_response,
            timestamp: consultation.timestamp
          }
        ]);
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Error loading consultation history:', JSON.stringify(error));
    }
  };

  const handlePatientInfoSubmit = (e) => {
    e.preventDefault();
    setShowPatientForm(false);
    
    const welcomeMessage = {
      type: 'doctor',
      content: `Akwaaba! I'm Dr. Kwame Asare from Korle Bu Teaching Hospital. I'm here to help you with your medical concerns. Please describe your symptoms or any health questions you may have, and I'll provide you with professional medical guidance.\n\nRemember, this consultation is for preliminary advice only. For serious concerns or if symptoms persist for more than 3 days, please visit a healthcare facility for proper examination.\n\nHow are you feeling today?`,
      timestamp: new Date().toISOString()
    };
    
    setMessages([welcomeMessage]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const patientMessage = {
      type: 'patient',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, patientMessage]);
    setIsLoading(true);
    setInputMessage(''); // Clear input immediately when sending starts
    setTypingText(''); // Reset typing text
    setTypingIndex(0); // Reset typing index

    try {
      const consultationRequest = {
        message: inputMessage,
        session_id: sessionId,
        patient_info: {
          age: patientInfo.age ? parseInt(patientInfo.age) : undefined,
          gender: patientInfo.gender || undefined,
          location: patientInfo.location || "Ghana"
        }
      };

      const response = await axios.post(`${API}/consult`, consultationRequest);
      setCurrentResponse(response.data.doctor_response); // Store full response for typing
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        type: 'error',
        content: 'I apologize, but I encountered a technical issue. Please try again in a moment. If the problem persists, please contact technical support or visit your nearest healthcare facility.',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Simulate character-by-character typing effect
  useEffect(() => {
    if (currentResponse && typingIndex < currentResponse.length) {
      const timer = setTimeout(() => {
        setTypingText(prev => prev + currentResponse[typingIndex]);
        setTypingIndex(prev => prev + 1);

        if (typingIndex + 1 === currentResponse.length) {
          setMessages(prev => [
            ...prev,
            {
              type: 'doctor',
              content: currentResponse,
              timestamp: new Date().toISOString()
            }
          ]);
          setCurrentResponse(''); // Clear after completion
          setTypingIndex(0); // Reset for next message
        }
      }, 15); // Adjust delay for typing speed

      return () => clearTimeout(timer);
    }
  }, [typingIndex, currentResponse]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (showPatientForm) {
    return (
      <div className="patient-form-container">
        <div className="patient-form">
          <div className="form-header">
            <h1>🏥 Ghana AI Doctor</h1>
            <h2>Dr. Kwame Asare</h2>
            <p className="hospital-info">Korle Bu Teaching Hospital, Accra</p>
          </div>
          
          <div className="form-content">
            <p className="form-description">
              Welcome to your AI medical consultation. Please provide some basic information 
              to help me give you better medical guidance. This information is optional but helpful.
            </p>
            
            <form onSubmit={handlePatientInfoSubmit}>
              <div className="form-group">
                <label htmlFor="age">Age (optional):</label>
                <input
                  id="age"
                  type="number"
                  min="1"
                  max="120"
                  value={patientInfo.age}
                  onChange={(e) => setPatientInfo({...patientInfo, age: e.target.value})}
                  placeholder="Enter your age"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="gender">Gender (optional):</label>
                <select
                  id="gender"
                  value={patientInfo.gender}
                  onChange={(e) => setPatientInfo({...patientInfo, gender: e.target.value})}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="location">Location:</label>
                <input
                  id="location"
                  type="text"
                  value={patientInfo.location}
                  onChange={(e) => setPatientInfo({...patientInfo, location: e.target.value})}
                  placeholder="City, Region"
                />
              </div>
              
              <div className="form-buttons">
                <button type="submit" className="btn-primary">
                  Start Consultation
                </button>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => setShowPatientForm(false)}
                >
                  Skip & Continue
                </button>
              </div>
            </form>
          </div>
          
          <div className="medical-disclaimer">
            <p><strong>Medical Disclaimer:</strong> This AI consultation provides preliminary medical guidance only and should not replace professional medical care. For emergencies, call 193 or visit your nearest hospital immediately.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="medical-chat-app">
      <div className="chat-header">
        <div className="doctor-info">
          <div className="doctor-avatar">🩺</div>
          <div className="doctor-details">
            <h2>Dr. Kwame Asare</h2>
            <p>Senior Physician • Korle Bu Teaching Hospital</p>
            <p className="specialization">Tropical Medicine & General Practice</p>
          </div>
        </div>
        <div className="ghana-flag">🇬🇭</div>
      </div>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.type}`}>
            <div className="message-content">
              {message.type === 'doctor' && (
                <div className="doctor-badge">
                  <span className="doctor-icon">👨‍⚕️</span>
                  <span>Dr. Asante</span>
                </div>
              )}
              {message.type === 'patient' && (
                <div className="patient-badge">
                  <span className="patient-icon">👤</span>
                  <span>You</span>
                </div>
              )}
              <div className="message-text">
                {message.content.split('\n').map((line, lineIndex) => (
                  <p key={lineIndex}>{line}</p>
                ))}
              </div>
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString('en-GB', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          </div>
        ))}
        {currentResponse && (
          <div className="message doctor">
            <div className="message-content">
              <div className="doctor-badge">
                <span className="doctor-icon">👨‍⚕️</span>
                <span>Dr. Asante</span>
              </div>
              <div className="message-text">
                <p>{typingText}</p> {/* Display the typing text */}
              </div>
              <div className="message-timestamp">
                {new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        )}
        
        {isLoading && !currentResponse && (
          <div className="message doctor loading">
            <div className="message-content">
              <div className="doctor-badge">
                <span className="doctor-icon">👨‍⚕️</span>
                <span>Dr. Asante</span>
              </div>
              <div className="message-text">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p>Dr. Asare is analyzing your symptoms...</p>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-section">
        <div className="emergency-notice">
          <p>🚨 <strong>Emergency?</strong> Call 193 or visit your nearest hospital immediately</p>
        </div>
        
        <div className="chat-input">
          <div className="input-container">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe your symptoms or ask a medical question..."
              rows="3"
              disabled={isLoading}
            />
            <button 
              onClick={sendMessage} 
              disabled={isLoading || !inputMessage.trim()}
              className="send-button"
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </div>
        </div>
        
        <div className="medical-disclaimer-footer">
          <p>
            <strong>Important:</strong> This is preliminary medical guidance. 
            If symptoms persist for more than 3 days or worsen, please visit a healthcare facility for proper examination.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;