
import sqlite3

# --- Configuration ---
DB_FILE_PATH = 'chats.db'
# --- ---

def analyze_usage_by_month():
    """Connects to the database and counts chat usage by month."""
    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()

        query = """
        SELECT 
            strftime('%Y-%m', datetime(created_at, 'unixepoch')) as month,
            COUNT(id) as chat_count
        FROM 
            chats
        GROUP BY 
            month
        ORDER BY 
            month;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("No chat data found in the database.")
            return

        print("聊天使用次數統計 (按月份):")
        print("=" * 30)
        print(f"{'月份':<10} | {'使用次數':<10}")
        print("-" * 30)

        for row in results:
            month, count = row
            print(f"{month:<10} | {count:<10}")
        
        print("=" * 30)

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: The database file '{DB_FILE_PATH}' was not found.", file=sys.stderr)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    analyze_usage_by_month()
