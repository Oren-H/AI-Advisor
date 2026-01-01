import os
from typing import Dict, Optional
from pathlib import Path

class PromptManager:
    """Manages loading and caching of prompts from text files."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt text files
        """
        self.prompts_dir = Path(prompts_dir)
        self._prompt_cache: Dict[str, str] = {}
        
    def get_prompt(self, prompt_name: str) -> str:
        """
        Get a prompt by name, loading from file if not cached.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            
        Returns:
            The prompt text content
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        if prompt_name not in self._prompt_cache:
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self._prompt_cache[prompt_name] = f.read().strip()
        
        return self._prompt_cache[prompt_name]
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt and format it with the provided variables.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            **kwargs: Variables to format into the prompt
            
        Returns:
            The formatted prompt text
        """
        prompt_template = self.get_prompt(prompt_name)
        return prompt_template.format(**kwargs)
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._prompt_cache.clear()
    
    def list_available_prompts(self) -> list:
        """List all available prompt files."""
        if not self.prompts_dir.exists():
            return []
        
        return [f.stem for f in self.prompts_dir.glob("*.txt")]

# Global prompt manager instance with absolute path to agent/prompts directory
_agent_dir = Path(__file__).parent  # agent/
_prompts_dir = _agent_dir / "prompts"
prompt_manager = PromptManager(str(_prompts_dir))

if __name__ == "__main__":
    prompt_manager.clear_cache()