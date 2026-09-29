"""Reliable Gemini client for the optional semantic layer.

Uses Google's current Interactions API first, with a GenerateContent fallback.
Transient errors are retried; unavailable model aliases can fall back to a
nearby supported Flash model. AI is enrichment only and never blocks auditing.
"""
import json, os, random, time, urllib.error, urllib.request

DEFAULT_MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = ["gemini-3.7-flash", "gemini-3.5-flash"]
MAX_RETRIES = max(0, int(os.getenv("GEMINI_MAX_RETRIES", "0")))
REQUEST_TIMEOUT_SEC = max(5, int(os.getenv("GEMINI_TIMEOUT_SEC", "8")))

class GeminiClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        requested = str(model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)).strip().removeprefix("models/")
        self.model = requested or DEFAULT_MODEL
        configured = [self.model]
        if os.getenv("GEMINI_ALLOW_MODEL_FALLBACK", "1") != "0":
            configured += [m for m in FALLBACK_MODELS if m not in configured]
        self.models = configured
        self.last_model = self.model

    def _post(self, url, payload, headers_extra=None):
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        if headers_extra: headers.update(headers_extra)
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    @staticmethod
    def _retryable(code, text):
        return code in (408, 429, 500, 502, 503, 504) or any(x in text.upper() for x in ("RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED", "TIMEOUT"))

    def _call_interactions(self, model, system_instruction, user_content, max_output_tokens):
        url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        payload = {
            "model": model,
            "input": user_content,
            "system_instruction": system_instruction,
            "generation_config": {"max_output_tokens": max_output_tokens},
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": {
                    "type": "object",
                    "properties": {
                        "vendor": {"type": "string"},
                        "device_type": {"type": "string"},
                        "os": {"type": "string"},
                        "confidence": {"type": "number"},
                        "mappings": {"type": "array", "items": {"type": "object"}}
                    },
                    "required": ["vendor", "device_type", "os", "confidence", "mappings"]
                }
            }
        }
        data = self._post(url, payload)
        if data.get("status") in ("failed", "cancelled"):
            raise RuntimeError(json.dumps(data)[:1200])
        # Current Interactions responses expose output_text in SDKs and steps in REST.
        if data.get("output_text"):
            return data["output_text"]
        for step in reversed(data.get("steps", [])):
            if isinstance(step, dict):
                for key in ("text", "output_text"):
                    if step.get(key): return str(step[key])
                content = step.get("content") or {}
                for part in content.get("parts", []) if isinstance(content, dict) else []:
                    if isinstance(part, dict) and part.get("text"): return str(part["text"])
        raise RuntimeError(f"Gemini interaction returned no text: {json.dumps(data)[:1000]}")

    def _call_generate_content(self, model, system_instruction, user_content, max_output_tokens):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "generationConfig": {"maxOutputTokens": max_output_tokens, "thinkingConfig": {"thinkingLevel": "low"}},
        }
        data = self._post(url, payload)
        candidates = data.get("candidates") or []
        if not candidates: raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:900]}")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(str(p.get("text", "")) for p in parts if isinstance(p, dict))
        if not text.strip(): raise RuntimeError(f"Gemini returned empty response: {json.dumps(data)[:900]}")
        return text

    def generate_json_free(self, system_instruction, user_content, max_output_tokens=1200):
        """Generate JSON without the semantic-layer schema, for modular AI tasks."""
        errors=[]
        for model in self.models:
            for method in ("interactions_free", "generate_content_free"):
                for attempt in range(MAX_RETRIES + 1):
                    try:
                        if method == "interactions_free":
                            url="https://generativelanguage.googleapis.com/v1beta/interactions"
                            payload={"model":model,"input":user_content,"system_instruction":system_instruction,"generation_config":{"max_output_tokens":max_output_tokens},"response_format":{"type":"text","mime_type":"application/json"}}
                            data=self._post(url,payload); text=data.get("output_text") or ""
                            if not text:
                                for step in reversed(data.get("steps",[])):
                                    if isinstance(step,dict) and step.get("text"): text=str(step["text"]); break
                        else:
                            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                            payload={"systemInstruction":{"parts":[{"text":system_instruction}]},"contents":[{"role":"user","parts":[{"text":user_content}]}],"generationConfig":{"maxOutputTokens":max_output_tokens,"responseMimeType":"application/json","thinkingConfig":{"thinkingLevel":"low"}}}
                            data=self._post(url,payload); candidates=data.get("candidates") or []; parts=candidates[0].get("content",{}).get("parts",[]) if candidates else []; text="".join(str(x.get("text","")) for x in parts if isinstance(x,dict))
                        if text.strip(): self.last_model=model; return text
                        raise RuntimeError("Gemini returned empty JSON response")
                    except urllib.error.HTTPError as exc:
                        body=exc.read().decode("utf-8",errors="replace"); errors.append(f"{method} {model}: HTTP {exc.code}: {body[:500]}")
                        if self._retryable(exc.code,body) and attempt<MAX_RETRIES: time.sleep(min(10,.8*(2**attempt))+random.uniform(0,.3)); continue
                        break
                    except (urllib.error.URLError,TimeoutError) as exc:
                        errors.append(str(exc))
                        if attempt<MAX_RETRIES: time.sleep(min(10,.8*(2**attempt))+random.uniform(0,.3)); continue
                        break
                    except Exception as exc: errors.append(str(exc)); break
        raise RuntimeError("Gemini unavailable after retries. "+" | ".join(errors[-4:]))

    def generate_json(self, system_instruction, user_content, max_output_tokens=1200):
        errors=[]
        for model in self.models:
            for method in ("interactions", "generate_content"):
                for attempt in range(MAX_RETRIES + 1):
                    try:
                        if method == "interactions":
                            text = self._call_interactions(model, system_instruction, user_content, max_output_tokens)
                        else:
                            text = self._call_generate_content(model, system_instruction, user_content, max_output_tokens)
                        self.last_model = model
                        return text
                    except urllib.error.HTTPError as exc:
                        body = exc.read().decode("utf-8", errors="replace")
                        msg=f"{method} {model}: HTTP {exc.code}: {body[:700]}"; errors.append(msg)
                        if self._retryable(exc.code, body) and attempt < MAX_RETRIES:
                            time.sleep(min(10, 0.8*(2**attempt))+random.uniform(0,.3)); continue
                        break
                    except (urllib.error.URLError, TimeoutError) as exc:
                        errors.append(f"{method} {model}: network/timeout: {exc}")
                        if attempt < MAX_RETRIES:
                            time.sleep(min(10, 0.8*(2**attempt))+random.uniform(0,.3)); continue
                        break
                    except Exception as exc:
                        errors.append(f"{method} {model}: {exc}")
                        break
        raise RuntimeError("Gemini unavailable after retries. " + " | ".join(errors[-4:]))
