"""Channel Adaptation Skill for formatting responses per channel."""

import re
from pathlib import Path
from typing import Dict


class ChannelAdaptationSkill:
    """
    Skill for adapting response formatting to different channels.
    
    Reads brand voice guidelines and applies channel-specific
    formatting rules for Email, WhatsApp, and Web Form.
    """
    
    def __init__(self, brand_voice_path: str = None):
        """
        Initialize the Channel Adaptation Skill.
        
        Args:
            brand_voice_path: Path to the brand voice file.
                            Defaults to context/brand-voice.md.
        """
        if brand_voice_path is None:
            self.brand_voice_path = Path(__file__).parent.parent.parent / "context" / "brand-voice.md"
        else:
            self.brand_voice_path = Path(brand_voice_path)
        
        self._brand_voice = {}
        self._load_brand_voice()
    
    def _load_brand_voice(self) -> None:
        """Load brand voice guidelines from the markdown file."""
        try:
            with open(self.brand_voice_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse key guidelines
            self._brand_voice = {
                'overall_tone': self._parse_section(content, 'Overall Tone'),
                'email_style': self._parse_section(content, 'Email Style'),
                'whatsapp_style': self._parse_section(content, 'WhatsApp Style'),
                'web_form_style': self._parse_section(content, 'Web Form Style')
            }
        except FileNotFoundError:
            print(f"Warning: Brand voice file not found at {self.brand_voice_path}")
            self._brand_voice = {}
        except Exception as e:
            print(f"Error loading brand voice: {e}")
            self._brand_voice = {}
    
    def _parse_section(self, content: str, section_name: str) -> list:
        """
        Parse a section from the brand voice file.
        
        Args:
            content: Full file content.
            section_name: Name of the section to parse.
            
        Returns:
            List of guidelines in that section.
        """
        guidelines = []
        in_section = False
        
        for line in content.split('\n'):
            if section_name.upper() in line.upper() or section_name.lower() in line.lower():
                in_section = True
                continue
            
            if in_section:
                # Check for next section header
                if line.strip().startswith('##') and in_section:
                    break
                
                # Parse bullet points
                if line.strip().startswith('-'):
                    guideline = line.strip()[1:].strip()
                    guidelines.append(guideline)
        
        return guidelines
    
    def format_response(self, response: str, channel: str, customer_name: str = None) -> str:
        """
        Format a response for the specified channel.
        
        Args:
            response: Base response text to format.
            channel: Channel type ('email', 'whatsapp', 'web_form').
            customer_name: Optional customer name for personalization.
            
        Returns:
            Formatted response string.
        """
        channel = channel.lower()
        
        if channel == 'email':
            return self._format_email(response, customer_name)
        elif channel == 'whatsapp':
            return self._format_whatsapp(response)
        elif channel == 'web_form':
            return self._format_web_form(response, customer_name)
        else:
            # Default to web form style for unknown channels
            return self._format_web_form(response, customer_name)
    
    def _format_email(self, response: str, customer_name: str = None) -> str:
        """
        Format response for email channel.
        
        - Formal tone with greeting and signature
        - Under 300 words
        - Use bullet points for steps
        
        Args:
            response: Base response text.
            customer_name: Customer name for greeting.
            
        Returns:
            Formatted email response.
        """
        # Build greeting
        if customer_name:
            greeting = f"Dear {customer_name},"
        else:
            greeting = "Dear Valued Customer,"
        
        # Ensure response has proper structure
        formatted_body = self._add_bullet_points(response)
        
        # Truncate if over 300 words
        words = formatted_body.split()
        if len(words) > 280:  # Leave room for greeting/signature
            formatted_body = ' '.join(words[:280]) + '...'
        
        # Add signature
        signature = "\n\nBest regards,\nTechCorp Support Team"
        
        return f"{greeting}\n\n{formatted_body}{signature}"
    
    def _format_whatsapp(self, response: str) -> str:
        """
        Format response for WhatsApp channel.
        
        - Casual and short
        - Max 2-3 sentences
        - No formal greeting
        
        Args:
            response: Base response text.
            
        Returns:
            Formatted WhatsApp response.
        """
        # Remove any formal greetings
        response = re.sub(r'^(dear|hello|hi|hey)\s*\w*,?\s*', '', response, flags=re.IGNORECASE)
        
        # Remove markdown headers for WhatsApp
        response = re.sub(r'^##\s+', '', response, flags=re.MULTILINE)
        response = re.sub(r'^###\s+', '', response, flags=re.MULTILINE)
        
        # Convert bullet points to simple text
        response = re.sub(r'^[\-\•]\s*', '', response, flags=re.MULTILINE)
        
        # Keep it to 2-3 sentences (max ~50 words)
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Take first 3 sentences
        limited_sentences = sentences[:3]
        
        # Join and ensure under 3 sentences
        result = '. '.join(limited_sentences)
        if not result.endswith('.'):
            result += '.'
        
        # Truncate if still too long
        words = result.split()
        if len(words) > 40:
            result = ' '.join(words[:40]) + '...'
            if not result.endswith('.'):
                result += '.'
        
        return response if len(response) < 100 else result
    
    def _format_web_form(self, response: str, customer_name: str = None) -> str:
        """
        Format response for web form channel.
        
        - Semi-formal
        - Medium length
        - Numbered steps when needed
        
        Args:
            response: Base response text.
            customer_name: Optional customer name.
            
        Returns:
            Formatted web form response.
        """
        # Add numbered steps where appropriate
        formatted_body = self._add_numbered_steps(response)
        
        # Add greeting if name provided
        if customer_name:
            greeting = f"Hello {customer_name},\n\n"
        else:
            greeting = ""
        
        # Add closing
        closing = "\n\nThank you for contacting TechCorp Support."
        
        return f"{greeting}{formatted_body}{closing}"
    
    def _add_bullet_points(self, text: str) -> str:
        """
        Convert numbered lists or steps to bullet points.
        
        Args:
            text: Text to format.
            
        Returns:
            Text with bullet points.
        """
        # Convert numbered lists to bullets
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Match numbered items like "1.", "1)", "1-"
            match = re.match(r'^\s*(\d+)[.\)\-]\s*(.+)$', line)
            if match:
                formatted_lines.append(f"• {match.group(2)}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _add_numbered_steps(self, text: str) -> str:
        """
        Ensure steps are properly numbered.
        
        Args:
            text: Text to format.
            
        Returns:
            Text with numbered steps.
        """
        # Already has numbered steps, keep as is
        if re.search(r'^\s*\d+[.\)]\s+', text, re.MULTILINE):
            return text
        
        # Convert bullet points to numbered
        lines = text.split('\n')
        formatted_lines = []
        step_number = 1
        
        for line in lines:
            if line.strip().startswith('•') or line.strip().startswith('-'):
                content = re.sub(r'^\s*[•\-]\s*', '', line)
                formatted_lines.append(f"{step_number}. {content}")
                step_number += 1
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
