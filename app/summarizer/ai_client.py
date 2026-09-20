import requests
import google.generativeai as genai
from openai import OpenAI

class AISummarizer:
    def __init__(self, provider: str, api_key: str = "", endpoint: str = ""):
        self.provider = provider.lower()
        self.api_key = api_key
        self.endpoint = endpoint # For Ollama

        if self.provider == "gemini" and self.api_key:
            genai.configure(api_key=self.api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

        elif self.provider == "openai" and self.api_key:
            self.openai_client = OpenAI(api_key=self.api_key)

    def summarize(self, text: str, course_name: str, filename: str) -> str:
        if not text.strip():
            return "No text available to summarize."

        # Limit to roughly 30k chars to avoid token limits for basic models
        safe_text = text[:30000]
        prompt = f"""
You are an expert academic assistant.
Please summarize the following material from the course "{course_name}", filename "{filename}".
Extract the key concepts, main topics, and any important formulas or definitions.
Format the output in Markdown with clear headings and bullet points.
Keep it concise but comprehensive.

Here is the content:
{safe_text}
"""

        try:
            if self.provider == "gemini":
                return self._summarize_gemini(prompt)
            elif self.provider == "openai":
                return self._summarize_openai(prompt)
            elif self.provider == "ollama":
                return self._summarize_ollama(prompt)
            else:
                return f"Unsupported provider: {self.provider}"
        except Exception as e:
            return f"Error during summarization: {str(e)}"

    def _summarize_gemini(self, prompt: str) -> str:
        response = self.gemini_model.generate_content(prompt)
        return response.text

    def _summarize_openai(self, prompt: str) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def _summarize_ollama(self, prompt: str) -> str:
        # Default to llama3 if no specific model is configured
        endpoint = self.endpoint or "http://localhost:11434"
        url = f"{endpoint}/api/generate"
        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
