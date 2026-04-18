import asyncio
from database import connect_db, close_db, faculty_collection
from security import hash_password

async def run_seed():
    # 1. Connect to the database
    await connect_db()
    col = faculty_collection()

    # 2. Check if the account already exists
    existing = await col.find_one({"email": "anand@manit.ac.in"})
    if existing:
        print("\n⚠️ Test account already exists in the database!")
    else:
        # 3. Create the test account
        print("\n⏳ Seeding database...")
        test_faculty = {
            "name": "Dr. Anand",
            "email": "anand@manit.ac.in",
            "emp_id": "MANIT-CS-001",
            "department": "Computer Science",
            "designation": "Professor",
            "profile_photo_url": None,
            "status": "unclaimed",
            "password_hash": hash_password("password123"), # Default temp password
            "publications": [],
            "experience": [],
            "certifications": []
        }
        
        await col.insert_one(test_faculty)
        print("✅ Successfully created test account!")
        print("   Email: anand@manit.ac.in")
        print("   Password: password123")

    # 4. Close the connection
    await close_db()

if __name__ == "__main__":
    asyncio.run(run_seed())