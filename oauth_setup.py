"""
YouTube OAuth Setup Script

This script will:
1. Use your client_secret.json credentials
2. Open a browser for you to authorize the app
3. Save the OAuth token to token.json
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def main():
    print("\n" + "="*80)
    print("🔐 YouTube OAuth Setup")
    print("="*80)
    
    # Find client secret file
    client_secret_path = Path("whats_eat") / "client_secret_797713590203-le9kctqmfmek6ksgrgmocd2cepaqdlvu.apps.googleusercontent.com.json"
    
    if not client_secret_path.exists():
        print(f"❌ client_secret file not found at: {client_secret_path}")
        return
    
    print(f"✓ Found client_secret: {client_secret_path.name}")
    
    # Check if token already exists
    token_path = Path("token.json")
    if token_path.exists():
        print(f"\n⚠️  token.json already exists at: {token_path}")
        response = input("Do you want to regenerate it? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
        print("Regenerating token...")
    
    print("\n" + "="*80)
    print("🌐 Starting OAuth Flow")
    print("="*80)
    print("A browser window will open for you to:")
    print("1. Sign in to your Google account")
    print("2. Authorize 'WhatsEat' to access your YouTube data")
    print("3. Grant 'Read-only' access to your YouTube account")
    print("")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path),
            SCOPES
        )
        
        # This will open browser for authorization
        print("\n🔓 Opening browser for authorization...")
        creds = flow.run_local_server(port=0)
        
        # Save the credentials
        print("\n💾 Saving credentials...")
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
        
        print("\n" + "="*80)
        print("✅ OAuth Setup Successful!")
        print("="*80)
        print(f"✓ Token saved to: {token_path.absolute()}")
        print(f"✓ Token expires: {creds.expiry}")
        print(f"✓ Scopes authorized: {creds.scopes}")
        
        print("\n📋 You can now run:")
        print("   python tests\\test_user_profile_real.py")
        print("\nThis will fetch your actual YouTube data!")
        
    except Exception as e:
        print(f"\n❌ Error during OAuth flow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
