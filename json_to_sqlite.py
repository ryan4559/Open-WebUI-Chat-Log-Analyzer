import sqlite3
import ijson
import json
import sys
import argparse
import glob
import os

# --- Configuration ---
DB_FILE_PATH = 'chats.db' # Fixed database file name
# --- ---

def create_tables(cursor):
    """Creates the necessary tables in the SQLite database."""
    # (The table creation logic remains the same)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        archived BOOLEAN,
        pinned BOOLEAN,
        folder_id TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        chat_id TEXT,
        role TEXT,
        content TEXT,
        model TEXT,
        timestamp INTEGER,
        FOREIGN KEY (chat_id) REFERENCES chats (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        chat_id TEXT,
        tag_name TEXT,
        PRIMARY KEY (chat_id, tag_name),
        FOREIGN KEY (chat_id) REFERENCES chats (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_models (
        chat_id TEXT,
        model_name TEXT,
        PRIMARY KEY (chat_id, model_name),
        FOREIGN KEY (chat_id) REFERENCES chats (id)
    )
    ''')
    print("Database tables created or already exist.")

def find_json_file():
    """Automatically find a single .json file in the current directory."""
    json_files = glob.glob('*.json')
    if len(json_files) == 1:
        return json_files[0]
    elif len(json_files) == 0:
        print("Error: No JSON file found in the current directory.", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Error: Multiple JSON files found: {', '.join(json_files)}", file=sys.stderr)
        print("Please specify which one to process by running: python json_to_sqlite.py <filename>", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to stream JSON and populate the SQLite database."""
    parser = argparse.ArgumentParser(description="Convert an Open WebUI JSON export to a SQLite database.")
    parser.add_argument('json_file', nargs='?', default=None, 
                        help="Path to the JSON file to process. If not provided, the script will look for a single .json file in the current directory.")
    args = parser.parse_args()

    if args.json_file:
        json_file_path = args.json_file
    else:
        json_file_path = find_json_file()

    # Generate DB name from JSON file name, e.g., 'my_export.json' -> 'my_export.db'
    db_file_path = DB_FILE_PATH

    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        create_tables(cursor)

        print(f"Starting data migration from \"{json_file_path}\" to \"{db_file_path}\"..." )
        
        with open(json_file_path, 'rb') as f:
            chat_objects = ijson.items(f, 'item')
            count = 0
            for chat in chat_objects:
                try:
                    # --- Insert into chats table ---
                    cursor.execute('''
                    INSERT OR IGNORE INTO chats (id, user_id, title, created_at, updated_at, archived, pinned, folder_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                        chat.get('id'), chat.get('user_id'), chat.get('title'),
                        chat.get('created_at'), chat.get('updated_at'), chat.get('archived'),
                        chat.get('pinned'), chat.get('folder_id')
                    ))

                    chat_details = chat.get('chat', {})
                    chat_id = chat.get('id')

                    # --- Insert into messages table ---
                    if 'messages' in chat_details and isinstance(chat_details['messages'], list):
                        for message in chat_details['messages']:
                            if isinstance(message, dict):
                                cursor.execute('''
                                INSERT OR IGNORE INTO messages (id, chat_id, role, content, model, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?)''', (
                                    message.get('id'), chat_id, message.get('role'),
                                    message.get('content'), message.get('model'),
                                    message.get('timestamp')
                                ))

                    # --- Insert into tags table ---
                    all_tags = set()
                    if 'tags' in chat_details and isinstance(chat_details.get('tags'), list):
                        all_tags.update(chat_details['tags'])
                    if 'meta' in chat and isinstance(chat.get('meta'), dict) and isinstance(chat['meta'].get('tags'), list):
                        all_tags.update(chat['meta']['tags'])
                    
                    for tag in all_tags:
                        cursor.execute('''
                        INSERT OR IGNORE INTO tags (chat_id, tag_name) VALUES (?, ?)''', (chat_id, tag))

                    # --- Insert into chat_models table ---
                    if 'models' in chat_details and isinstance(chat_details.get('models'), list):
                        for model_name in chat_details['models']:
                            cursor.execute('''
                            INSERT OR IGNORE INTO chat_models (chat_id, model_name) VALUES (?, ?)''', (chat_id, model_name))

                except Exception as e:
                    print(f"\nSkipping a record due to an error during processing: {e}", file=sys.stderr)
                    continue

                count += 1
                if count % 100 == 0:
                    sys.stdout.write(f"\rProcessed {count} chat records...")
                    sys.stdout.flush()
                    conn.commit()

        conn.commit()
        conn.close()
        print(f"\nSuccessfully migrated {count} chat records to \"{db_file_path}\".")

    except FileNotFoundError:
        print(f"Error: The file \"{json_file_path}\" was not found.", file=sys.stderr)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
