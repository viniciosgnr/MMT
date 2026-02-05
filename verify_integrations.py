import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

API_URL = "http://localhost:8000/api"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_auth_token():
    """ Authenticate so we can call protected endpoints """
    email = "test_integration@mmt.com"
    password = "password123"
    
    auth_url = f"{SUPABASE_URL}/auth/v1"
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    
    # Try Login
    res = requests.post(f"{auth_url}/token?grant_type=password", headers=headers, json={"email": email, "password": password})
    
    if res.status_code != 200:
        print("Login failed, trying signup...")
        res = requests.post(f"{auth_url}/signup", headers=headers, json={"email": email, "password": password})
        
        if res.status_code not in [200, 201]:
             # Might require email confirmation?
             print(f"Signup failed: {res.text}")
             return None
        
        # If signup auto-signs in (depends on config), we might have token. 
        # Usually checking confirmation is needed. 
        # If auto-confirm is off, this test blocks. Assuming dev env has auto-confirm or we use an existing user.
        # Retry login?
        res = requests.post(f"{auth_url}/token?grant_type=password", headers=headers, json={"email": email, "password": password})

    if res.status_code == 200:
        data = res.json()
        return data["access_token"]
    
    print(f"Auth Failed: {res.text}")
    return None

def test_integration():
    print("--- Starting Integration Verification ---")
    
    token = get_auth_token()
    if not token:
        print("CRITICAL: Could not authenticate. Backend requires token.")
        # Try to proceed? No, mostly will fail 401.
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Test M2 -> M9: Fail a Task
    print("\n1. Testing M2 -> M9 (Calibration Failure)...")
    
    # Create a dummy task first (skipping full campaign creation for brevity, assuming ID 1 exists or fails)
    # Actually let's try to fail task #1 if it exists, or handle 404
    task_id = 999 
    
    # Check if we have any tasks
    try:
        tasks = requests.get(f"{API_URL}/calibration/tasks", headers=headers).json()
        if tasks and len(tasks) > 0:
            task_id = tasks[0]['id']
            print(f"Found existing task #{task_id}, using it.")
        else:
             print("No tasks found. Skipping M2->M9 test or need to mock data.")
    except Exception as e:
        print(f"Error fetching tasks: {e}")

    if task_id != 999:
        url = f"{API_URL}/calibration/tasks/{task_id}/fail?reason=IntegrationTestFailure"
        print(f"POST {url}")
        res = requests.post(url, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            print(f"Success! Response: {json.dumps(data, indent=2)}")
            notif_id = data.get("notification_id")
            
            # Verify Notification Created
            if notif_id:
                notif_res = requests.get(f"{API_URL}/failures", headers=headers)
                failures = notif_res.json()
                found = next((f for f in failures if f['id'] == notif_id), None)
                if found:
                    print(f"Verified: Failure Notification #{notif_id} exists in M9.")
                    print(f"Description: {found.get('description')}")
                else:
                    print("Error: Notification reported created but not found in list.")
        else:
            print(f"Failed to fail task. Status: {res.status_code}, Body: {res.text}")

    # 2. Test M5 -> Side Effects
    print("\n2. Testing M5 -> Side Effects (Manual Sync)...")
    # Simulate data ingestion
    payload = {
        "source_id": 1, # Assuming source 1 exists
        "data": [
            {
                "tag_number": "TIT-001",
                "value": 99.9,
                "timestamp": "2024-01-01T12:00:00",
                "unit": "C",
                "quality": "Good"
            }
        ]
    }
    
    # Check for sources
    sources = requests.get(f"{API_URL}/sync/sources", headers=headers).json()
    if not sources:
        # Create one
        s = requests.post(f"{API_URL}/sync/sources", json={"name": "TestBench", "type": "FLOW_COMPUTER", "connection_string": "local", "is_active": True}, headers=headers).json()
        payload["source_id"] = s["id"]
        print(f"Created Sync Source {s['id']}")
    else:
        payload["source_id"] = sources[0]["id"]

    res_sync = requests.post(f"{API_URL}/sync/ingest", json=payload, headers=headers)
    if res_sync.status_code == 200:
        print(f"Sync Ingest Success: {res_sync.json()}")
        # Check logs for "Impact analysis complete" or similar logic? 
        # Since I didn't add logging view, I assume success 200 means IntegrationService ran without crash.
    else:
        print(f"Sync Ingest Failed: {res_sync.status_code} {res_sync.text}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_integration()
