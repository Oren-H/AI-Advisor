import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_cerebras import ChatCerebras

load_dotenv()

class LLMManager:
    """Manages shared LLM instances to avoid redundant initializations."""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
        if not self.openai_api_key or not self.cerebras_api_key:
            raise ValueError("api key environment variable is required")
        
        # Cache for LLM instances
        self._llm_cache = {}
    
    def get_llm(self, 
                model_provider: str,
                model: str = "o4-mini", 
                temperature: float = 0.7,
                use_structured_output: bool = False,
                structured_output_class: Optional[type] = None):
        """
        Get a shared LLM instance with the specified configuration.
        
        Args:
            model_provider: The provider to use ("openai" or "cerebras")
            model: The model to use (default: o4-mini)
            temperature: The temperature setting (default: 0.7)
            use_structured_output: Whether to use structured output (default: False, OpenAI only)
            structured_output_class: The class to use for structured output (required if use_structured_output=True)
        
        Returns:
            A configured ChatOpenAI or ChatCerebras instance
        """
        if model_provider not in ["openai", "cerebras"]:
            raise ValueError("model_provider must be either 'openai' or 'cerebras'")
        
        # Create a cache key based on configuration
        cache_key = f"{model_provider}_{model}_{temperature}_{use_structured_output}_{structured_output_class.__name__ if structured_output_class else 'None'}"
        
        if cache_key not in self._llm_cache:
            if model_provider == "openai":
                llm = ChatOpenAI(
                    model=model,
                    api_key=self.openai_api_key,
                    temperature=temperature
                )
                
                if use_structured_output and structured_output_class:
                    llm = llm.with_structured_output(structured_output_class, method="function_calling")
                    
            elif model_provider == "cerebras":
                if use_structured_output:
                    raise ValueError("Structured output is not supported for Cerebras models")
                llm = ChatCerebras(
                    model=model,
                    api_key=self.cerebras_api_key,
                    temperature=temperature
                )
            
            self._llm_cache[cache_key] = llm
        
        return self._llm_cache[cache_key]

    def clear_cache(self):
        """
        Clear all cached LLM instances.
        
        This is useful for:
        - Debugging configuration issues
        - Memory management in long-running applications
        - Forcing recreation of LLM instances after configuration changes
        """
        self._llm_cache.clear()
        print(f"✅ LLM cache cleared. All cached instances have been removed.")

    def get_cache_info(self):
        """
        Get information about the current cache state.
        
        Returns:
            dict: Cache statistics including number of cached instances and their keys
        """
        cache_keys = list(self._llm_cache.keys())
        return {
            "cached_instances": len(cache_keys),
            "cache_keys": cache_keys
        }


# Global instance
llm_manager = LLMManager()

if __name__ == "__main__":
    llm_manager.clear_cache()