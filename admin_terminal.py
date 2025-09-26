#!/usr/bin/env python3
"""
Admin Terminal App for Kaonic Serial Number System
Manages public key registration requests with a user-friendly terminal interface.
"""

import requests
import json
import sys
from datetime import datetime
from typing import List, Dict, Optional

class AdminTerminal:
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url
        self.session = requests.Session()
        
    def test_connection(self) -> bool:
        """Test connection to the server"""
        try:
            response = self.session.get(f"{self.server_url}/verify?sn=K1S-A001", timeout=5)
            return response.status_code in [200, 404]  # 404 is OK for non-existent serial
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def get_registration_requests(self) -> List[Dict]:
        """Fetch all registration requests from the server"""
        try:
            response = self.session.get(f"{self.server_url}/admin/registration_requests")
            if response.status_code == 200:
                data = response.json()
                return data.get('requests', [])
            else:
                print(f"❌ Failed to fetch requests: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching requests: {e}")
            return []
    
    def approve_request(self, request_id: int, approved_by: str = "admin_terminal") -> bool:
        """Approve a registration request"""
        try:
            response = self.session.post(
                f"{self.server_url}/admin/approve_request/{request_id}",
                json={"approved_by": approved_by}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Approved request {request_id} for factory: {data.get('factory_name')}")
                return True
            else:
                print(f"❌ Failed to approve request: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error approving request: {e}")
            return False
    
    def deny_request(self, request_id: int, denied_by: str = "admin_terminal") -> bool:
        """Deny a registration request"""
        try:
            response = self.session.post(
                f"{self.server_url}/admin/deny_request/{request_id}",
                json={"denied_by": denied_by}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"❌ Denied request {request_id} for factory: {data.get('factory_name')}")
                return True
            else:
                print(f"❌ Failed to deny request: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error denying request: {e}")
            return False
    
    def revoke_request(self, request_id: int, revoked_by: str = "admin_terminal") -> bool:
        """Revoke an approved registration request"""
        try:
            response = self.session.post(
                f"{self.server_url}/admin/revoke_request/{request_id}",
                json={"revoked_by": revoked_by}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🔄 Revoked request {request_id} for factory: {data.get('factory_name')}")
                return True
            else:
                print(f"❌ Failed to revoke request: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error revoking request: {e}")
            return False
    
    def display_requests(self, requests: List[Dict]) -> None:
        """Display registration requests in a formatted table"""
        if not requests:
            print("📭 No registration requests found.")
            return
        
        print(f"\n📋 Registration Requests ({len(requests)} total)")
        print("=" * 120)
        print(f"{'ID':<4} {'Factory Name':<20} {'Status':<10} {'Created':<20} {'Approved By':<15} {'Public Key':<50}")
        print("-" * 120)
        
        for req in requests:
            try:
                request_id = req.get('id', 'N/A')
                factory_name = (req.get('factory_name') or 'N/A')[:18]
                status = req.get('status', 'N/A')
                created_at = req.get('created_at', 'N/A')
                approved_by = (req.get('approved_by') or 'N/A')[:13]
                public_key = (req.get('public_key') or 'N/A')[:47]
                
                # Format created date
                if created_at and created_at != 'N/A':
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                # Color coding for status
                status_colors = {
                    'pending': '🟡',
                    'approved': '🟢',
                    'denied': '🔴'
                }
                status_icon = status_colors.get(status, '⚪')
                
                print(f"{request_id:<4} {factory_name:<20} {status_icon} {status:<8} {created_at:<20} {approved_by:<15} {public_key:<50}")
            except Exception as e:
                print(f"❌ Error displaying request {req.get('id', 'unknown')}: {e}")
                continue
    
    def display_request_details(self, request: Dict) -> None:
        """Display detailed information about a specific request"""
        print(f"\n📄 Request Details - ID: {request.get('id')}")
        print("=" * 60)
        print(f"Factory Name: {request.get('factory_name')}")
        print(f"Status: {request.get('status')}")
        print(f"Created: {request.get('created_at')}")
        print(f"Approved At: {request.get('approved_at', 'N/A')}")
        print(f"Approved By: {request.get('approved_by', 'N/A')}")
        print(f"Public Key: {request.get('public_key_full', request.get('public_key'))}")
        print("=" * 60)
    
    def get_user_choice(self, prompt: str, valid_choices: List[str]) -> str:
        """Get user input with validation"""
        while True:
            choice = input(f"\n{prompt} ").strip().lower()
            if choice in valid_choices:
                return choice
            print(f"❌ Invalid choice. Please enter one of: {', '.join(valid_choices)}")
    
    def select_request_by_id(self, requests: List[Dict]) -> Optional[Dict]:
        """Allow user to select a request by ID"""
        if not requests:
            print("📭 No requests available to select.")
            return None
        
        # Display requests with IDs
        self.display_requests(requests)
        
        # Get valid IDs
        valid_ids = [str(req.get('id')) for req in requests]
        valid_ids.append('back')
        
        while True:
            choice = input(f"\nEnter request ID to select (or 'back' to return): ").strip()
            if choice == 'back':
                return None
            elif choice in valid_ids:
                request_id = int(choice)
                return next((req for req in requests if req.get('id') == request_id), None)
            else:
                print(f"❌ Invalid ID. Available IDs: {', '.join(valid_ids[:-1])}")
    
    def process_single_request(self, request: Dict) -> None:
        """Process a single request with detailed menu"""
        self.display_request_details(request)
        
        status = request.get('status', '').lower()
        request_id = request.get('id')
        
        if status == 'pending':
            print("\n📋 Available Actions:")
            print("  approve - Approve this request")
            print("  deny    - Deny this request")
            print("  back    - Return to main menu")
            
            choice = self.get_user_choice("Choose action:", ['approve', 'deny', 'back'])
            
            if choice == 'approve':
                self.approve_request(request_id)
            elif choice == 'deny':
                self.deny_request(request_id)
            elif choice == 'back':
                return
                
        elif status == 'approved':
            print("\n📋 Available Actions:")
            print("  revoke  - Revoke approval (reset to pending)")
            print("  back    - Return to main menu")
            
            choice = self.get_user_choice("Choose action:", ['revoke', 'back'])
            
            if choice == 'revoke':
                self.revoke_request(request_id)
            elif choice == 'back':
                return
                
        elif status == 'denied':
            print("\n📋 Available Actions:")
            print("  approve - Approve this request")
            print("  back    - Return to main menu")
            
            choice = self.get_user_choice("Choose action:", ['approve', 'back'])
            
            if choice == 'approve':
                self.approve_request(request_id)
            elif choice == 'back':
                return
        
        # Wait for user to continue
        input("\nPress Enter to continue...")
    
    def show_summary(self, requests: List[Dict]) -> None:
        """Show summary statistics"""
        if not requests:
            print("📭 No requests to summarize.")
            return
        
        pending = len([r for r in requests if r.get('status') == 'pending'])
        approved = len([r for r in requests if r.get('status') == 'approved'])
        denied = len([r for r in requests if r.get('status') == 'denied'])
        
        print(f"\n📊 Summary Statistics")
        print("=" * 30)
        print(f"Total Requests: {len(requests)}")
        print(f"🟡 Pending: {pending}")
        print(f"🟢 Approved: {approved}")
        print(f"🔴 Denied: {denied}")
        print("=" * 30)
    
    def run(self) -> None:
        """Main application loop"""
        print("🔐 Kaonic Serial Number System - Admin Terminal")
        print("=" * 50)
        
        # Test connection
        if not self.test_connection():
            print("❌ Cannot connect to server. Please check if the server is running.")
            return
        
        print("✅ Connected to server successfully!")
        
        while True:
            print(f"\n🏠 Main Menu")
            print("=" * 20)
            print("1. List all requests")
            print("2. Select request by ID")
            print("3. Show summary")
            print("4. Refresh data")
            print("5. Quit")
            
            choice = self.get_user_choice("Choose option (1-5):", ['1', '2', '3', '4', '5'])
            
            if choice == '1':
                requests = self.get_registration_requests()
                self.display_requests(requests)
                input("\nPress Enter to continue...")
                
            elif choice == '2':
                requests = self.get_registration_requests()
                selected_request = self.select_request_by_id(requests)
                if selected_request:
                    self.process_single_request(selected_request)
                    
            elif choice == '3':
                requests = self.get_registration_requests()
                self.show_summary(requests)
                input("\nPress Enter to continue...")
                
            elif choice == '4':
                print("🔄 Refreshing data...")
                requests = self.get_registration_requests()
                print(f"✅ Found {len(requests)} requests")
                
            elif choice == '5':
                print("👋 Goodbye!")
                break

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Admin Terminal for Kaonic Serial Number System")
    parser.add_argument("--server", default="http://localhost:5000", 
                       help="Server URL (default: http://localhost:5000)")
    
    args = parser.parse_args()
    
    try:
        admin = AdminTerminal(args.server)
        admin.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
