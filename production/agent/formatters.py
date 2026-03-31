"""
TechCorp Customer Success AI Agent - Formatters

Channel-specific response formatters for email, WhatsApp, and web form.
"""

from typing import Optional


# ============================================================================
# CHANNEL CONSTANTS
# ============================================================================

EMAIL_MAX_WORDS = 500
WHATSAPP_MAX_CHARS = 300
WEB_FORM_MAX_WORDS = 300

EMAIL_SIGNATURE = "Best regards,\nTechCorp Support Team"
WHATSAPP_HUMAN_PROMPT = "Reply 'human' for live support"


# ============================================================================
# EMAIL FORMATTER
# ============================================================================

def format_for_email(text: str, customer_name: str = "") -> str:
    """
    Format response for email channel.
    
    - Add formal greeting with customer name
    - Add signature
    - Ensure under 500 words
    
    Args:
        text: Base response text.
        customer_name: Optional customer name for greeting.
    
    Returns:
        Formatted email string.
    """
    # Build greeting
    if customer_name:
        greeting = f"Dear {customer_name},"
    else:
        greeting = "Dear Valued Customer,"
    
    # Trim text if too long
    words = text.split()
    if len(words) > EMAIL_MAX_WORDS:
        text = ' '.join(words[:EMAIL_MAX_WORDS]) + "..."
    
    # Build email parts
    parts = []
    parts.append(greeting)
    parts.append("")  # Empty line after greeting
    parts.append(text)
    parts.append("")  # Empty line before signature
    parts.append(EMAIL_SIGNATURE)
    
    return '\n'.join(parts)


# ============================================================================
# WHATSAPP FORMATTER
# ============================================================================

def format_for_whatsapp(text: str) -> str:
    """
    Format response for WhatsApp channel.
    
    - Keep under 300 characters
    - Add human prompt hint
    - Remove formal language
    - Conversational tone
    
    Args:
        text: Base response text.
    
    Returns:
        Formatted WhatsApp message string.
    """
    # Remove formal greetings if present
    formal_greetings = [
        "Dear ", "Hello ", "Hi ", "Good morning", "Good afternoon",
        "Good evening", "Valued Customer", "Best regards"
    ]
    
    cleaned_text = text
    for greeting in formal_greetings:
        if cleaned_text.startswith(greeting):
            # Find the end of the greeting line
            newline_pos = cleaned_text.find('\n')
            if newline_pos > 0:
                cleaned_text = cleaned_text[newline_pos + 1:].strip()
    
    # Remove signature if present
    if "Best regards" in cleaned_text:
        cleaned_text = cleaned_text.split("Best regards")[0].strip()
    
    if "TechCorp Support Team" in cleaned_text:
        cleaned_text = cleaned_text.split("TechCorp Support Team")[0].strip()
    
    # Trim to max length (reserve space for human prompt)
    max_content_length = WHATSAPP_MAX_CHARS - len(f"\n\n{WHATSAPP_HUMAN_PROMPT}") - 5
    
    if len(cleaned_text) > max_content_length:
        cleaned_text = cleaned_text[:max_content_length - 3] + "..."
    
    # Add human prompt
    result = cleaned_text.strip()
    
    if WHATSAPP_HUMAN_PROMPT.lower() not in result.lower():
        result += f"\n\n{WHATSAPP_HUMAN_PROMPT}"
    
    return result


# ============================================================================
# WEB FORM FORMATTER
# ============================================================================

def format_for_web_form(text: str, ticket_id: str = "") -> str:
    """
    Format response for web form channel.
    
    - Add semi-formal greeting
    - Add ticket reference if provided
    - Ensure under 300 words
    - Add closing statement
    
    Args:
        text: Base response text.
        ticket_id: Optional ticket ID for reference.
    
    Returns:
        Formatted web form response string.
    """
    parts = []
    
    # Greeting
    parts.append("Hello,")
    parts.append("")
    
    # Ticket reference if available
    if ticket_id:
        parts.append(f"Regarding your ticket #{ticket_id}:")
        parts.append("")
    
    # Trim text if too long
    words = text.split()
    if len(words) > WEB_FORM_MAX_WORDS:
        text = ' '.join(words[:WEB_FORM_MAX_WORDS]) + "..."
    
    parts.append(text)
    parts.append("")
    
    # Closing
    parts.append("If you have any further questions, please don't hesitate to reach out.")
    parts.append("")
    parts.append("Best regards,")
    parts.append("TechCorp Support Team")
    
    return '\n'.join(parts)


# ============================================================================
# ROUTER FUNCTION
# ============================================================================

def format_response(
    text: str,
    channel: str,
    customer_name: str = "",
    ticket_id: str = ""
) -> str:
    """
    Route to correct formatter based on channel.
    
    Args:
        text: Base response text.
        channel: Channel type (email, whatsapp, web_form).
        customer_name: Optional customer name (for email).
        ticket_id: Optional ticket ID (for web form).
    
    Returns:
        Formatted response string.
    
    Raises:
        ValueError: If channel is not recognized.
    """
    channel_lower = channel.lower()
    
    if channel_lower == "email":
        return format_for_email(text, customer_name)
    elif channel_lower == "whatsapp":
        return format_for_whatsapp(text)
    elif channel_lower == "web_form":
        return format_for_web_form(text, ticket_id)
    else:
        raise ValueError(
            f"Unknown channel: {channel}. "
            f"Must be one of: email, whatsapp, web_form"
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def trim_to_channel_limit(text: str, channel: str) -> str:
    """
    Trim text to channel-specific limits without formatting.
    
    Args:
        text: Text to trim.
        channel: Channel type.
    
    Returns:
        Trimmed text.
    """
    channel_lower = channel.lower()
    
    if channel_lower == "email":
        words = text.split()
        if len(words) > EMAIL_MAX_WORDS:
            return ' '.join(words[:EMAIL_MAX_WORDS]) + "..."
        return text
    
    elif channel_lower == "whatsapp":
        if len(text) > WHATSAPP_MAX_CHARS:
            return text[:WHATSAPP_MAX_CHARS - 3] + "..."
        return text
    
    elif channel_lower == "web_form":
        words = text.split()
        if len(words) > WEB_FORM_MAX_WORDS:
            return ' '.join(words[:WEB_FORM_MAX_WORDS]) + "..."
        return text
    
    return text


def get_channel_limits(channel: str) -> dict:
    """
    Get response limits for a channel.
    
    Args:
        channel: Channel type.
    
    Returns:
        Dictionary with limit information.
    
    Raises:
        ValueError: If channel is not recognized.
    """
    channel_lower = channel.lower()
    
    if channel_lower == "email":
        return {
            "type": "words",
            "limit": EMAIL_MAX_WORDS,
            "requires_greeting": True,
            "requires_signature": True
        }
    elif channel_lower == "whatsapp":
        return {
            "type": "characters",
            "limit": WHATSAPP_MAX_CHARS,
            "requires_greeting": False,
            "requires_signature": False,
            "human_prompt": WHATSAPP_HUMAN_PROMPT
        }
    elif channel_lower == "web_form":
        return {
            "type": "words",
            "limit": WEB_FORM_MAX_WORDS,
            "requires_greeting": True,
            "requires_closing": True
        }
    else:
        raise ValueError(
            f"Unknown channel: {channel}. "
            f"Must be one of: email, whatsapp, web_form"
        )
