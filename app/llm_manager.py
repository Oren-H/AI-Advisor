import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class LLMManager:
    """Manages shared LLM instances to avoid redundant initializations."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Cache for LLM instances
        self._llm_cache = {}
    
    def get_llm(self, 
                model: str = "gpt-4o-mini", 
                temperature: float = 0.7,
                use_structured_output: bool = False,
                structured_output_class: Optional[type] = None) -> ChatOpenAI:
        """
        Get a shared LLM instance with the specified configuration.
        
        Args:
            model: The model to use (default: gpt-4o-mini)
            temperature: The temperature setting (default: 0.7)
            use_structured_output: Whether to use structured output (default: False)
            structured_output_class: The class to use for structured output (required if use_structured_output=True)
        
        Returns:
            A configured ChatOpenAI instance
        """
        # Create a cache key based on configuration
        cache_key = f"{model}_{temperature}_{use_structured_output}_{structured_output_class.__name__ if structured_output_class else 'None'}"
        
        if cache_key not in self._llm_cache:
            llm = ChatOpenAI(
                model=model,
                api_key=self.api_key,
                temperature=temperature
            )
            
            if use_structured_output and structured_output_class:
                llm = llm.with_structured_output(structured_output_class, method="function_calling")
            
            self._llm_cache[cache_key] = llm
        
        return self._llm_cache[cache_key]
    
    def get_intent_classification_llm(self) -> ChatOpenAI:
        """Get LLM optimized for intent classification (low temperature for consistency)."""
        return self.get_llm(model="gpt-4o-mini", temperature=0.1)
    
    def get_advisory_llm(self) -> ChatOpenAI:
        """Get LLM optimized for advisory responses (higher temperature for creativity)."""
        return self.get_llm(model="gpt-4o-mini", temperature=0.7)
    
    def get_response_llm(self) -> ChatOpenAI:
        """Get LLM optimized for general responses."""
        return self.get_llm(model="gpt-4o-mini", temperature=0.7)
    
    def get_memory_llm(self) -> ChatOpenAI:
        """Get LLM optimized for memory/profile extraction (low temperature for accuracy)."""
        return self.get_llm(model="gpt-4o-mini", temperature=0.1)
    
    def get_structured_llm(self, output_class: type) -> ChatOpenAI:
        """Get LLM with structured output for filter generation."""
        return self.get_llm(
            model="gpt-4o-mini", 
            temperature=0, 
            use_structured_output=True,
            structured_output_class=output_class
        )
    
    def get_mapping_llm(self) -> ChatOpenAI:
        """Get LLM optimized for department mapping."""
        return self.get_llm(model="gpt-4", temperature=0)

# Global instance
llm_manager = LLMManager() 