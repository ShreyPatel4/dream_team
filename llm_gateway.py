import os
import yaml
import json
import time
import urllib.request
from google import genai
from google.genai import types
import anthropic

try:
    from telemetry_writer import telemetry as _tel
except ImportError:
    class _Noop:
        def emit(self, *a, **kw): pass
    _tel = _Noop()

class LLMGateway:
    """Multi-provider router that abstracts API vs Local inference based on coconutos.yml."""
    
    def __init__(self, config_path: str, gemini_key: str, anthropic_key: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f).get('inference', {})
            
        self.mode = self.config.get('mode', 'api')
        self.api_config = self.config.get('api', {})
        self.local_config = self.config.get('local', {})
        
        self.gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None
        
    def _get_api_model_for_role(self, agent_id: str) -> str:
        if agent_id == "08":
            return self.api_config.get("default_orchestration", "gemini-3.1-pro")
        elif agent_id in ["10", "10w", "05", "04", "06"]: # Leads / QA
            return self.api_config.get("default_review", "claude-4.6-opus")
        else:
            return self.api_config.get("default_code", "claude-4.6-opus")

    def _get_local_model_for_role(self, agent_id: str) -> str:
        if agent_id == "08":
            return self.local_config.get("orchestration_model", "qwen2.5:7b-instruct-q4_K_M")
        elif agent_id in ["10", "10w", "05", "04", "06"]:
            return self.local_config.get("review_model", "qwen2.5:7b-instruct-q4_K_M")
        else:
            return self.local_config.get("code_model", "deepseek-coder-v2:6.7b-instruct-q4_K_M")

    def generate(self, agent_id: str, system_instruction: str, prompt_context: str,
                 project_id: str = None, trace_id: str = None) -> tuple[str, str]:
        """Returns (response_text, model_used). Emits telemetry events."""
        
        if self.mode == "local" or (self.mode == "hybrid" and agent_id == "08"):
            target_model = self._get_local_model_for_role(agent_id)
            provider = "ollama"
        else:
            target_model = self._get_api_model_for_role(agent_id)
            provider = "gemini" if "gemini" in target_model.lower() else "anthropic"

        # ── TELEMETRY: before call ──
        _tel.emit("llm_call_start", project_id, agent_id, trace_id=trace_id,
                  data={"model": target_model, "provider": provider})

        t0 = time.time()
        try:
            if provider == "ollama":
                text = self._call_ollama(target_model, system_instruction, prompt_context)
                latency_ms = int((time.time() - t0) * 1000)
                _tel.emit("llm_call_complete", project_id, agent_id, trace_id=trace_id,
                          data={"model": target_model, "provider": provider,
                                "input_tokens": 0, "output_tokens": 0,
                                "cost_usd": 0.0, "latency_ms": latency_ms})
                return text, target_model

            elif provider == "gemini":
                response = self.gemini_client.models.generate_content(
                    model=target_model,
                    contents=prompt_context,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2
                    )
                )
                latency_ms = int((time.time() - t0) * 1000)
                in_tok = getattr(getattr(response, 'usage_metadata', None), 'prompt_token_count', 0) or 0
                out_tok = getattr(getattr(response, 'usage_metadata', None), 'candidates_token_count', 0) or 0
                cost = (in_tok * 0.00000125) + (out_tok * 0.000005)  # Gemini Pro pricing
                _tel.emit("llm_call_complete", project_id, agent_id, trace_id=trace_id,
                          data={"model": target_model, "provider": provider,
                                "input_tokens": in_tok, "output_tokens": out_tok,
                                "cost_usd": round(cost, 6), "latency_ms": latency_ms})
                return response.text, target_model

            elif provider == "anthropic":
                response = self.anthropic_client.messages.create(
                    model=target_model,
                    max_tokens=4096,
                    temperature=0.2,
                    system=system_instruction,
                    messages=[{"role": "user", "content": prompt_context}]
                )
                latency_ms = int((time.time() - t0) * 1000)
                in_tok = getattr(response.usage, 'input_tokens', 0)
                out_tok = getattr(response.usage, 'output_tokens', 0)
                cost = (in_tok * 0.000015) + (out_tok * 0.000075)  # Claude Opus pricing
                _tel.emit("llm_call_complete", project_id, agent_id, trace_id=trace_id,
                          data={"model": target_model, "provider": provider,
                                "input_tokens": in_tok, "output_tokens": out_tok,
                                "cost_usd": round(cost, 6), "latency_ms": latency_ms})
                return response.content[0].text, target_model

            else:
                raise ValueError(f"Unsupported API model requested: {target_model}")

        except Exception as e:
            # ── TELEMETRY: failure ──
            _tel.emit("llm_call_failed", project_id, agent_id, trace_id=trace_id,
                      data={"model": target_model, "provider": provider, "error": str(e)})
            raise

    def _call_ollama(self, model: str, system: str, prompt: str) -> str:
        host = self.local_config.get("ollama_host", "http://localhost:11434")
        url = f"{host}/api/generate"
        
        payload = {
            "model": model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": self.local_config.get("context_window", 8192)
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
        except Exception as e:
            print(f"[Ollama Error]: Make sure Ollama is running and has model '{model}'. {e}")
            return f"Error executing local model: {e}"
