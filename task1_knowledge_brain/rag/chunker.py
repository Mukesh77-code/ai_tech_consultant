"""
Document Chunker for Brilliant Directories Help Articles.
Splits articles on heading/topic boundaries, keeps procedures and tables intact,
preserves overlap, and attaches title, URL, section, and image references to every chunk.
"""

import re
from typing import Dict, List


class DocumentChunker:
    def __init__(self, target_chunk_size: int = 500, overlap_size: int = 80):
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

    def chunk_article(self, article: dict) -> List[dict]:
        """
        Takes a parsed article dict and returns a list of enriched chunks.
        """
        chunks = []
        title = article.get("title", "")
        url = article.get("url", "")
        category = article.get("category", "")
        images = article.get("enriched_images", article.get("images", []))

        # Build an image lookup associated with keywords/headings
        chunk_index = 0

        # Process structured sections first
        sections = article.get("sections", [])
        if not sections and article.get("full_text"):
            sections = [{"heading": "Main Content", "content": article["full_text"]}]

        for sec in sections:
            heading = sec.get("heading", "General")
            content = sec.get("content", "").strip()
            if not content:
                continue

            # Identify matching images for this section
            sec_images = []
            for img in images:
                img_desc = img.get("visual_description", "") + " " + img.get("surrounding_context", "") + " " + " ".join(img.get("interface_labels", []))
                if heading.lower() in img_desc.lower() or any(w in content.lower() for w in img.get("interface_labels", [])):
                    sec_images.append({
                        "url": img.get("image_url", img.get("url")),
                        "description": img.get("visual_description", img.get("alt_text", "")),
                        "labels": img.get("interface_labels", [])
                    })

            # Check if content fits in one chunk
            words = content.split()
            if len(words) <= self.target_chunk_size:
                chunk_index += 1
                chunks.append(self._create_chunk(
                    chunk_id=f"{self._sanitize_id(url)}_{chunk_index}",
                    title=title,
                    url=url,
                    category=category,
                    section_heading=heading,
                    text=f"Article: {title}\nCategory: {category}\nSection: {heading}\n\n{content}",
                    images=sec_images
                ))
            else:
                # Split with overlap respecting sentences
                paragraphs = content.split("\n")
                current_block = []
                current_word_count = 0

                for para in paragraphs:
                    p_words = para.split()
                    if current_word_count + len(p_words) > self.target_chunk_size and current_block:
                        chunk_index += 1
                        joined = "\n".join(current_block)
                        chunks.append(self._create_chunk(
                            chunk_id=f"{self._sanitize_id(url)}_{chunk_index}",
                            title=title,
                            url=url,
                            category=category,
                            section_heading=heading,
                            text=f"Article: {title}\nCategory: {category}\nSection: {heading}\n\n{joined}",
                            images=sec_images
                        ))
                        # Retain overlap (last paragraph or slice)
                        current_block = [current_block[-1]] if len(current_block) > 1 else []
                        current_word_count = sum(len(p.split()) for p in current_block)

                    current_block.append(para)
                    current_word_count += len(p_words)

                if current_block:
                    chunk_index += 1
                    joined = "\n".join(current_block)
                    chunks.append(self._create_chunk(
                        chunk_id=f"{self._sanitize_id(url)}_{chunk_index}",
                        title=title,
                        url=url,
                        category=category,
                        section_heading=heading,
                        text=f"Article: {title}\nCategory: {category}\nSection: {heading}\n\n{joined}",
                        images=sec_images
                    ))

        # Also add procedural steps as dedicated high-value chunks if available
        for step_list in article.get("procedural_steps", []):
            if step_list:
                chunk_index += 1
                steps_text = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(step_list)])
                chunks.append(self._create_chunk(
                    chunk_id=f"{self._sanitize_id(url)}_steps_{chunk_index}",
                    title=title,
                    url=url,
                    category=category,
                    section_heading="Step-by-Step Instructions",
                    text=f"Article: {title}\nCategory: {category}\nStep-by-Step Instructions:\n{steps_text}",
                    images=images[:2]
                ))

        # Add image descriptions as retrievable visual chunks
        for img in images:
            if img.get("interface_labels") or img.get("visual_description"):
                chunk_index += 1
                vis_text = (
                    f"Article: {title}\nScreenshot / UI Evidence:\n"
                    f"Settings Path: {img.get('settings_path', 'Dashboard')}\n"
                    f"UI Controls & Labels: {', '.join(img.get('interface_labels', []))}\n"
                    f"Visual Details: {img.get('visual_description', '')}"
                )
                chunks.append(self._create_chunk(
                    chunk_id=f"{self._sanitize_id(url)}_img_{chunk_index}",
                    title=title,
                    url=url,
                    category=category,
                    section_heading=f"UI Interface ({img.get('settings_path', 'Dashboard')})",
                    text=vis_text,
                    images=[img]
                ))

        return chunks

    def _create_chunk(
        self,
        chunk_id: str,
        title: str,
        url: str,
        category: str,
        section_heading: str,
        text: str,
        images: list
    ) -> dict:
        return {
            "chunk_id": chunk_id,
            "title": title,
            "url": url,
            "category": category,
            "section_heading": section_heading,
            "text": text.strip(),
            "images": images
        }

    def _sanitize_id(self, url: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "_", url.split("/")[-1])[:40]
