import json
import os
from datetime import datetime
from typing import Dict, Any

class QueryLogger:
    """
    Logs all queries and responses for analysis and research.
    Creates a structured log of STEWARD's interactions.
    """
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.log_dir = os.path.join(current_dir, 'logs')
        else:
            self.log_dir = log_dir
            
        os.makedirs(self.log_dir, exist_ok=True)
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(self.log_dir, f'session_{self.session_id}.jsonl')
        
    def log_query(self, query: str, mode: str, results: Any, metadata: Dict = None):
        """
        Log a query and its results.
        Uses JSONL format (one JSON object per line) for easy streaming.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "query": query,
            "mode": mode,  # "keyword" or "semantic"
            "result_count": len(results) if isinstance(results, list) else 0,
            "results": results,
            "metadata": metadata or {}
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            
        return entry
    
    def get_session_log(self):
        """Get all queries from current session"""
        if not os.path.exists(self.log_file):
            return []
        
        entries = []
        with open(self.log_file) as f:
            for line in f:
                entries.append(json.loads(line))
        return entries
    
    def get_all_queries(self):
        """Get all queries from all sessions"""
        all_entries = []
        for filename in sorted(os.listdir(self.log_dir)):
            if filename.startswith('session_') and filename.endswith('.jsonl'):
                filepath = os.path.join(self.log_dir, filename)
                with open(filepath) as f:
                    for line in f:
                        all_entries.append(json.loads(line))
        return all_entries
    
    def generate_report(self):
        """Generate a summary report of all queries"""
        queries = self.get_all_queries()
        
        report = {
            "total_queries": len(queries),
            "by_mode": {},
            "most_common_topics": {},
            "sessions": len(set(q['session_id'] for q in queries))
        }
        
        for q in queries:
            mode = q['mode']
            report['by_mode'][mode] = report['by_mode'].get(mode, 0) + 1
            
            # Extract keywords from query
            words = q['query'].lower().split()
            for word in words:
                if len(word) > 4:  # Only count meaningful words
                    report['most_common_topics'][word] = report['most_common_topics'].get(word, 0) + 1
        
        # Sort topics by frequency
        report['most_common_topics'] = dict(
            sorted(report['most_common_topics'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return report


# CLI for query log analysis
if __name__ == "__main__":
    import sys
    
    logger = QueryLogger()
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report = logger.generate_report()
        print(json.dumps(report, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        queries = logger.get_all_queries()
        for q in queries[-10:]:  # Last 10 queries
            print(f"[{q['timestamp']}] {q['mode']}: {q['query']} ({q['result_count']} results)")
    else:
        print("Usage:")
        print("  python3 logger.py report  # Generate summary report")
        print("  python3 logger.py list    # List recent queries")
