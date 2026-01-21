# =========================================================
# Input Validators
# =========================================================

def validate_topic(topic):
    """
    Validate user input topic
    Returns: (is_valid: bool, error_message: str)
    """
    if not topic or len(topic.strip()) < 5:
        return False, "⚠️ Topic must be at least 5 characters long"
    
    if len(topic) > 200:
        return False, "⚠️ Topic too long (maximum 200 characters)"
    
    # Check for prohibited content
    prohibited_keywords = [
        "explicit", "violence", "gore", "porn", "nsfw",
        "kill", "murder", "death", "blood"
    ]
    
    topic_lower = topic.lower()
    for keyword in prohibited_keywords:
        if keyword in topic_lower:
            return False, "⚠️ Content policy violation. Please use respectful themes."
    
    return True, ""