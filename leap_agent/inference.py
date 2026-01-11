"""Ollama Inference Wrapper for LEAP Agent.

Handles model loading/unloading for sequential orchestration.
On 4GB VRAM, we can only have one model loaded at a time.
"""
import ollama
import time
from typing import Optional, Generator
from dataclasses import dataclass
from .config import LEAPConfig


@dataclass
class InferenceMetrics:
    """Track inference performance."""
    load_time: float = 0.0
    inference_time: float = 0.0
    tokens_generated: int = 0
    tokens_per_second: float = 0.0


class OllamaInference:
    """Ollama inference wrapper with model management."""
    
    def __init__(self, config: LEAPConfig):
        self.config = config
        self.current_model: Optional[str] = None
        self.metrics = InferenceMetrics()
        
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """Generate response from a model.
        In sequential mode, this will unload previous model before loading new one.
        """
        start = time.time()
        
        # Track if model changed
        model_changed = model != self.current_model
        if model_changed and self.config.verbose:
            print(f" Loading model: {model}")
        
        try:
            if stream:
                return self._stream_generate(model, prompt, temperature, max_tokens)
            else:
                response = ollama.generate(
                    model=model,
                    prompt=prompt,
                    options={
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                )
                
                self.current_model = model
                self.metrics.inference_time = time.time() - start
                self.metrics.tokens_generated = response.get('eval_count', 0)
                
                if self.metrics.inference_time > 0:
                    self.metrics.tokens_per_second = (
                        self.metrics.tokens_generated / self.metrics.inference_time
                    )
                
                return response['response']
                
        except Exception as e:
            raise RuntimeError(f"Ollama inference failed: {e}")
    
    def _stream_generate(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Generator[str, None, None]:
        """Stream generation for real-time output."""
        start = time.time()
        total_tokens = 0
        
        for chunk in ollama.generate(
            model=model,
            prompt=prompt,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            stream=True
        ):
            if 'response' in chunk:
                total_tokens += 1
                yield chunk['response']
        
        self.current_model = model
        self.metrics.inference_time = time.time() - start
        self.metrics.tokens_generated = total_tokens
        if self.metrics.inference_time > 0:
            self.metrics.tokens_per_second = total_tokens / self.metrics.inference_time
    
    def warmup(self):
        """Pre-load models into Ollama's cache."""
        if not self.config.warmup_models:
            return
            
        print(" Warming up models...")
        
        # Quick generation to load models
        start = time.time()
        ollama.generate(
            model=self.config.main_model,
            prompt="Hello",
            options={"num_predict": 1}
        )
        main_time = time.time() - start
        
        start = time.time()
        ollama.generate(
            model=self.config.sub_model,
            prompt="Hello",
            options={"num_predict": 1}
        )
        sub_time = time.time() - start
        
        print(f" Models ready: {self.config.main_model}({main_time:.1f}s), "
              f"{self.config.sub_model}({sub_time:.1f}s)")
    
    def get_metrics(self) -> dict:
        """Get last inference metrics."""
        return {
            "load_time": self.metrics.load_time,
            "inference_time": self.metrics.inference_time,
            "tokens": self.metrics.tokens_generated,
            "tok/s": round(self.metrics.tokens_per_second, 1),
        }

def test_ollama_connection() -> bool:
    """Test if Ollama is running."""
    try:
        ollama.list()
        return True
    except Exception:
        return False


def list_available_models() -> list[str]:
    """List models available in Ollama."""
    try:
        models = ollama.list()
        return [m['name'] for m in models.get('models', [])]
    except Exception:
        return []
