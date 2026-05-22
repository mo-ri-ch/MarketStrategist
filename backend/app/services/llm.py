import os
import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger("market-strategist-llm")

def get_openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def generate_company_summary(
    name: str,
    website: str,
    industry: str | None,
    services: str | None,
    region: str | None,
    goals: str | None
) -> str:
    """
    Generate an AI strategic summary profile for an onboarded company.
    """
    client = get_openai_client()
    
    prompt = f"""
    You are an expert market analyst and strategist.
    Analyze the following company profile and write a concise, premium 2-3 paragraph strategic intelligence briefing.
    Include key focus areas, potential competitive positioning, and areas to monitor.

    Company Name: {name}
    Website: {website}
    Industry: {industry or 'Not specified'}
    Services/Offerings: {services or 'Not specified'}
    Geographic Region: {region or 'Not specified'}
    Strategic Goals: {goals or 'Not specified'}

    Output the briefing clearly as raw text.
    """
    
    if not client:
        # Fallback stub when OpenAI API key is not present
        logger.warning("OPENAI_API_KEY environment variable not set. Generating mock company summary.")
        industry_phrase = f"in the {industry} sector" if industry else ""
        region_phrase = f"within the {region} market" if region else ""
        services_phrase = f"focused on: {services}." if services else "with a broad catalog of offerings."
        goals_phrase = f" The primary strategic focus is aligned with: {goals}." if goals else ""
        
        return (
            f"Intel Summary for {name}: {name} operates {industry_phrase} {region_phrase}, "
            f"{services_phrase}{goals_phrase} As a competitor or platform owner, key monitoring vectors "
            f"should focus on their digital footprint updates, feature expansions, and customer engagement "
            f"sentiment spikes across YouTube, LinkedIn, X, and Reddit. Immediate strategic recommendations "
            f"include establishing baseline website diff trackers and setting alerts for pricing adjustments."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional corporate intelligence analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return f"AI strategic summary generation for {name} is temporarily unavailable, but the company profile is successfully registered."
