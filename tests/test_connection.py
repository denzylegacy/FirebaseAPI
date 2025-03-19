#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplified script to validate token and list users from the Firebase API
"""

import requests
import json
import time
import sys

from app.settings import CONFIG


class FirebaseAPIClient:
    """Client for interacting with the Firebase API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        """Initialize the API client"""
        self.base_url = base_url
        self.token = None
        self.token_expiry = 0
        self.headers = {
            "Content-Type": "application/json"
        }
        
        self.email = CONFIG.ADMIN_EMAIL
        self.password = CONFIG.ADMIN_PASSWORD
    
    def check_server_status(self):
        """Check if the server is online"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server is online!")
                return True
            else:
                print(f"❌ API server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API server. Make sure the server is running.")
            return False
        except Exception as e:
            print(f"❌ Error checking server status: {str(e)}")
            return False
    
    def login(self):
        """Login to the API and get a token"""
        if not self.check_server_status():
            return False
            
        url = f"{self.base_url}/api/v1/auth/login-json"
        data = {
            "email": self.email,
            "password": self.password
        }
        
        print(f"🔑 Attempting login with {self.email}...")
        
        try:
            response = requests.post(
                url, 
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                self.headers["Authorization"] = f"Bearer {self.token}"
                # Token expires in 10 minutes (600 seconds)
                self.token_expiry = time.time() + 600
                print(f"✅ Login successful!")
                return True
            else:
                print(f"❌ Login error: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API server.")
            return False
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False
    
    def is_token_valid(self):
        """Check if the token is still valid"""
        if not self.token:
            print("❌ No token available. Please login first.")
            return False
        
        # Check if token has expired
        if time.time() > self.token_expiry:
            print("⚠️ Token expired. Renewing...")
            return self.login()
        
        url = f"{self.base_url}/api/v1/auth/user/me"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.ok:
                print("✅ Token is valid!")
                return True
            else:
                print(f"❌ Invalid token: {response.text}")
                return self.login()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API server. Make sure the server is running.")
            return False
        except Exception as e:
            print(f"❌ Error validating token: {str(e)}")
            return False
    
    def list_users(self):
        """List all users in the database"""
        if not self.is_token_valid():
            return None
        
        url = f"{self.base_url}/api/v1/data/users"
        
        try:
            print(f"Attempting to access: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json()
                print(f"✅ {len(users)} users found!")
                return users
            else:
                print(f"❌ Error listing users: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API server.")
            return None
        except Exception as e:
            print(f"❌ Error listing users: {str(e)}")
            return None
    
    def get_user_details(self, user_id):
        """Get details for a specific user"""
        if not self.is_token_valid():
            return None
        
        url = f"{self.base_url}/api/v1/data/users/{user_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ User details for {user_id} retrieved successfully!")
                return user
            else:
                print(f"❌ Error getting user details: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API server. Make sure the server is running.")
            return None
        except Exception as e:
            print(f"❌ Error getting user details: {str(e)}")
            return None
    
    def is_admin(self):
        """Check if the current user is an admin"""
        if not self.is_token_valid():
            return False
        
        url = f"{self.base_url}/api/v1/auth/user/me"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.ok:
                user_data = response.json()
                is_admin = user_data.get("is_admin", False)
                print(f"User admin status: {is_admin}")
                return is_admin
            else:
                print(f"Error checking admin status: {response.text}")
                return False
        except Exception as e:
            print(f"Error checking admin status: {str(e)}")
            return False
    
    def check_admin_exists(self):
        """Check if admin user exists in Firebase"""
        url = f"{self.base_url}/api/v1/auth/check-admin"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                admin_data = response.json()
                if admin_data.get("exists", False):
                    print("✅ Admin user exists in Firebase")
                    print(f"Admin data: {json.dumps(admin_data, indent=2)}")
                    return True
                else:
                    print("❌ Admin user does not exist in Firebase")
                    return False
            else:
                print(f"❌ Error checking admin user: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error checking admin user: {str(e)}")
            return False

    def check_firebase_connection(self):
        """Check if the Firebase connection is working"""
        url = f"{self.base_url}/api/v1/auth/test"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("✅ API test endpoint is working!")
                return True
            else:
                print(f"❌ API test endpoint returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking API test endpoint: {str(e)}")
            return False


def main():
    """Main function"""
    client = FirebaseAPIClient()
    
    if not client.check_server_status():
        print("\n⚠️ Instructions to start the API server:")
        print("1. Open a terminal")
        print("2. Navigate to the project directory")
        print("3. Run: uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload")
        print("4. Try running this script again after starting the server")
        sys.exit(1)
    
    # Check if the API test endpoint is working
    client.check_firebase_connection()
    
    # Check if admin exists
    client.check_admin_exists()
    
    # Try login with direct credentials
    print("\nTrying login with direct credentials...")
    direct_login_url = f"{client.base_url}/api/v1/auth/login-json"
    direct_login_data = {
        "email": "admin@example.com",
        "password": "$296p36WQoeG6Lruj3vjPGga31lW"
    }
    
    try:
        response = requests.post(
            direct_login_url,
            json=direct_login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Continue with normal login
    if not client.login():
        print("❌ Could not login. Exiting.")
        return
    
    # Check if user is admin
    if client.is_admin():
        print("✅ Current user has admin privileges")
        
        # List all users (admin only)
        users = client.list_users()
        if users:
            print("\n📋 User list:")
            for user_id, user_data in users.items():
                print(f"  • ID: {user_id}")
                print(f"    Email: {user_data.get('email', 'N/A')}")
                print(f"    Username: {user_data.get('username', 'N/A')}")
                print(f"    Admin: {'Yes' if user_data.get('is_admin', False) else 'No'}")
                print(f"    Status: {'Active' if not user_data.get('disabled', False) else 'Inactive'}")
                print("")
    else:
        print("⚠️ Current user does not have admin privileges")
        print("Some operations will not be available")


if __name__ == "__main__":
    main() 