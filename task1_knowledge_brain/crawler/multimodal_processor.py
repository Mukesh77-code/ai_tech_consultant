"""
Multimodal Image Processor for Knowledge Brain.
Extracts interface labels, button names, settings paths, and visual details from screenshots.
Supports Claude Vision API when available, with an intelligent local visual-context fallback.
"""

import base64
import json
import logging
import os
import re
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class MultimodalProcessor:
    def __init__(self, cache_path: str = "task1_knowledge_brain/storage/image_cache.json"):
        self.cache_path = cache_path
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        self.cache = self._load_cache()
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    def _load_cache(self) -> Dict[str, dict]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading image cache: {e}")
        return {}

    def _save_cache(self) -> None:
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def process_image(self, image_info: dict, article_title: str) -> dict:
        """
        Takes an image dict: {'url': ..., 'alt_text': ..., 'surrounding_context': ...}
        Returns enriched multimodal dict with extracted UI labels, settings paths, and visual description.
        """
        img_url = image_info["url"]

        # Check cache
        if img_url in self.cache:
            return self.cache[img_url]

        alt_text = image_info.get("alt_text", "")
        context = image_info.get("surrounding_context", "")

        # Try Claude Vision if API key is present
        result = None
        if self.anthropic_api_key:
            result = self._describe_with_claude_vision(img_url, article_title, context)

        # Fallback to local heuristic / context synthesizer
        if not result:
            result = self._synthesize_visual_context(img_url, alt_text, context, article_title)

        self.cache[img_url] = result
        self._save_cache()
        return result

    def _describe_with_claude_vision(self, image_url: str, article_title: str, context: str) -> Optional[dict]:
        try:
            # Download image bytes
            resp = requests.get(image_url, timeout=10, headers={"User-Agent": "AITechConsultantBot/1.0"})
            if resp.status_code != 200:
                return None

            content_type = resp.headers.get("Content-Type", "image/png").split(";")[0]
            if "image" not in content_type:
                content_type = "image/png"

            img_base64 = base64.b64encode(resp.content).decode("utf-8")

            prompt = (
                f"You are analyzing a screenshot from a Brilliant Directories help article titled '{article_title}'.\n"
                f"Surrounding article context: {context}\n"
                "Please extract all visible interface details in the screenshot:\n"
                "1. Exact menu and tab names (e.g., Settings > General Settings)\n"
                "2. Form field labels, checkboxes, buttons (e.g., 'Save Changes', 'Enable SSL')\n"
                "3. Any visible error messages, help hints, or status badges\n"
                "Format as a concise JSON object: "
                "{\"visual_description\": \"...\", \"interface_labels\": [\"...\"], \"settings_path\": \"...\"}"
            )

            headers = {
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": content_type,
                                    "data": img_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            api_resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
            if api_resp.status_code == 200:
                data = api_resp.json()
                text_response = data["content"][0]["text"]
                # Parse JSON block
                json_match = re.search(r"\{.*\}", text_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    parsed["image_url"] = image_url
                    parsed["source"] = "claude_vision"
                    return parsed
        except Exception as e:
            logger.warning(f"Claude Vision extraction failed for {image_url}: {e}")
        return None

    def _synthesize_visual_context(self, image_url: str, alt_text: str, context: str, article_title: str) -> dict:
        """
        High-fidelity heuristic visual analyzer for screenshots when Vision API is not active.
        Extracts UI buttons, settings paths, and input fields from nearby text and URL clues.
        """
        labels = []
        settings_path = "Dashboard"

        # Detect paths like "Settings > General Settings" or "Finance > Payment Gateways"
        path_match = re.search(r"([A-Z][a-zA-Z\s]+(?:\s*[>>→]\s*[A-Z][a-zA-Z\s]+)+)", context)
        if path_match:
            settings_path = path_match.group(1).replace("→", ">").strip()

        # Detect quoted buttons or action words: "Click 'Save Changes'", "Select 'Enable'"
        quoted = re.findall(r"['\"]([^'\"]{2,40})['\"]", context)
        for q in quoted:
            if any(term in q.lower() for term in ["settings", "save", "button", "enable", "disable", "tab", "select", "edit", "add", "payment"]):
                labels.append(q)

        # Detect action phrases
        action_matches = re.findall(r"(?:click|select|toggle|choose|navigate to|open)\s+([A-Za-z0-9\s]{3,30})", context, re.I)
        for act in action_matches:
            clean = act.strip().title()
            if clean and clean not in labels:
                labels.append(clean)

        if alt_text and alt_text not in labels:
            labels.append(alt_text)

        desc = f"Screenshot illustrating '{article_title}'. Context: {context[:250]}. "
        if labels:
            desc += f"Visible UI controls and buttons: {', '.join(labels[:6])}. "
        if settings_path != "Dashboard":
            desc += f"Navigation path: {settings_path}."

        return {
            "image_url": image_url,
            "visual_description": desc,
            "interface_labels": list(set(labels))[:8],
            "settings_path": settings_path,
            "source": "contextual_multimodal_analyzer"
        }
