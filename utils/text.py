#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 GodEye OSINT Project
"""
Text utilities for GodEye normalization.

Handles text cleaning, normalization, and sanitization.
"""

import re
from typing import Optional
import html
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text for storage.
    
    Operations:
    1. Convert to string if not already
    2. Strip leading/trailing whitespace
    3. Normalize whitespace (collapse multiple spaces)
    4. Decode HTML entities
    5. Remove control characters
    6. Truncate to max_length if specified
    
    Args:
        text: Text to clean
        max_length: Maximum length (truncates with "..." if exceeded)
    
    Returns:
        Cleaned text string
    
    Examples:
        >>> clean_text("  Hello\\n\\nWorld  ")
        "Hello World"
        
        >>> clean_text("Test &amp; text", max_length=10)
        "Test & ..."
        
        >>> clean_text(None)
        ""
    """
    if text is None:
        return ""
    
    # Convert to string
    text = str(text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize string for use as filename.
    
    Removes or replaces characters that are invalid in filenames.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename safe for filesystem
    
    Example:
        >>> sanitize_filename("test/file:name?.txt")
        "test_file_name_.txt"
    """
    # Replace invalid characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def truncate_with_ellipsis(text: str, length: int) -> str:
    """
    Truncate text to length with ellipsis.
    
    Args:
        text: Text to truncate
        length: Maximum length including ellipsis
    
    Returns:
        Truncated text
    
    Example:
        >>> truncate_with_ellipsis("This is a long text", 10)
        "This is..."
    """
    if len(text) <= length:
        return text
    return text[:length - 3] + "..."


def extract_urls(text: str) -> list[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text containing URLs
    
    Returns:
        List of extracted URLs
    
    Example:
        >>> extract_urls("Check https://example.com and http://test.org")
        ['https://example.com', 'http://test.org']
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def extract_emails(text: str) -> list[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text containing emails
    
    Returns:
        List of extracted email addresses
    
    Example:
        >>> extract_emails("Contact user@example.com or admin@test.org")
        ['user@example.com', 'admin@test.org']
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace to single spaces.
    
    Args:
        text: Text with irregular whitespace
    
    Returns:
        Text with normalized whitespace
    
    Example:
        >>> normalize_whitespace("Hello\\n\\n  World\\t!")
        "Hello World !"
    """
    return re.sub(r'\s+', ' ', text).strip()


def remove_emoji(text: str) -> str:
    """
    Remove emoji characters from text.
    
    Args:
        text: Text containing emoji
    
    Returns:
        Text without emoji
    
    Example:
        >>> remove_emoji("Hello 👋 World 🌍")
        "Hello  World "
    """
    # Emoji pattern (Unicode ranges)
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


def extract_hashtags(text: str) -> list[str]:
    """
    Extract hashtags from text (social media).
    
    Args:
        text: Text containing hashtags
    
    Returns:
        List of hashtags without # symbol
    
    Example:
        >>> extract_hashtags("Check out #Python and #OSINT tools!")
        ['Python', 'OSINT']
    """
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)


def extract_mentions(text: str) -> list[str]:
    """
    Extract @mentions from text (social media).
    
    Args:
        text: Text containing mentions
    
    Returns:
        List of usernames without @ symbol
    
    Example:
        >>> extract_mentions("Thanks @user1 and @user2!")
        ['user1', 'user2']
    """
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, text)