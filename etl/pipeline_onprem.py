import sqlite3
from typing import List, Dict, Any
from etl.shared import splitter

def load_onprem_tickets(db_path: str) -> List[Dict[str, Any]]:
    """Carga los tickets de la base de datos sqlite onprem."""
    documents = []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Load issues
        cursor.execute("SELECT id, key, summary, status, priority, reporter, assignee, system FROM issues")
        issues = cursor.fetchall()
        
        for issue in issues:
            issue_dict = dict(issue)
            
            # Fetch related comments
            cursor.execute("SELECT author, body, is_internal FROM comments WHERE issue_id = ?", (issue_dict['id'],))
            comments = cursor.fetchall()
            
            # Construct text representation of the ticket
            content = f"Ticket {issue_dict['key']}: {issue_dict['summary']}\n"
            content += f"Status: {issue_dict['status']}\n"
            content += f"Priority: {issue_dict['priority']}\n"
            content += f"System: {issue_dict['system']}\n"
            content += f"Reporter: {issue_dict['reporter']}, Assignee: {issue_dict['assignee']}\n"
            
            if comments:
                content += "\nComments:\n"
                for comment in comments:
                    visibility = "Internal" if comment["is_internal"] else "Public"
                    content += f"- [{visibility}] {comment['author']}: {comment['body']}\n"
            
            title = f"{issue_dict['key']} - {issue_dict['summary']}"
            
            if splitter:
                chunks = splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"onprem_{issue_dict['key']}_{i}",
                        "source_id": issue_dict['key'],
                        "source": "onprem",
                        "title": title,
                        "content": chunk,
                        "url": f"sqlite://{issue_dict['key']}"
                    })
            else:
                documents.append({
                    "id": f"onprem_{issue_dict['key']}_0",
                    "source_id": issue_dict['key'],
                    "source": "onprem",
                    "title": title,
                    "content": content,
                    "url": f"sqlite://{issue_dict['key']}"
                })
        
    except sqlite3.Error as e:
        print(f"Error reading database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            
    return documents
