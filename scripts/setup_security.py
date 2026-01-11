"""
Security setup script
Generate secure keys and password hashes for production
"""
import secrets
import bcrypt
import os
import sys

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(64)

def generate_password_hash(password: str) -> str:
    """Generate bcrypt password hash"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def main():
    print("=" * 60)
    print("OneSpace Security Setup")
    print("=" * 60)
    
    # 1. Generate JWT Secret Key
    jwt_secret = generate_secret_key()
    print("\n[+] Generated Secure JWT Secret Key")
    
    # 2. Get Admin Password
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        while True:
            try:
                password = input("\nEnter admin password (min 8 chars): ").strip()
                if len(password) >= 8:
                    break
                print("Password too short! Please use at least 8 characters.")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                return
    
    password_hash = generate_password_hash(password)
    print("[+] Generated Admin Password Hash")
    
    # 3. Create/Update .env file
    env_content = f"""# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=onespace

# Security
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH={password_hash}

# App
DEBUG=True
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
MAX_UPLOAD_SIZE_MB=10
"""
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
        
    print(f"\n[+] Security configuration written to {env_path}")
    print("\nConfiguration Summary:")
    print("-" * 30)
    print(f"JWT_SECRET_KEY: {jwt_secret[:10]}...")
    print(f"ADMIN_USERNAME: admin")
    print(f"ADMIN_PASSWORD: {password}")
    print("-" * 30)
    print("\nPlease restart the backend server to apply changes.")

if __name__ == "__main__":
    main()
