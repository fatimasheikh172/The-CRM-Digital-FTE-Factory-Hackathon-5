"""Escalation Decision Skill for determining when to escalate to human agents."""

import re
from pathlib import Path
from typing import Dict


class EscalationDecisionSkill:
    """
    Skill for deciding whether a customer message requires escalation.
    
    Reads escalation rules from escalation-rules.md and applies
    them based on message content and sentiment.
    """
    
    # Keywords that trigger immediate escalation
    REFUND_KEYWORDS = {'refund', 'refunds', 'money back', 'chargeback', 'cancel subscription'}
    LEGAL_KEYWORDS = {'lawyer', 'attorney', 'legal', 'lawsuit', 'court', 'sue', 'litigation'}
    HUMAN_REQUEST_KEYWORDS = {'human', 'person', 'agent', 'representative', 'manager', 'supervisor', 'speak to someone'}
    ANGER_INDICATORS = {'angry', 'furious', 'enraged', 'outraged', 'disgusted'}
    
    def __init__(self, rules_path: str = None):
        """
        Initialize the Escalation Decision Skill.
        
        Args:
            rules_path: Path to the escalation rules file.
                       Defaults to context/escalation-rules.md.
        """
        if rules_path is None:
            self.rules_path = Path(__file__).parent.parent.parent / "context" / "escalation-rules.md"
        else:
            self.rules_path = Path(rules_path)
        
        self._rules = {}
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load escalation rules from the markdown file."""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse sections
            self._rules = {
                'immediate': self._parse_section(content, 'IMMEDIATELY'),
                'try_first': self._parse_section(content, 'Try First'),
                'never': self._parse_section(content, 'Never')
            }
        except FileNotFoundError:
            print(f"Warning: Escalation rules file not found at {self.rules_path}")
            self._rules = {'immediate': [], 'try_first': [], 'never': []}
        except Exception as e:
            print(f"Error loading escalation rules: {e}")
            self._rules = {'immediate': [], 'try_first': [], 'never': []}
    
    def _parse_section(self, content: str, section_name: str) -> list:
        """
        Parse a section from the rules file.
        
        Args:
            content: Full file content.
            section_name: Name of the section to parse.
            
        Returns:
            List of rules in that section.
        """
        rules = []
        in_section = False
        
        for line in content.split('\n'):
            if section_name.upper() in line.upper():
                in_section = True
                continue
            
            if in_section:
                # Check for next section header
                if line.strip().startswith('##') and in_section:
                    break
                
                # Parse bullet points
                if line.strip().startswith('-'):
                    rule = line.strip()[1:].strip()
                    rules.append(rule.lower())
        
        return rules
    
    def should_escalate(self, message: str, sentiment: float) -> Dict:
        """
        Determine if a message should be escalated.
        
        Args:
            message: Customer message text.
            sentiment: Sentiment score (0.0-1.0, lower = more negative).
            
        Returns:
            Dictionary with 'escalate' (bool), 'reason' (str), and 'urgency' (str).
        """
        message_lower = message.lower()
        
        # Check for immediate escalation triggers
        
        # 1. Refund requests
        if any(keyword in message_lower for keyword in self.REFUND_KEYWORDS):
            return {
                'escalate': True,
                'reason': 'Customer requested refund',
                'urgency': 'high'
            }
        
        # 2. Legal mentions
        if any(keyword in message_lower for keyword in self.LEGAL_KEYWORDS):
            return {
                'escalate': True,
                'reason': 'Customer mentioned legal action',
                'urgency': 'critical'
            }
        
        # 3. Human agent request
        if any(keyword in message_lower for keyword in self.HUMAN_REQUEST_KEYWORDS):
            return {
                'escalate': True,
                'reason': 'Customer requested human agent',
                'urgency': 'high'
            }
        
        # 4. Very negative sentiment (threshold: 0.25 for strict escalation)
        if sentiment < 0.25:
            return {
                'escalate': True,
                'reason': 'Very negative sentiment detected',
                'urgency': 'high'
            }
        
        # 5. Angry/abusive language
        if any(indicator in message_lower for indicator in self.ANGER_INDICATORS):
            return {
                'escalate': True,
                'reason': 'Angry or abusive language detected',
                'urgency': 'high'
            }
        
        # Check for "Try First Then Escalate" conditions
        # These should be handled by the agent first, then escalated if unresolved
        
        # For now, return no escalation needed
        return {
            'escalate': False,
            'reason': None,
            'urgency': 'normal'
        }
