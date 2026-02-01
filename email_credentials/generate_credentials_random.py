import csv
import random
import string
from datetime import datetime

def generate_password(length=12):
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

def generate_random_email():
    """Generate a completely random Gmail address."""
    adjectives = ["blue", "red", "fast", "smart", "quick", "happy", "lucky", "bright", "dark", "wild", "calm", "bold"]
    animals = ["tiger", "eagle", "wolf", "dragon", "phoenix", "lion", "bear", "fox", "shark", "cobra", "hawk", "raven"]
    
    name = f"{random.choice(adjectives)}{random.choice(animals)}"
    number = random.randint(100, 9999)
    
    return f"{name}{number}@gmail.com"

def generate_username(index):
    """Generate a random username."""
    adjectives = ["blue", "red", "fast", "smart", "quick", "happy", "lucky", "bright"]
    nouns = ["tiger", "eagle", "wolf", "dragon", "phoenix", "lion", "bear", "fox"]
    return f"{random.choice(adjectives)}{random.choice(nouns)}{index}"

def generate_credentials(count=100):
    """Generate count credentials with random emails."""
    credentials = []
    emails_used = set()
    
    for i in range(1, count + 1):
        # Generate unique email
        while True:
            email = generate_random_email()
            if email not in emails_used:
                emails_used.add(email)
                break
        
        username = generate_username(i)
        password = generate_password()
        date_created = datetime.now().strftime("%Y-%m-%d")
        
        credentials.append({
            "Email": email,
            "Username": username,
            "Password": password,
            "Date Created": date_created,
            "Notes": ""
        })
    
    return credentials

def save_to_csv(credentials, filename="credentials.csv"):
    """Save credentials to CSV file."""
    if not credentials:
        return
    
    keys = credentials[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(credentials)
    
    print(f"[OK] Saved {len(credentials)} credentials to '{filename}'")

def save_to_json(credentials, filename="credentials.json"):
    """Save credentials to JSON file."""
    import json
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(credentials, f, indent=2)
    
    print(f"[OK] Saved {len(credentials)} credentials to '{filename}'")

if __name__ == "__main__":
    NUM_CREDENTIALS = 100
    
    print("Generating 100 random email credentials...")
    credentials = generate_credentials(NUM_CREDENTIALS)
    
    # Save both formats
    save_to_csv(credentials, "credentials.csv")
    save_to_json(credentials, "credentials.json")
    
    # Print first 10 as preview
    print("\n[PREVIEW] First 10 credentials:")
    for i, cred in enumerate(credentials[:10], 1):
        print(f"  {i}. Email: {cred['Email']} | Username: {cred['Username']} | Password: {cred['Password']}")
    
    print(f"\n[DONE] Ready to import into Google Sheets!")
