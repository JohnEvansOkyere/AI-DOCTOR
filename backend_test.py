#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
from dotenv import load_dotenv
import sys

# Load environment variables from frontend .env file to get the backend URL
load_dotenv("/app/frontend/.env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Testing backend API at: {API_URL}")

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def run_test(test_name, test_func):
    """Run a test and track results"""
    print(f"\n{'='*80}\nRunning test: {test_name}\n{'='*80}")
    try:
        result = test_func()
        if result:
            test_results["passed"] += 1
            test_results["tests"].append({"name": test_name, "status": "PASSED"})
            print(f"✅ Test PASSED: {test_name}")
        else:
            test_results["failed"] += 1
            test_results["tests"].append({"name": test_name, "status": "FAILED"})
            print(f"❌ Test FAILED: {test_name}")
        return result
    except Exception as e:
        test_results["failed"] += 1
        test_results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
        print(f"❌ Test FAILED with exception: {test_name}")
        print(f"Error: {str(e)}")
        return False

def test_root_endpoint():
    """Test the root API endpoint"""
    response = requests.get(f"{API_URL}/")
    
    # Check status code
    if response.status_code != 200:
        print(f"Root endpoint returned status code {response.status_code}")
        return False
    
    # Check response content
    data = response.json()
    if "message" not in data or "doctor" not in data or "version" not in data:
        print(f"Root endpoint missing expected fields: {data}")
        return False
    
    # Check specific content
    if "Ghana AI Doctor Agent" not in data["message"]:
        print(f"Root endpoint message doesn't contain expected text: {data['message']}")
        return False
    
    if "Dr. Kwame Asante" not in data["doctor"]:
        print(f"Root endpoint doctor doesn't contain expected name: {data['doctor']}")
        return False
    
    print(f"Root endpoint response: {json.dumps(data, indent=2)}")
    return True

def test_health_endpoint():
    """Test the health check endpoint"""
    response = requests.get(f"{API_URL}/health")
    
    # Check status code
    if response.status_code != 200:
        print(f"Health endpoint returned status code {response.status_code}")
        return False
    
    # Check response content
    data = response.json()
    if "status" not in data or "database" not in data or "ai_service" not in data:
        print(f"Health endpoint missing expected fields: {data}")
        return False
    
    # Check specific content
    if data["status"] != "healthy":
        print(f"Health endpoint status is not 'healthy': {data['status']}")
        return False
    
    print(f"Health endpoint response: {json.dumps(data, indent=2)}")
    return True

def test_consultation_without_patient_info():
    """Test medical consultation without patient info"""
    session_id = str(uuid.uuid4())
    
    payload = {
        "message": "I have been having a headache for the past 2 days and feeling dizzy.",
        "session_id": session_id
    }
    
    response = requests.post(f"{API_URL}/consult", json=payload)
    
    # Check status code
    if response.status_code != 200:
        print(f"Consultation endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check response content
    data = response.json()
    if "doctor_response" not in data or "session_id" not in data:
        print(f"Consultation response missing expected fields: {data}")
        return False
    
    # Check session ID matches
    if data["session_id"] != session_id:
        print(f"Returned session ID doesn't match: expected {session_id}, got {data['session_id']}")
        return False
    
    # Check doctor response contains medical content
    doctor_response = data["doctor_response"]
    if len(doctor_response) < 100:  # Basic check that response is substantial
        print(f"Doctor response seems too short: {doctor_response}")
        return False
    
    # Check for Ghana-specific content and medical disclaimers
    ghana_terms = ["Ghana", "Accra", "Korle Bu", "Dr. Kwame"]
    has_ghana_context = any(term in doctor_response for term in ghana_terms)
    
    disclaimer_terms = ["disclaimer", "emergency", "persist", "doctor", "hospital"]
    has_disclaimer = any(term.lower() in doctor_response.lower() for term in disclaimer_terms)
    
    if not has_ghana_context:
        print("Doctor response doesn't contain Ghana-specific context")
        print(f"Response: {doctor_response[:200]}...")
    
    if not has_disclaimer:
        print("Doctor response doesn't contain medical disclaimers")
        print(f"Response: {doctor_response[:200]}...")
    
    print(f"Consultation response ID: {data['id']}")
    print(f"Doctor response (first 200 chars): {doctor_response[:200]}...")
    return True

def test_consultation_with_patient_info():
    """Test medical consultation with patient info"""
    session_id = str(uuid.uuid4())
    
    payload = {
        "message": "I have a fever and sore throat since yesterday.",
        "session_id": session_id,
        "patient_info": {
            "age": 35,
            "gender": "Female",
            "location": "Kumasi, Ghana"
        }
    }
    
    response = requests.post(f"{API_URL}/consult", json=payload)
    
    # Check status code
    if response.status_code != 200:
        print(f"Consultation endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check response content
    data = response.json()
    if "doctor_response" not in data or "session_id" not in data or "patient_info" not in data:
        print(f"Consultation response missing expected fields: {data}")
        return False
    
    # Check patient info was stored correctly
    patient_info = data["patient_info"]
    if patient_info["age"] != 35 or patient_info["gender"] != "Female" or "Kumasi" not in patient_info["location"]:
        print(f"Patient info not stored correctly: {patient_info}")
        return False
    
    # Check doctor response contains medical content
    doctor_response = data["doctor_response"]
    if len(doctor_response) < 100:  # Basic check that response is substantial
        print(f"Doctor response seems too short: {doctor_response}")
        return False
    
    print(f"Consultation response ID: {data['id']}")
    print(f"Doctor response (first 200 chars): {doctor_response[:200]}...")
    return True

def test_multiple_consultations_same_session():
    """Test multiple consultations in the same session"""
    session_id = str(uuid.uuid4())
    
    # First consultation
    payload1 = {
        "message": "I have a persistent cough and chest pain.",
        "session_id": session_id,
        "patient_info": {
            "age": 42,
            "gender": "Male",
            "location": "Accra, Ghana"
        }
    }
    
    response1 = requests.post(f"{API_URL}/consult", json=payload1)
    if response1.status_code != 200:
        print(f"First consultation failed with status code {response1.status_code}")
        return False
    
    # Wait briefly to ensure different timestamps
    time.sleep(1)
    
    # Second consultation (follow-up)
    payload2 = {
        "message": "I also have difficulty breathing when I lie down.",
        "session_id": session_id
    }
    
    response2 = requests.post(f"{API_URL}/consult", json=payload2)
    if response2.status_code != 200:
        print(f"Second consultation failed with status code {response2.status_code}")
        return False
    
    # Check that both consultations have the same session ID
    data1 = response1.json()
    data2 = response2.json()
    
    if data1["session_id"] != session_id or data2["session_id"] != session_id:
        print(f"Session IDs don't match: {data1['session_id']}, {data2['session_id']}, expected {session_id}")
        return False
    
    print(f"First consultation ID: {data1['id']}")
    print(f"Second consultation ID: {data2['id']}")
    
    return True

def test_consultation_history():
    """Test consultation history retrieval"""
    # Create a new session with multiple consultations
    session_id = str(uuid.uuid4())
    
    # First consultation
    payload1 = {
        "message": "I have been experiencing stomach pain after meals.",
        "session_id": session_id,
        "patient_info": {
            "age": 28,
            "gender": "Female",
            "location": "Tamale, Ghana"
        }
    }
    
    response1 = requests.post(f"{API_URL}/consult", json=payload1)
    if response1.status_code != 200:
        print(f"First consultation failed with status code {response1.status_code}")
        return False
    
    # Wait briefly to ensure different timestamps
    time.sleep(1)
    
    # Second consultation
    payload2 = {
        "message": "The pain is worse when I eat spicy food.",
        "session_id": session_id
    }
    
    response2 = requests.post(f"{API_URL}/consult", json=payload2)
    if response2.status_code != 200:
        print(f"Second consultation failed with status code {response2.status_code}")
        return False
    
    # Now retrieve the consultation history
    response = requests.get(f"{API_URL}/consultations/{session_id}")
    
    # Check status code
    if response.status_code != 200:
        print(f"History endpoint returned status code {response.status_code}")
        return False
    
    # Check response content
    data = response.json()
    if "session_id" not in data or "consultations" not in data:
        print(f"History response missing expected fields: {data}")
        return False
    
    # Check session ID matches
    if data["session_id"] != session_id:
        print(f"Returned session ID doesn't match: expected {session_id}, got {data['session_id']}")
        return False
    
    # Check that we have both consultations
    consultations = data["consultations"]
    if len(consultations) != 2:
        print(f"Expected 2 consultations, got {len(consultations)}")
        return False
    
    # Check that consultations contain the correct messages
    messages = [c["patient_message"] for c in consultations]
    if "stomach pain" not in messages[0] or "spicy food" not in messages[1]:
        print(f"Consultation messages don't match expected content: {messages}")
        return False
    
    print(f"Retrieved {len(consultations)} consultations for session {session_id}")
    return True

def test_error_handling():
    """Test error handling for invalid requests"""
    # Test missing required field (message)
    payload = {
        "session_id": str(uuid.uuid4())
        # Missing "message" field
    }
    
    response = requests.post(f"{API_URL}/consult", json=payload)
    
    # Should return a 422 Unprocessable Entity for validation error
    if response.status_code != 422:
        print(f"Expected status code 422 for invalid request, got {response.status_code}")
        return False
    
    # Test invalid session ID format in history endpoint
    response = requests.get(f"{API_URL}/consultations/invalid-session-id")
    
    # This should still return 200 but with empty consultations list
    # or 404/400 depending on implementation
    if response.status_code == 200:
        data = response.json()
        if len(data.get("consultations", [])) > 0:
            print(f"Expected empty consultations for invalid session ID, got {data}")
            return False
    elif response.status_code not in [400, 404, 422]:
        print(f"Expected status code 400/404/422 for invalid session ID, got {response.status_code}")
        return False
    
    print("Error handling tests passed")
    return True

def run_all_tests():
    """Run all tests and print summary"""
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check Endpoint", test_health_endpoint),
        ("Consultation Without Patient Info", test_consultation_without_patient_info),
        ("Consultation With Patient Info", test_consultation_with_patient_info),
        ("Multiple Consultations Same Session", test_multiple_consultations_same_session),
        ("Consultation History", test_consultation_history),
        ("Error Handling", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Total tests: {test_results['passed'] + test_results['failed']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    # Print detailed results
    print("\nDetailed Results:")
    for test in test_results["tests"]:
        status_symbol = "✅" if test["status"] == "PASSED" else "❌"
        print(f"{status_symbol} {test['name']}: {test['status']}")
        if "error" in test:
            print(f"   Error: {test['error']}")
    
    return test_results["failed"] == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
