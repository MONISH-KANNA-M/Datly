import os
import logging
import requests
import contextvars
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Thread-safe/Async-safe context variable to manage active model backend selection
active_provider_var = contextvars.ContextVar("active_provider", default="ollama")

class LLMServiceException(Exception):
    """Custom exception class for Ollama/Groq communication failures."""
    pass

def generate_completion(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    """
    Sends chat prompt containing system and user messages to the configured Ollama or Groq API endpoint
    depending on the active provider context variable.
    
    Returns:
        The response content string.
    
    Raises:
        LLMServiceException if connection fails.
    """
    provider = active_provider_var.get()
    
    if provider == "groq":
        # --- GROQ API Execution ---
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise LLMServiceException("GROQ_API_KEY is missing. Please add it to your backend '.env' file.")
            
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Using Llama 3.1 8b instant model for fast SQL outputs
        model = "llama-3.1-8b-instant"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "stream": False
        }
        
        logger.info(f"Invoking Groq API model '{model}'")
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            
            message_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not message_content:
                raise LLMServiceException("Received empty message choices from Groq completions.")
                
            return message_content
        except Exception as e:
            logger.error(f"Groq API invocation failed: {str(e)}")
            raise LLMServiceException(f"Failed to query Groq model: {str(e)}")
            
    else:
        # --- OLLAMA Local Execution (Default) ---
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip('/')
        model = os.getenv("OLLAMA_MODEL", "llama3.1").strip()
        endpoint = f"{base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "options": {
                "temperature": temperature,
                "seed": 42
            },
            "stream": False
        }
        
        logger.info(f"Invoking Ollama model '{model}' at '{endpoint}'")
        try:
            response = requests.post(endpoint, json=payload, timeout=180)
            
            if response.status_code == 404:
                raise LLMServiceException(
                    f"Ollama returned 404. Model '{model}' might not be installed. "
                    f"Please run 'ollama pull {model}' first."
                )
                
            response.raise_for_status()
            response_data = response.json()
            
            message_content = response_data.get("message", {}).get("content", "").strip()
            if not message_content:
                raise LLMServiceException("Received empty response content from Ollama model.")
                
            return message_content
            
        except requests.exceptions.ConnectionError:
            error_msg = (
                f"Could not connect to Ollama at '{base_url}'. "
                f"Please ensure the Ollama service is running locally on your machine. "
                f"To install or run, visit: https://ollama.com"
            )
            logger.error(error_msg)
            raise LLMServiceException(error_msg)
            
        except requests.exceptions.Timeout:
            error_msg = f"Ollama model query timed out after 180 seconds."
            logger.error(error_msg)
            raise LLMServiceException(error_msg)
            
        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise e
            error_msg = f"An unexpected error occurred during LLM communication: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceException(error_msg)
