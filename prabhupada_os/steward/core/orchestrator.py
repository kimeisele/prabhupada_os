"""
Workflow Orchestrator - The Playbook Engine

This module implements multi-step workflow execution for complex tasks.
It addresses the "Playbook Gap" by enabling sequential, conditional workflows
rather than single-shot prompt execution.

A workflow (playbook) defines:
1. Sequential steps with specific modes/actions
2. Context passing between steps
3. Conditional branching logic
4. Validation checkpoints
"""

import os
import yaml
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Import other STEWARD components
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from prabhupada_os.steward import queue as job_queue_module
from prabhupada_os.steward.core.validator import SmritiValidator

PromptRegistry = job_queue_module.PromptRegistry


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    id: str
    mode: str
    action: str
    params: Dict = None
    input_source: str = None  # e.g., "previous.results"
    next_step: str = None
    condition: Dict = None
    validate: bool = False
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class Playbook:
    """A complete workflow definition"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    playbook_id: str
    success: bool
    steps_completed: int
    total_steps: int
    results: Dict
    execution_time: float
    errors: List[Dict] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class WorkflowOrchestrator:
    """
    Executes multi-step workflows defined in playbooks.
    
    This is the "Playbook Engine" that enables complex, sequential
    task execution with context passing and conditional logic.
    """
    
    def __init__(self, playbook_dir: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            playbook_dir: Directory containing playbook YAML files
        """
        if playbook_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            playbook_dir = os.path.join(
                os.path.dirname(current_dir),
                'playbooks'
            )
        
        self.playbook_dir = playbook_dir
        self.registry = PromptRegistry()
        self.validator = SmritiValidator()
        
        # Ensure playbook directory exists
        os.makedirs(self.playbook_dir, exist_ok=True)
    
    def load_playbook(self, playbook_id: str) -> Playbook:
        """
        Load a playbook from YAML file.
        
        Args:
            playbook_id: ID of the playbook to load
            
        Returns:
            Playbook object
        """
        playbook_path = os.path.join(self.playbook_dir, f"{playbook_id}.yaml")
        
        if not os.path.exists(playbook_path):
            raise FileNotFoundError(f"Playbook not found: {playbook_id}")
        
        with open(playbook_path) as f:
            data = yaml.safe_load(f)
        
        # Parse steps
        steps = []
        for step_data in data.get('steps', []):
            step = WorkflowStep(
                id=step_data['id'],
                mode=step_data['mode'],
                action=step_data['action'],
                params=step_data.get('params', {}),
                input_source=step_data.get('input'),
                next_step=step_data.get('next'),
                condition=step_data.get('condition'),
                validate=step_data.get('validate', False)
            )
            steps.append(step)
        
        return Playbook(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            steps=steps,
            metadata=data.get('metadata', {})
        )
    
    def execute_workflow(
        self, 
        playbook_id: str, 
        initial_query: str,
        context: Optional[Dict] = None
    ) -> WorkflowResult:
        """
        Execute a complete workflow.
        
        Args:
            playbook_id: ID of the playbook to execute
            initial_query: The initial query/input
            context: Optional additional context
            
        Returns:
            WorkflowResult with all step outputs
        """
        start_time = time.time()
        
        # Load playbook
        playbook = self.load_playbook(playbook_id)
        
        # Initialize workflow context
        workflow_context = {
            'query': initial_query,
            'playbook_id': playbook_id,
            'started_at': datetime.now().isoformat(),
            'user_context': context or {}
        }
        
        # Results storage
        step_results = {}
        errors = []
        current_step_id = playbook.steps[0].id if playbook.steps else None
        steps_completed = 0
        
        # Execute steps
        while current_step_id:
            step = self._find_step(playbook, current_step_id)
            if not step:
                errors.append({
                    'step': current_step_id,
                    'error': 'Step not found in playbook'
                })
                break
            
            try:
                # Execute step
                step_result = self.execute_step(
                    step, 
                    workflow_context,
                    step_results
                )
                
                step_results[step.id] = step_result
                steps_completed += 1
                
                # Determine next step
                current_step_id = self._determine_next_step(
                    step, 
                    step_result,
                    playbook
                )
                
            except Exception as e:
                errors.append({
                    'step': step.id,
                    'error': str(e)
                })
                break
        
        execution_time = time.time() - start_time
        
        return WorkflowResult(
            playbook_id=playbook_id,
            success=len(errors) == 0,
            steps_completed=steps_completed,
            total_steps=len(playbook.steps),
            results=step_results,
            execution_time=execution_time,
            errors=errors
        )
    
    def execute_step(
        self,
        step: WorkflowStep,
        workflow_context: Dict,
        previous_results: Dict
    ) -> Dict:
        """
        Execute a single workflow step.
        
        Args:
            step: The step to execute
            workflow_context: Overall workflow context
            previous_results: Results from previous steps
            
        Returns:
            Dict with step execution results
        """
        # Get input for this step
        step_input = self._get_step_input(
            step,
            workflow_context,
            previous_results
        )
        
        # Load prompt context for this step's mode
        prompt_context = self.registry.get_prompt(step.mode)
        
        # Execute action based on type
        if step.action == 'semantic_search':
            result = self._execute_search(step_input, step.params, semantic=True)
        elif step.action == 'keyword_search':
            result = self._execute_search(step_input, step.params, semantic=False)
        elif step.action == 'extract_relationships':
            result = self._extract_relationships(step_input, previous_results)
        elif step.action == 'find_conflicts':
            result = self._find_conflicts(step_input, previous_results)
        elif step.action == 'synthesize':
            result = self._synthesize(step_input, previous_results, prompt_context)
        else:
            result = {'error': f'Unknown action: {step.action}'}
        
        # Validate if required
        if step.validate and 'smriti' in result and 'sruti' in result:
            validation = self.validator.validate_synthesis(
                result['smriti'],
                result['sruti']
            )
            result['validation'] = {
                'passed': validation.passed,
                'score': validation.score,
                'failures': validation.failures
            }
        
        result['step_id'] = step.id
        result['mode'] = step.mode
        result['action'] = step.action
        
        return result
    
    def _get_step_input(
        self,
        step: WorkflowStep,
        workflow_context: Dict,
        previous_results: Dict
    ) -> Any:
        """Extract input for a step from context or previous results"""
        if not step.input_source:
            # Use original query
            return workflow_context['query']
        
        # Parse input source (e.g., "previous.results", "context.user_input")
        parts = step.input_source.split('.')
        
        if parts[0] == 'previous':
            # Get from previous step
            if len(previous_results) == 0:
                return workflow_context['query']
            
            last_result = list(previous_results.values())[-1]
            
            if len(parts) > 1:
                return last_result.get(parts[1], last_result)
            return last_result
        
        elif parts[0] == 'context':
            if len(parts) > 1:
                return workflow_context.get(parts[1])
            return workflow_context
        
        return workflow_context['query']
    
    def _determine_next_step(
        self,
        current_step: WorkflowStep,
        step_result: Dict,
        playbook: Playbook
    ) -> Optional[str]:
        """Determine the next step based on conditions"""
        
        # Check for conditional branching
        if current_step.condition:
            condition_field = current_step.condition.get('if')
            then_step = current_step.condition.get('then')
            else_step = current_step.condition.get('else')
            
            # Evaluate condition
            if self._evaluate_condition(condition_field, step_result):
                return then_step
            else:
                return else_step
        
        # No condition, use next_step
        return current_step.next_step
    
    def _evaluate_condition(self, condition: str, result: Dict) -> bool:
        """Evaluate a condition against step result"""
        # Simple condition evaluation
        if condition == 'contradictions_found':
            return len(result.get('contradictions', [])) > 0
        elif condition == 'validation_passed':
            return result.get('validation', {}).get('passed', False)
        elif condition == 'results_found':
            return len(result.get('results', [])) > 0
        
        return False
    
    def _find_step(self, playbook: Playbook, step_id: str) -> Optional[WorkflowStep]:
        """Find a step by ID in the playbook"""
        for step in playbook.steps:
            if step.id == step_id:
                return step
        return None
    
    def _execute_search(self, query: str, params: Dict, semantic: bool) -> Dict:
        """Execute a search (placeholder - would call actual CLI)"""
        # This would actually call the CLI or core search
        return {
            'query': query,
            'mode': 'semantic' if semantic else 'keyword',
            'results': [],
            'note': 'Placeholder - integrate with actual search'
        }
    
    def _extract_relationships(self, input_data: Any, previous_results: Dict) -> Dict:
        """Extract entities and relationships (placeholder)"""
        return {
            'entities': [],
            'relationships': [],
            'note': 'Placeholder - implement concept mapping'
        }
    
    def _find_conflicts(self, input_data: Any, previous_results: Dict) -> Dict:
        """Find contradictions (placeholder)"""
        return {
            'contradictions': [],
            'note': 'Placeholder - implement contradiction detection'
        }
    
    def _synthesize(self, input_data: Any, previous_results: Dict, context: str) -> Dict:
        """Synthesize final answer (placeholder)"""
        return {
            'smriti': 'Placeholder synthesis',
            'sruti': [],
            'note': 'Placeholder - implement synthesis with LLM'
        }


# CLI for testing orchestrator
if __name__ == "__main__":
    orchestrator = WorkflowOrchestrator()
    
    print("🎭 Workflow Orchestrator Test")
    print("=" * 60)
    
    # List available playbooks
    playbook_dir = orchestrator.playbook_dir
    print(f"\nPlaybook directory: {playbook_dir}")
    
    if os.path.exists(playbook_dir):
        playbooks = [f.replace('.yaml', '') for f in os.listdir(playbook_dir) if f.endswith('.yaml')]
        print(f"Available playbooks: {playbooks}")
    else:
        print("No playbooks directory found. Creating...")
        os.makedirs(playbook_dir, exist_ok=True)
        print("✅ Playbooks directory created")
