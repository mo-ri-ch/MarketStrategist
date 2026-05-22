import os
import random
import logging
from typing import Dict, Any, List
from app.services.llm import get_openai_client

logger = logging.getLogger("market-strategist-search-trends")

def get_fallback_discoveries(company_name: str, industry: str, services: str) -> List[Dict[str, Any]]:
    """
    Fallback templates for competitor discovery when OpenAI API is not available.
    """
    industry_clean = industry or "Technology"
    
    # Generic competitor templates
    templates = [
        {
            "name": "ApexSystems",
            "website": "https://apexsystems-demo.com",
            "industry": industry_clean,
            "description": "An enterprise SaaS platform specializing in automated workflows and cloud scaling integration.",
            "match_reason": f"Offers overlapping capabilities in {industry_clean} with a focus on enterprise automation solutions.",
            "confidence_score": 0.88
        },
        {
            "name": "NexaCore Technologies",
            "website": "https://nexacore-tech.com",
            "industry": industry_clean,
            "description": "A developer-centric framework provider focusing on low-code UI and instant database bindings.",
            "match_reason": f"Targets similar developer personas by simplifying visual development interfaces in the {industry_clean} domain.",
            "confidence_score": 0.82
        },
        {
            "name": "Stratos Analytics",
            "website": "https://stratos-analytics-mock.com",
            "industry": industry_clean,
            "description": "Real-time market analytics and competitor positioning metrics collector for fast-growing companies.",
            "match_reason": "Direct overlap with intelligence aggregation tools and developer dashboard analytics.",
            "confidence_score": 0.79
        }
    ]
    
    # Pick a random subset of 1-2 competitors to simulate discovery
    return random.sample(templates, k=random.randint(1, 2))

def discover_unmanaged_competitors(company_name: str, industry: str, services: str, region: str = None) -> List[Dict[str, Any]]:
    """
    Discovers potential competitors based on the user's company profile.
    If OPENAI_API_KEY is configured, generates realistic competitors using LLM reasoning.
    """
    region_str = region or "Global"
    logger.info(f"Simulating competitor discovery for: {company_name} in {industry} (Region: {region_str})")
    
    client = get_openai_client()
    
    if not client:
        return get_fallback_discoveries(company_name, industry, services)
        
    prompt = f"""
    You are a premium market research and competitive intelligence discovery tool.
    Analyze the following profile of a company and find 2-3 potential competitors that offer similar products,
    services, or target the same market in the specified region. Generate realistic, fictitious (or real-world) competitors.
    
    Company Name: {company_name}
    Industry: {industry or 'Technology'}
    Services/Offerings: {services or 'Enterprise software services'}
    Target Operating Region: {region_str}
    
    Provide the output strictly as a valid JSON list of competitor objects. Each object must have these exact fields:
    - "name": The name of the competitor company
    - "website": A realistic mockup website URL (e.g. https://competitorname.com)
    - "industry": The primary industry sector
    - "description": A paragraph describing what the competitor does (1-2 sentences)
    - "match_reason": A sentence explaining why they are considered a competitor to "{company_name}"
    - "confidence_score": Float between 0.0 and 1.0 indicating how strongly they compete.
    
    Strictly valid JSON starting with [ and ending with ]. No markdown wrappers.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional competitive intelligence analyst who outputs only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        import json
        content = response.choices[0].message.content.strip()
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
        logger.error(f"Error calling OpenAI in search trends competitor discovery: {e}")
        return get_fallback_discoveries(company_name, industry, services)
