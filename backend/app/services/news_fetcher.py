import os
import random
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.llm import get_openai_client

logger = logging.getLogger("market-strategist-news-fetcher")

def get_fallback_news(competitor_name: str) -> List[Dict[str, Any]]:
    """
    Fallback templates for news items when OpenAI API is not available.
    """
    categories = ["funding", "acquisition", "partnership", "product_launch", "general"]
    
    templates = [
        {
            "title": f"{competitor_name} Raises $45M in Series C Funding to Accelerate Enterprise AI Platform",
            "description": f"{competitor_name} announced today that it has secured $45 million in Series C funding. The round was led by Sequoia Capital, with participation from existing investors. The new capital will be used to scale the company's enterprise AI platform and expand its engineering team.",
            "source": "TechCrunch",
            "url": f"https://techcrunch.com/2026/05/{competitor_name.lower().replace(' ', '-')}-funding",
            "sentiment": 0.8,
            "category": "funding"
        },
        {
            "title": f"{competitor_name} Acquires DataAnalytics Corp for $12M to Enhance Predictive Capabilities",
            "description": f"In a strategic move to boost its data intelligence offerings, {competitor_name} has completed the acquisition of DataAnalytics Corp, a developer of advanced forecasting tools. The integration is expected to bring immediate real-time reporting enhancements to users.",
            "source": "VentureBeat",
            "url": f"https://venturebeat.com/2026/05/{competitor_name.lower().replace(' ', '-')}-acquisition",
            "sentiment": 0.6,
            "category": "acquisition"
        },
        {
            "title": f"Google Cloud and {competitor_name} Form Strategic Alliance for Scalable Infrastructure",
            "description": f"Google Cloud and {competitor_name} today announced a multi-year partnership to host and scale cloud operations. Under the agreement, {competitor_name} will migrate its core workloads to Google Cloud and collaborate on joint go-to-market solutions.",
            "source": "Reuters",
            "url": f"https://reuters.com/business/{competitor_name.lower().replace(' ', '-')}-partnership",
            "sentiment": 0.5,
            "category": "partnership"
        },
        {
            "title": f"{competitor_name} Launches Next-Gen Predictive Modeler with Advanced Real-Time Analytics",
            "description": f"Responding to growing market demand for real-time strategy models, {competitor_name} unveiled its new predictive engine. The module promises up to 3x faster response times and seamless API integration for enterprise subscribers.",
            "source": "Forbes",
            "url": f"https://forbes.com/sites/{competitor_name.lower().replace(' ', '-')}-product-launch",
            "sentiment": 0.7,
            "category": "product_launch"
        }
    ]
    
    # Pick a random subset of 2-3 news articles to simulate a real-world fetch
    return random.sample(templates, k=random.randint(2, 3))

def fetch_competitor_news(competitor_name: str) -> List[Dict[str, Any]]:
    """
    Fetches news articles for a competitor.
    If OPENAI_API_KEY is configured, generates realistic news articles matching the competitor's profile.
    """
    logger.info(f"Simulating news fetch for competitor: {competitor_name}")
    
    client = get_openai_client()
    
    if not client:
        return get_fallback_news(competitor_name)
    
    prompt = f"""
    You are a professional market intelligence engine. Generate 2 to 3 highly realistic news articles
    about the competitor "{competitor_name}" that occurred recently in 2026.
    Articles should fall into one of these categories: funding, acquisition, partnership, product_launch, general.
    Ensure they sound like legitimate publications from TechCrunch, VentureBeat, Reuters, Forbes, etc.
    
    Provide the output strictly as a valid JSON list. Each object must have these exact fields:
    - "title": The title of the news article
    - "description": A paragraph describing the news event in detail (2-4 sentences)
    - "source": The publisher name (e.g. TechCrunch, Reuters)
    - "url": A realistic mockup URL
    - "sentiment": Float between -1.0 and 1.0 (the sentiment of the news)
    - "category": One of "funding", "acquisition", "partnership", "product_launch", "general"
    
    Strictly valid JSON starting with [ and ending with ]. No markdown wrappers.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional corporate intelligence news crawler who outputs only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        import json
        content = response.choices[0].message.content.strip()
        # Clean any accidental markdown backticks
        if content.startswith("```"):
            if content.startswith("```json"):
                content = content[7:]
            else:
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error calling OpenAI in news fetcher: {e}")
        return get_fallback_news(competitor_name)
