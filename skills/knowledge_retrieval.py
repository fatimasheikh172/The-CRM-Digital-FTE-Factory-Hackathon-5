"""Knowledge Retrieval Skill for searching product documentation."""

import re
from pathlib import Path
from typing import List, Dict


class KnowledgeRetrievalSkill:
    """
    Skill for retrieving relevant information from product documentation.
    
    Reads from product-docs.md and provides search functionality
    to find relevant sections for customer queries.
    """
    
    def __init__(self, docs_path: str = None):
        """
        Initialize the Knowledge Retrieval Skill.
        
        Args:
            docs_path: Path to the product documentation file.
                      Defaults to context/product-docs.md relative to project root.
        """
        if docs_path is None:
            # Default path relative to project root
            self.docs_path = Path(__file__).parent.parent.parent / "context" / "product-docs.md"
        else:
            self.docs_path = Path(docs_path)
        
        self._content = None
        self._sections = []
        self._load_documentation()
    
    def _load_documentation(self) -> None:
        """Load and parse the product documentation into sections."""
        try:
            with open(self.docs_path, 'r', encoding='utf-8') as f:
                self._content = f.read()
            
            # Parse sections (headers start with ##)
            self._sections = self._parse_sections(self._content)
        except FileNotFoundError:
            print(f"Warning: Documentation file not found at {self.docs_path}")
            self._content = ""
            self._sections = []
        except Exception as e:
            print(f"Error loading documentation: {e}")
            self._content = ""
            self._sections = []
    
    def _parse_sections(self, content: str) -> List[Dict]:
        """
        Parse documentation content into structured sections.
        
        Args:
            content: Raw documentation content.
            
        Returns:
            List of dictionaries with 'title', 'content', and 'keywords'.
        """
        sections = []
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Check for section header (## Header)
            header_match = re.match(r'^##\s+(.+)$', line)
            
            if header_match:
                # Save previous section if exists
                if current_section is not None:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content),
                        'keywords': self._extract_keywords(current_section, current_content)
                    })
                
                current_section = header_match.group(1).strip()
                current_content = []
            elif current_section is not None:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section is not None:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content),
                'keywords': self._extract_keywords(current_section, current_content)
            })
        
        return sections
    
    def _extract_keywords(self, title: str, content: List[str]) -> List[str]:
        """
        Extract keywords from section title and content.
        
        Args:
            title: Section title.
            content: Section content lines.
            
        Returns:
            List of lowercase keywords.
        """
        text = f"{title} {' '.join(content)}".lower()
        # Extract words, excluding common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'and', 'or', 'but', 'if', 'then', 'else', 'when', 'than'}
        
        words = re.findall(r'\b[a-z]+\b', text)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(keywords))
    
    def search(self, query: str) -> List[Dict]:
        """
        Search for relevant sections based on a query.
        
        Args:
            query: Search query string.
            
        Returns:
            List of matching sections with relevance scores.
        """
        if not self._sections:
            return []
        
        query_lower = query.lower()
        query_words = set(re.findall(r'\b[a-z]+\b', query_lower))
        query_words = {w for w in query_words if len(w) > 2}
        
        results = []
        
        for section in self._sections:
            score = 0
            
            # Check title match
            title_lower = section['title'].lower()
            for word in query_words:
                if word in title_lower:
                    score += 3  # Higher weight for title matches
            
            # Check keywords match
            for keyword in section['keywords']:
                if keyword in query_words:
                    score += 2
                elif any(word in keyword for word in query_words):
                    score += 1
            
            # Check content match
            content_lower = section['content'].lower()
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    'title': section['title'],
                    'content': section['content'].strip(),
                    'score': score
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def get_relevant_sections(self, query: str, top_k: int = 3) -> str:
        """
        Get the top K most relevant sections as formatted text.
        
        Args:
            query: Search query string.
            top_k: Number of top sections to return.
            
        Returns:
            Formatted string with relevant sections.
        """
        results = self.search(query)
        
        if not results:
            return "No relevant documentation found."
        
        # Take top K results
        top_results = results[:top_k]
        
        # Format as readable text
        formatted = []
        for result in top_results:
            formatted.append(f"## {result['title']}")
            formatted.append(result['content'])
            formatted.append("")  # Empty line between sections
        
        return '\n'.join(formatted)
