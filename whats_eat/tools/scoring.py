from __future__ import annotations
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class RankingInput(BaseModel):
    places: List[Dict[str, Any]]
    query_spec: Dict[str, Any]
    user_profile: Optional[Dict[str, Any]] = None

@tool("rank_places", args_schema=RankingInput)
def rank_places(places: List[Dict[str, Any]], query_spec: Dict[str, Any], 
               user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Score and rank places based on query requirements and user preferences.
    Uses multi-criteria decision making to balance factors.
    """
    scored_places = []
    
    for place in places:
        score = 0.0
        reasons = []
        filters_passed = []
        cautions = []
        
        # Location score (if geo in query_spec)
        if query_spec.get('geo') and place.get('location'):
            # TODO: Add haversine distance calculation
            pass
            
        # Price band match
        if query_spec.get('price_band'):
            target_level = len(query_spec['price_band'])  # Count $ signs
            if place.get('price_level') == target_level:
                score += 0.3
                filters_passed.append('price_match')
            elif place.get('price_level', 0) <= target_level:
                score += 0.1
                cautions.append('slightly_cheaper')
            else:
                score -= 0.2
                cautions.append('over_budget')
        
        # Cuisine match
        if query_spec.get('cuisines'):
            place_types = set(place.get('types', []))
            matched_cuisines = place_types.intersection(set(query_spec['cuisines']))
            if matched_cuisines:
                score += 0.2 * len(matched_cuisines)
                reasons.extend([f"serves_{c}" for c in matched_cuisines])
        
        # Diet restrictions
        if query_spec.get('diet_restrictions'):
            # TODO: Add diet validation logic
            pass
            
        # User preference boost
        if user_profile:
            # Boost for preferred cuisines
            preferred = set(user_profile.get('cuisines', []))
            place_types = set(place.get('types', []))
            matches = preferred.intersection(place_types)
            if matches:
                score += 0.1 * len(matches)
                reasons.extend([f"preferred_{c}" for c in matches])
                
            # Penalty for disliked
            disliked = set(user_profile.get('disliked', []))
            if disliked.intersection(place_types):
                score -= 0.3
                cautions.append('contains_disliked')
        
        # Rating/popularity boost
        rating = place.get('rating', 0)
        if rating:
            score += min(0.2, rating / 25.0)  # Small boost for good ratings
            
        # Add to results
        scored_places.append({
            'place_id': place['place_id'],
            'score': round(score, 3),
            'why': reasons,
            'filters_passed': filters_passed,
            'cautions': cautions
        })
    
    # Sort by score descending
    scored_places.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'items': scored_places,
        'rationale': 'Ranked based on location, price match, cuisine preferences and ratings'
    }