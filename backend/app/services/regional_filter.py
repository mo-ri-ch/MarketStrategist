"""
Regional Filter Service — provides location scope utilities to inject regional search modifiers
and filter competitor intelligence events.
"""

from typing import List, Dict, Any


def inject_regional_modifiers(prompt: str, region: str) -> str:
    """
    Augments a crawling/analysis prompt with regional modifiers to ensure
    the generated or scraped content respects the requested geographic scope.
    """
    region_str = region or "Global"
    if region_str.lower() == "global":
        return prompt

    geographic_instruction = (
        f"\nIMPORTANT geographic constraint: Focus strictly on the '{region_str}' region. "
        f"All generated news, hiring updates, pricing adjustments, or strategic discoveries "
        f"must apply to or occur within the '{region_str}' market."
    )
    return prompt + geographic_instruction


def filter_events_by_region(events: List[Dict[str, Any]], allowed_regions: List[str]) -> List[Dict[str, Any]]:
    """
    Filters a list of competitor events based on a list of allowed regions.
    Always allows 'Global' events.
    """
    if not allowed_regions or "Global" in allowed_regions:
        return events

    allowed_lower = [r.lower() for r in allowed_regions]
    filtered = []
    for event in events:
        event_region = event.get("region", "Global")
        if event_region.lower() == "global" or event_region.lower() in allowed_lower:
            filtered.append(event)
    return filtered
