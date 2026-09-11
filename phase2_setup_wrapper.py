#!/usr/bin/env python3
"""Phase 2 setup wrapper - bypasses input() function"""
import sys
import os

# Add project to path
sys.path.insert(0, r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine")

# Import the Phase2Setup class
from phase2_setup import Phase2Setup

def main():
    print("[*] Phase 2: PostgreSQL Database Setup")
    print("[*] Starting automated setup...")
    print()
    
    # Use default password
    db_password = "postgres"
    
    try:
        setup = Phase2Setup(
            db_user="postgres",
            db_password=db_password,
            db_host="localhost",
            db_port=5432
        )
        
        print(f"[+] Phase 2Setup initialized")
        print(f"[+] PostgreSQL: localhost:{5432}")
        print(f"[+] Database: customer_intelligence")
        print()
        
        # Run the full setup
        success = setup.run_setup()
        
        if success:
            print("\n[✓] Phase 2 setup COMPLETED SUCCESSFULLY")
            sys.exit(0)
        else:
            print("\n[!] Phase 2 setup FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[!] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
