import os
import json
import yaml
from datetime import datetime
from typing import List, Dict, Optional

class JobQueue:
    """
    Simple job queue for STEWARD agent.
    Allows queuing tasks for the agent to process.
    """
    
    def __init__(self, queue_dir: str = None):
        if queue_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.queue_dir = os.path.join(current_dir, 'jobs')
        else:
            self.queue_dir = queue_dir
            
        os.makedirs(self.queue_dir, exist_ok=True)
        
    def enqueue(self, task: Dict) -> str:
        """
        Add a task to the queue.
        Returns the job ID.
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_file = os.path.join(self.queue_dir, f"{job_id}.json")
        
        job_data = {
            "id": job_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "task": task
        }
        
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
            
        return job_id
    
    def get_pending(self) -> List[Dict]:
        """Get all pending jobs"""
        jobs = []
        for filename in os.listdir(self.queue_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.queue_dir, filename)) as f:
                    job = json.load(f)
                    if job['status'] == 'pending':
                        jobs.append(job)
        return sorted(jobs, key=lambda x: x['created_at'])
    
    def mark_complete(self, job_id: str, result: Dict):
        """Mark a job as complete"""
        job_file = os.path.join(self.queue_dir, f"{job_id}.json")
        if os.path.exists(job_file):
            with open(job_file) as f:
                job = json.load(f)
            
            job['status'] = 'complete'
            job['completed_at'] = datetime.now().isoformat()
            job['result'] = result
            
            with open(job_file, 'w') as f:
                json.dump(job, f, indent=2)


class PromptRegistry:
    """
    Manages context prompts for the STEWARD agent.
    """
    
    def __init__(self, registry_path: str = None):
        if registry_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.registry_path = os.path.join(current_dir, 'prompts/registry.yaml')
        else:
            self.registry_path = registry_path
            
    def load(self) -> Dict:
        """Load the prompt registry"""
        with open(self.registry_path) as f:
            return yaml.safe_load(f)
    
    def get_prompt(self, prompt_id: str) -> Optional[str]:
        """Get a specific prompt by ID"""
        registry = self.load()
        for prompt in registry.get('prompts', []):
            if prompt['id'] == prompt_id:
                return prompt['context']
        return None
    
    def list_prompts(self) -> List[Dict]:
        """List all available prompts"""
        registry = self.load()
        return [
            {"id": p['id'], "name": p['name']}
            for p in registry.get('prompts', [])
        ]


# CLI for job management
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 queue.py [enqueue|list|prompts]")
        sys.exit(1)
    
    command = sys.argv[1]
    queue = JobQueue()
    registry = PromptRegistry()
    
    if command == "enqueue":
        # Example: python3 queue.py enqueue "theological_inquiry" "What is karma?"
        if len(sys.argv) < 4:
            print("Usage: python3 queue.py enqueue <prompt_id> <query>")
            sys.exit(1)
        
        prompt_id = sys.argv[2]
        query = sys.argv[3]
        
        job_id = queue.enqueue({
            "type": "query",
            "prompt_id": prompt_id,
            "query": query
        })
        print(f"✅ Job queued: {job_id}")
        
    elif command == "list":
        jobs = queue.get_pending()
        print(f"📋 Pending Jobs: {len(jobs)}")
        for job in jobs:
            print(f"  - {job['id']}: {job['task']}")
            
    elif command == "prompts":
        prompts = registry.list_prompts()
        print("📝 Available Prompts:")
        for p in prompts:
            print(f"  - {p['id']}: {p['name']}")
