import sqlite3

def migrate():
    print("Migrating DB...")
    conn = sqlite3.connect('data/classroom.db')
    c = conn.cursor()

    # Check if summary_text exists
    c.execute("PRAGMA table_info(downloaded_files)")
    columns = [col[1] for col in c.fetchall()]

    if 'summary_text' not in columns:
        print("Adding summary_text column...")
        c.execute("ALTER TABLE downloaded_files ADD COLUMN summary_text TEXT")

    # Create user_settings if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
