"""Optional live Gemini connectivity check.
Run with GEMINI_API_KEY set. It is skipped by pytest when no key is configured.
"""
import os
import pytest

if not os.getenv("GEMINI_API_KEY"):
    pytest.skip("GEMINI_API_KEY not set; skipping live Gemini test.", allow_module_level=True)

from gemini_client import GeminiClient


def test_gemini_live():
    client = GeminiClient()
    text = client.generate_json(
        "Return JSON only.",
        '{"task":"reply with {\\"ok\\":true}"}',
        max_output_tokens=100,
    )
    assert text.strip()
    print(client.model)
    print(text)


if __name__ == "__main__":
    client = GeminiClient()
    print(client.model)
    print(client.generate_json("Return JSON only.", '{"task":"reply with {\\"ok\\":true}"}', 100))
