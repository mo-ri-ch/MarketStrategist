import os
import random
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.llm import get_openai_client

logger = logging.getLogger("market-strategist-social-scraper")

def get_fallback_posts(competitor_name: str, platform: str) -> List[Dict[str, Any]]:
    """
    Fallback templates for social media posts when OpenAI API is not available.
    """
    templates = {
        "linkedin": [
            {
                "post_text": f"Excited to announce the release of our new platform updates at {competitor_name}! Our engineering team has worked around the clock to deliver 2x performance.",
                "likes": random.randint(120, 450),
                "comments": random.randint(15, 60),
                "shares": random.randint(5, 25),
                "sentiment": 0.8
            },
            {
                "post_text": f"We are hiring! {competitor_name} is looking for Senior Full Stack Engineers and AI Research Scientists to join our remote-first team. Apply now!",
                "likes": random.randint(80, 200),
                "comments": random.randint(10, 30),
                "shares": random.randint(4, 15),
                "sentiment": 0.6
            }
        ],
        "twitter": [
            {
                "post_text": f"Unveiling our new pricing models starting next month! Get ready for more flexibility and lower entry barriers. #SaaS #AI #{competitor_name}",
                "likes": random.randint(50, 150),
                "comments": random.randint(8, 25),
                "shares": random.randint(10, 40),
                "sentiment": 0.4
            },
            {
                "post_text": f"Experiencing some server latency today. Our DevOps team is on it! We apologize for any inconvenience. Status page: status.{competitor_name.lower().replace(' ', '')}.com",
                "likes": random.randint(10, 40),
                "comments": random.randint(25, 80),
                "shares": random.randint(2, 10),
                "sentiment": -0.5
            }
        ],
        "youtube": [
            {
                "post_text": f"How to scale your engineering workflows in 2026 using {competitor_name} - Full Walkthrough Tutorial",
                "likes": random.randint(400, 1200),
                "comments": random.randint(45, 180),
                "shares": random.randint(100, 300),
                "sentiment": 0.7
            }
        ],
        "reddit": [
            {
                "post_text": f"Has anyone tried {competitor_name}'s new automated builder? I'm seeing mixed results with the layout generations. Some parts look great but custom css overrides are tricky.",
                "likes": random.randint(15, 85),
                "comments": random.randint(20, 65),
                "shares": 0,
                "sentiment": 0.1
            }
        ]
    }
    
    platform_key = platform.lower()
    if platform_key in templates:
        return templates[platform_key]
        
    # Generic fallback
    return [
        {
            "post_text": f"Checking out the latest updates from {competitor_name}. Looks like they are expanding their features.",
            "likes": random.randint(5, 50),
            "comments": random.randint(1, 10),
            "shares": random.randint(0, 5),
            "sentiment": 0.2
        }
    ]

def scrape_social_metrics(competitor_name: str, platform: str, region: str = None) -> Dict[str, Any]:
    """
    Gather or simulate analytics and recent posts for a competitor's social media.
    If OPENAI_API_KEY is configured, generates realistic posts matching the competitor's profile.
    """
    region_str = region or "Global"
    logger.info(f"Simulating social scrape for {competitor_name} on {platform} (Region: {region_str})")
    
    # Calculate baseline metrics dynamically based on platform
    platform_hash = sum(ord(c) for c in competitor_name + platform)
    
    if platform.lower() == "youtube":
        follower_count = (platform_hash % 200) * 1500 + 5000
        engagement_rate = round((platform_hash % 10) * 0.008 + 0.02, 3)
    elif platform.lower() == "linkedin":
        follower_count = (platform_hash % 150) * 800 + 2000
        engagement_rate = round((platform_hash % 10) * 0.005 + 0.015, 3)
    elif platform.lower() == "twitter":
        follower_count = (platform_hash % 300) * 500 + 1000
        engagement_rate = round((platform_hash % 10) * 0.003 + 0.008, 3)
    else:
        follower_count = (platform_hash % 100) * 200 + 500
        engagement_rate = round((platform_hash % 10) * 0.01 + 0.01, 3)
        
    client = get_openai_client()
    
    if not client:
        posts = get_fallback_posts(competitor_name, platform)
    else:
        prompt = f"""
        You are a strategic intelligence crawler. Simulate 2 realistic social media updates/posts 
        that a competitor named "{competitor_name}" would post on the platform "{platform}".
        Ensure they sound highly realistic for a business context in 2026.
        For example, mention a new release, hiring, event, pricing shift, or service outage.
        
        Provide the output strictly as a valid JSON list. Each object must have these exact fields:
        - "post_text": The body text of the post
        - "likes": Integer (estimate realistic counts)
        - "comments": Integer
        - "shares": Integer
        - "sentiment": Float between -1.0 and 1.0 (indicating the sentiment of the post text)
        
        Strictly valid JSON starting with [ and ending with ]. No markdown wrappers.
        """
        
        from app.services.regional_filter import inject_regional_modifiers
        prompt = inject_regional_modifiers(prompt, region_str)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional corporate intelligence crawler who outputs only valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            import json
            posts = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            logger.error(f"Error calling OpenAI in social crawler: {e}")
            posts = get_fallback_posts(competitor_name, platform)
            
    # Calculate average sentiment from posts
    avg_sentiment = sum(p.get("sentiment", 0.0) for p in posts) / len(posts) if posts else 0.0
    
    # Structure return payload
    return {
        "follower_count": follower_count,
        "engagement_rate": engagement_rate,
        "avg_sentiment": round(avg_sentiment, 2),
        "posts": posts
    }
