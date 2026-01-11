"""
Password hash generation tool
Generate bcrypt hash for admin password
"""
import sys
import bcrypt


def generate_hash(password: str) -> str:
    """Generate bcrypt password hash"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_hash(password: str, hashed: str) -> bool:
    """Verify password"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_password_hash.py <password>")
        print("Example: python generate_password_hash.py mypassword123")
        sys.exit(1)
    
    password = sys.argv[1]
    hashed = generate_hash(password)
    
    print("\n" + "=" * 60)
    print("Password hash generated successfully!")
    print("=" * 60)
    print(f"\nOriginal password: {password}")
    print(f"Bcrypt hash: {hashed}")
    print("\nAdd this to your .env file:")
    print(f"ADMIN_PASSWORD_HASH={hashed}")
    print("\n" + "=" * 60)
    
    # Verify
    if verify_hash(password, hashed):
        print("OK - Hash verification passed")
    else:
        print("ERROR - Hash verification failed")
