"""
STEWARD Agent - The Autonomous AI Operator

This is the main agent loop that integrates all STEWARD components:
- Job Queue for task management
- Prompt Registry for context injection
- Workflow Orchestrator for complex multi-step tasks
- Smriti Validator for accuracy checking
- Recovery Strategies for error handling

The STEWARD is not a chatbot - it's an autonomous operator that:
1. Polls the job queue continuously
2. Executes tasks with appropriate context
3. Validates all synthesis against source verses
4. Recovers from errors intelligently
5. Logs all queries for research

Usage:
    python3 prabhupada_os/steward/agent.py
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from prabhupada_os.steward import queue as job_queue_module
from prabhupada_os.steward.core.orchestrator import WorkflowOrchestrator
from prabhupada_os.steward.core.validator import SmritiValidator
from prabhupada_os.steward.core.recovery import RecoveryStrategies, RecoveryActionType
from prabhupada_os.steward.logger import QueryLogger

JobQueue = job_queue_module.JobQueue
PromptRegistry = job_queue_module.PromptRegistry


class StewardAgent:
    """
    Autonomous AI Operator for PrabhupadaOS.
    
    Processes jobs with:
    - Workflow orchestration
    - Validation
    - Error recovery
    - Query logging
    """
    
    def __init__(self, poll_interval: int = 5):
        """
        Initialize the STEWARD agent.
        
        Args:
            poll_interval: Seconds between queue polls
        """
        self.poll_interval = poll_interval
        
        # Initialize all components
        self.queue = JobQueue()
        self.registry = PromptRegistry()
        self.orchestrator = WorkflowOrchestrator()
        self.validator = SmritiValidator()
        self.recovery = RecoveryStrategies(max_retries=3)
        self.logger = QueryLogger()
        
        # Agent state
        self.running = False
        self.stats = {
            'jobs_processed': 0,
            'jobs_failed': 0,
            'validations_passed': 0,
            'validations_failed': 0,
            'recoveries_attempted': 0,
            'started_at': None
        }
    
    def run(self):
        """Main agent loop - runs continuously"""
        self.running = True
        self.stats['started_at'] = datetime.now().isoformat()
        
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              STEWARD AGENT - AUTONOMOUS MODE                  ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print("🤖 STEWARD Agent Online")
        print(f"📋 Poll Interval: {self.poll_interval}s")
        print(f"🔍 Validator: Active")
        print(f"🎭 Orchestrator: Active")
        print(f"🔧 Recovery: Active (max {self.recovery.max_retries} retries)")
        print()
        print("Awaiting Director's intent...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while self.running:
                self._process_queue()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 STEWARD Agent shutting down...")
            self._print_stats()
            print("✅ Shutdown complete")
    
    def _process_queue(self):
        """Process all pending jobs in the queue"""
        jobs = self.queue.get_pending()
        
        if not jobs:
            return  # Nothing to do
        
        print(f"\n📋 Processing {len(jobs)} pending job(s)...")
        
        for job in jobs:
            try:
                print(f"\n🔄 Job {job['id']}")
                print(f"   Type: {job['task'].get('type', 'unknown')}")
                print(f"   Query: {job['task'].get('query', 'N/A')}")
                
                result = self.process_job(job)
                
                self.queue.mark_complete(job['id'], result)
                self.stats['jobs_processed'] += 1
                
                print(f"   ✅ Complete")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
                self._handle_job_failure(job, e)
                self.stats['jobs_failed'] += 1
    
    def process_job(self, job: Dict) -> Dict:
        """
        Process a single job with full workflow.
        
        This is the core processing logic that:
        1. Determines execution mode (playbook vs simple)
        2. Executes with appropriate context
        3. Validates synthesis
        4. Handles failures with recovery
        5. Logs the query
        
        Args:
            job: Job data from queue
            
        Returns:
            Dict with results
        """
        job_id = job['id']
        task = job['task']
        
        # Determine execution mode
        if task.get('playbook_id'):
            # Complex workflow execution
            result = self._execute_playbook(job_id, task)
        else:
            # Simple prompt-based execution
            result = self._execute_simple(job_id, task)
        
        # Validate synthesis if present
        if 'smriti' in result and 'sruti' in result:
            validation = self.validator.validate_synthesis(
                result['smriti'],
                result['sruti']
            )
            
            result['validation'] = {
                'passed': validation.passed,
                'score': validation.score,
                'failures': validation.failures,
                'warnings': validation.warnings
            }
            
            if validation.passed:
                self.stats['validations_passed'] += 1
                print(f"   ✅ Validation passed (score: {validation.score:.2f})")
            else:
                self.stats['validations_failed'] += 1
                print(f"   ⚠️  Validation failed (score: {validation.score:.2f})")
                
                # Handle validation failure
                recovery_action = self.recovery.handle_validation_failure(
                    validation,
                    job_id
                )
                
                if recovery_action.type == RecoveryActionType.RETRY:
                    print(f"   🔄 Retrying with stricter validation...")
                    self.stats['recoveries_attempted'] += 1
                    # Recursive retry
                    return self.process_job(job)
                elif recovery_action.type == RecoveryActionType.ESCALATE:
                    print(f"   🚨 Escalating to Director for review")
                    result['requires_review'] = True
        
        # Log the query
        self.logger.log_query(
            query=task.get('query', ''),
            mode=task.get('prompt_id', 'unknown'),
            results=result,
            metadata={'job_id': job_id}
        )
        
        return result
    
    def _execute_playbook(self, job_id: str, task: Dict) -> Dict:
        """Execute a playbook-based workflow"""
        print(f"   🎭 Executing playbook: {task['playbook_id']}")
        
        try:
            workflow_result = self.orchestrator.execute_workflow(
                task['playbook_id'],
                task['query']
            )
            
            return {
                'type': 'playbook',
                'playbook_id': task['playbook_id'],
                'success': workflow_result.success,
                'steps_completed': workflow_result.steps_completed,
                'results': workflow_result.results,
                'execution_time': workflow_result.execution_time
            }
            
        except FileNotFoundError:
            print(f"   ⚠️  Playbook not found, falling back to simple execution")
            return self._execute_simple(job_id, task)
    
    def _execute_simple(self, job_id: str, task: Dict) -> Dict:
        """Execute a simple prompt-based query"""
        prompt_id = task.get('prompt_id', 'theological_inquiry')
        query = task.get('query', '')
        
        print(f"   📝 Executing with prompt: {prompt_id}")
        
        # Get prompt context
        context = self.registry.get_prompt(prompt_id)
        
        # This is a placeholder - in real implementation, this would:
        # 1. Call the CLI search
        # 2. Use an LLM to synthesize with the prompt context
        # 3. Return structured results
        
        return {
            'type': 'simple',
            'prompt_id': prompt_id,
            'query': query,
            'context': context,
            'smriti': 'Placeholder synthesis',
            'sruti': [],
            'note': 'Placeholder - integrate with actual search and LLM'
        }
    
    def _handle_job_failure(self, job: Dict, error: Exception):
        """Handle job processing failure"""
        job_id = job['id']
        
        # Determine recovery action
        recovery_action = self.recovery.handle_system_error(
            error,
            job_id,
            context={'job': job}
        )
        
        if recovery_action.type == RecoveryActionType.RETRY:
            wait_seconds = recovery_action.params.get('wait_seconds', 0)
            print(f"   🔄 Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            
            # Re-queue the job
            # (In real implementation, would modify the job and re-enqueue)
            
        elif recovery_action.type == RecoveryActionType.ESCALATE:
            print(f"   🚨 Critical failure - logging for Director review")
            
            # Mark job as failed with error details
            self.queue.mark_complete(job_id, {
                'success': False,
                'error': str(error),
                'recovery_action': recovery_action.strategy,
                'requires_review': True
            })
    
    def _print_stats(self):
        """Print agent statistics"""
        print("\n" + "=" * 60)
        print("📊 STEWARD Agent Statistics")
        print("=" * 60)
        print(f"Jobs Processed:       {self.stats['jobs_processed']}")
        print(f"Jobs Failed:          {self.stats['jobs_failed']}")
        print(f"Validations Passed:   {self.stats['validations_passed']}")
        print(f"Validations Failed:   {self.stats['validations_failed']}")
        print(f"Recoveries Attempted: {self.stats['recoveries_attempted']}")
        print(f"Started At:           {self.stats['started_at']}")
        print("=" * 60)


# Main entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="STEWARD Autonomous Agent")
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=5,
        help='Seconds between queue polls (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = StewardAgent(poll_interval=args.poll_interval)
    agent.run()
