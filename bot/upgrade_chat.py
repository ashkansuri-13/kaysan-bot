
# -*- coding: utf-8 -*-
"""Upgrade: Better conversation quality + model training focus."""

import re
import logging

log = logging.getLogger("kaysan.upgrade")

# ============================================
# 1. SMART RESPONSE CHECKER
# ============================================

def check_response_quality(response, intent, min_words=8):
    """Check if response meets quality standards."""
    if not response or len(response.strip()) < 3:
        return False, "too_short"
    
    words = response.split()
    
    # Too short for non-chat
    if intent != "chat" and len(words) < min_words:
        return False, "insufficient_detail"
    
    # Repetitive response
    if len(set(words)) < len(words) * 0.3:
        return False, "repetitive"
    
    # Generic filler responses
    fillers = [
        "of course", "sure", "certainly", "definitely",
        "بله", "حتماً", "قطعاً", "البته",
        "باشە", "سڵاو",
    ]
    lower = response.lower().strip()
    if lower in fillers or len(lower) < 10:
        return False, "filler_response"
    
    # All caps (shouting)
    if response.isupper() and len(response) > 20:
        return False, "all_caps"
    
    # Too many emojis (spam)
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]', response))
    if emoji_count > 5:
        return False, "too_many_emojis"
    
    return True, "ok"


def detect_confidence(response):
    """Detect confidence level from response text."""
    high_indicators = [
        "is", "are", "was", "will", "can", "should",
        "هست", "است", "می‌شه", "باید",
    ]
    low_indicators = [
        "i think", "maybe", "perhaps", "might be", "i believe",
        "فکر می‌کنم", "احتمالاً", "شاید",
    ]
    no_confidence = [
        "i dont know", "im not sure", "i have no idea",
        "نمی‌دونم", "مطمئن نیستم",
    ]
    
    lower = response.lower()
    
    for phrase in no_confidence:
        if phrase in lower:
            return "none"
    
    low_count = sum(1 for p in low_indicators if p in lower)
    high_count = sum(1 for p in high_indicators if p in lower)
    
    if low_count > high_count:
        return "low"
    elif high_count > low_count:
        return "high"
    else:
        return "medium"


def get_retry_prompt(original_question, previous_answer, lang, confidence):
    """Generate appropriate retry prompt based on confidence."""
    if confidence == "none":
        return None  # Dont retry if model says it doesnt know
    
    if confidence == "low":
        return f"""Your answer lacked confidence. Please answer more confidently.

User asked: {original_question}
Your answer: {previous_answer}

Provide a clear, confident answer in {lang}:"""
    
    return f"""Your answer was too short. Please provide more detail.

User asked: {original_question}
Your answer: {previous_answer}

Provide a better, more detailed answer in {lang}:"""


def adaptive_response_length(response, intent, user_context=None):
    """Adjust response length based on context."""
    words = response.split()
    
    if intent == "chat" and len(words) > 250:
        if "\n" in response:
            lines = response.split("\n")
            return "\n".join(lines[:20])
        return " ".join(words[:150]) + "..."
    
    # Code question -> ensure explanation + code
    if intent == "code" and "```" in response:
        parts = response.split("```")
        if len(parts) >= 3:
            explanation = parts[0].strip()
            code = parts[1]
            if len(explanation.split()) < 5:
                return f"Here is the solution:\n\n```{code}```"
    
    return response


def format_for_telegram(text):
    """Format response for better Telegram display."""
    # Ensure code blocks are properly formatted
    text = re.sub(r'```(\w+)?\n', r'```\n', text)
    
    # Bold important numbers
    text = re.sub(r'(?<!\*)\b(\d+\.?\d*%)\b(?<!\*)', r'**\1**', text)
    
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Ensure proper spacing around code blocks
    text = re.sub(r'```\n([^`])', r'```\n\n\1', text)
    text = re.sub(r'([^`])\n```', r'\1\n\n```', text)
    
    return text.strip()


def emoji_for_intent(intent, sentiment="neutral"):
    """Get appropriate emoji for intent and sentiment."""
    emoji_map = {
        "chat": {"neutral": "💬", "positive": "😊", "negative": "😔"},
        "code": {"neutral": "💻", "positive": "✅", "negative": "🔧"},
        "reason": {"neutral": "🧮", "positive": "🎯", "negative": "🤔"},
        "creative": {"neutral": "✨", "positive": "🎨", "negative": "📝"},
        "image": {"neutral": "🖼️", "positive": "🎨", "negative": "📷"},
    }
    return emoji_map.get(intent, {}).get(sentiment, "💬")


def detect_user_sentiment(text):
    """Detect user sentiment from text."""
    positive = ["خوب", "عالی", "ممنون", "متشکر", "good", "great", "thanks", "awesome", "perfect"]
    negative = ["بد", "مشکل", "خطا", "bad", "error", "wrong", "broken", "fix", "help"]
    frustrated = ["خسته", "بی‌حوصله", "تکرار", "dumb", "stupid", "useless", "annoying"]
    
    lower = text.lower()
    
    if any(w in lower for w in frustrated):
        return "frustrated"
    if any(w in lower for w in negative):
        return "negative"
    if any(w in lower for w in positive):
        return "positive"
    return "neutral"


def smart_retry_needed(response, intent, min_words=8):
    """Determine if response needs retry."""
    quality_ok, reason = check_response_quality(response, intent, min_words)
    if quality_ok:
        return False, None, None
    
    confidence = detect_confidence(response)
    if confidence == "none":
        return False, None, None
    
    return True, reason, confidence


# ===== Conversation Summarizer =====

def summarize_conversation(messages, max_points=5):
    """Summarize conversation into key points."""
    if not messages:
        return ""
    
    points = []
    for msg in messages[-20:]:  # Last 20 messages
        role = msg.get("role", "")
        text = msg.get("content", "")
        
        if role == "user" and text and len(text) > 10:
            # Extract key topic
            words = text.split()[:8]
            topic = " ".join(words)
            if topic not in points:
                points.append(topic)
    
    if not points:
        return ""
    
    summary = "Recent topics: " + "; ".join(points[:max_points])
    return summary


def build_context_with_summary(history, profile=None):
    """Build context with summary for better conversation flow."""
    if not history:
        return history
    
    # If history is short, use as-is
    if len(history) <= 10:
        return history
    
    # Summarize older messages
    older = history[:-10]
    recent = history[-10:]
    
    summary = summarize_conversation(older)
    if summary:
        summary_msg = {"role": "system", "content": f"[Context: {summary}]"}
        return [summary_msg] + recent
    
    return recent


def detect_topic_continuation(current_text, last_user_text):
    """Detect if user is continuing a previous topic."""
    if not last_user_text:
        return False
    
    # Common continuation words
    continuations = [
        "also", "and", "moreover", "furthermore", "additionally",
        "btw", "by the way", "oh", "wait", "actually",
        "بازم", "همچنین", "ضمناً", "راستی", "آره",
    ]
    
    lower = current_text.lower().strip()
    return any(lower.startswith(c) for c in continuations)


def should_ask_followup(response, intent, user_sentiment):
    """Determine if we should ask a follow-up question."""
    # Don't ask follow-ups for
    if intent in ("code", "image", "reason"):
        return False
    
    if user_sentiment in ("negative", "frustrated"):
        return False
    
    # Ask follow-up if response is short and topic is open-ended
    words = response.split()
    if len(words) < 15 and intent == "chat":
        return True
    
    return False
