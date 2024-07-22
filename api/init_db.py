from utils import connect_db, create_user, user_exists

def initialize_db():
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user2 (
            id UUID PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            phone_number VARCHAR(15),
            password VARCHAR(64)
        )
    """)

    users = [
        ("John Doe", "john@example.com", "1234567890", "password123"),
        ("Jane Smith", "jane@example.com", "9876543210", "password456"),
        ("Jane Smith", "janes@example.com", "9876548900", "password789")
    ]

    for name, email, phone_number, password in users:
        if not user_exists(cur, email):
            create_user(cur, name, email, phone_number, password)
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    initialize_db()
