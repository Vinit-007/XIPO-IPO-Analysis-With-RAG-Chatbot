
# Simple Sentiment Scoring Module for IPO News


# ===================== SENTIMENT ANALYSIS =====================

def analyze_sentiment(text):
    """
    Analyze sentiment of text using dictionary-based approach.
    
    Args:
        text (str): Text to analyze for sentiment
        
    Returns:
        int: Sentiment score (positive for positive sentiment, negative for negative)
    """
    if not text:
        return 0
    
    # Dictionary of positive financial/news keywords
    # These words typically indicate good news for IPOs
    positive_words = {
        "growth", "profit", "gain", "rise", "surge", "bull", "buy", 
        "oversubscribed", "premium", "listing", "strong", "positive",
        "jump", "high", "record", "success", "moat", "leader"
    }
    
    # Dictionary of negative financial/news keywords
    # These words typically indicate bad news for IPOs
    negative_words = {
        "loss", "fall", "decline", "bear", "sell", "risk", "debt", 
        "litigation", "concern", "negative", "drop", "low", "fail",
        "weak", "correction", "crash", "down", "issue", "worry"
    }
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    words = text_lower.split()
    
    # Calculate sentiment score by counting positive and negative words
    score = 0
    for word in words:
        # Remove punctuation for better word matching
        word = word.strip('.,!?"\'')
        if word in positive_words:
            score += 1  # Increment for positive words
        elif word in negative_words:
            score -= 1  # Decrement for negative words
            
    return score


# Convert numerical sentiment score to categorical label.
def get_label(score):

    if score >= 2:
        return "POSITIVE"
    elif score <= -2:
        return "NEGATIVE"
    else:
        return "NEUTRAL"


# ===================== BATCH PROCESSING =====================
# Score a list of news articles and return aggregate sentiment.
def score_news_articles(news_items):
    scored_news = []
    total_score = 0
    
    # Process each news article
    for item in news_items:
        # Combine headline and summary for comprehensive analysis
        text = f"{item.get('headline', '')} {item.get('summary', '')}"
        
        # Calculate sentiment score and label
        score = analyze_sentiment(text)
        label = get_label(score)
        
        # Create new item with sentiment information
        item_with_score = item.copy()
        item_with_score["sentiment_score"] = score
        item_with_score["sentiment_label"] = label
        
        scored_news.append(item_with_score)
        total_score += score
        
    # Calculate overall sentiment across all articles
    if not news_items:
        avg_score = 0
    else:
        avg_score = total_score / len(news_items)
        
    # Amplify average score for overall label determination
    # This makes the overall label more sensitive to sentiment trends
    overall_label = get_label(avg_score * 3)
    
    return {
        "articles": scored_news,
        "overall_sentiment": {
            "score": round(avg_score, 2),
            "label": overall_label,
            "total_articles": len(news_items)
        }
    }
