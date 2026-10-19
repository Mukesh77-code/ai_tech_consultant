"""
Article Parser for Brilliant Directories Knowledge Base.
Extracts title, structure, procedural steps, tables, image context, and metadata.
"""

import hashlib
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag


class ArticleParser:
    def __init__(self):
        pass

    def parse(self, html_content: str, url: str) -> Dict:
        """
        Parse article HTML into a normalized, structured article representation.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract Title
        title = ""
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        elif soup.title and soup.title.get_text(strip=True):
            title = soup.title.get_text(strip=True).split("|")[0].split("-")[0].strip()
        else:
            title = "Untitled Article"

        # 2. Extract Category/Breadcrumbs
        breadcrumbs = []
        bc_nav = soup.find(class_=re.compile(r"breadcrumb", re.I))
        if bc_nav:
            for a in bc_nav.find_all("a"):
                text = a.get_text(strip=True)
                if text and text.lower() not in ["home", "solutions", "knowledge base"]:
                    breadcrumbs.append(text)
        category = " > ".join(breadcrumbs) if breadcrumbs else "General"

        # 3. Locate Main Article Body
        main_container = (
            soup.find("article")
            or soup.find(class_=re.compile(r"article-body|solution-article|article_body|main-content", re.I))
            or soup.find(id=re.compile(r"article-body|solution-article", re.I))
            or soup.find("main")
            or soup.body
        )

        if not main_container:
            main_container = soup

        # 4. Clean up noise inside article container
        for tag in main_container.find_all(["script", "style", "noscript", "iframe", "nav", "footer"]):
            tag.decompose()

        # Remove header/footer widgets that might be nested
        for tag in main_container.find_all(class_=re.compile(r"header|footer|sidebar|share-buttons|feedback-form", re.I)):
            tag.decompose()

        # 5. Extract Image References with immediate textual context
        images = []
        for img in main_container.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            # Skip tracking pixels, tiny icons, or branding logos
            if any(skip in src.lower() for skip in ["logo", "icon", "pixel", "avatar", "spacer", "star"]):
                continue

            alt = img.get("alt", "").strip()
            
            # Find surrounding context (parent paragraph or siblings)
            parent = img.parent
            context_paragraphs = []
            if parent:
                # previous paragraph or text
                prev = parent.find_previous_sibling(["p", "li", "h2", "h3", "h4"])
                if prev:
                    context_paragraphs.append(prev.get_text(strip=True))
                
                # parent text itself
                parent_text = parent.get_text(strip=True)
                if parent_text and parent_text not in context_paragraphs:
                    context_paragraphs.append(parent_text)

                # next paragraph or text
                nxt = parent.find_next_sibling(["p", "li", "h2", "h3", "h4"])
                if nxt:
                    context_paragraphs.append(nxt.get_text(strip=True))

            nearby_text = " ".join([p for p in context_paragraphs if p]).strip()

            images.append({
                "url": src,
                "alt_text": alt,
                "surrounding_context": nearby_text[:500] if nearby_text else alt
            })

        # 6. Extract Procedural Steps (ordered lists)
        procedural_steps = []
        for ol in main_container.find_all("ol"):
            steps = [li.get_text(strip=True) for li in ol.find_all("li") if li.get_text(strip=True)]
            if steps:
                procedural_steps.append(steps)

        # 7. Extract Tables
        tables = []
        for table in main_container.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if any(cells):
                    rows.append(" | ".join(cells))
            if rows:
                tables.append("\n".join(rows))

        # 8. Extract Headings and Structured Sections
        sections = []
        current_heading = "Overview"
        current_content = []

        for element in main_container.children:
            if isinstance(element, Tag):
                if element.name in ["h1", "h2", "h3", "h4"]:
                    if current_content:
                        sections.append({
                            "heading": current_heading,
                            "content": "\n".join(current_content).strip()
                        })
                        current_content = []
                    current_heading = element.get_text(strip=True)
                else:
                    text = element.get_text(separator=" ", strip=True)
                    if text:
                        current_content.append(text)

        if current_content:
            sections.append({
                "heading": current_heading,
                "content": "\n".join(current_content).strip()
            })

        # If no sections were separated by headings, gather all text
        full_text = main_container.get_text(separator="\n", strip=True)
        # Normalize whitespace
        full_text = re.sub(r"\n{3,}", "\n\n", full_text)

        # 9. Compute Content Hash
        content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        return {
            "url": url,
            "title": title,
            "category": category,
            "sections": sections if sections else [{"heading": "Main Content", "content": full_text}],
            "full_text": full_text,
            "procedural_steps": procedural_steps,
            "tables": tables,
            "images": images,
            "content_hash": content_hash
        }
