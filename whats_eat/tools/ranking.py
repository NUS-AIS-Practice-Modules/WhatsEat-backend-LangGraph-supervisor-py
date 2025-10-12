# tools/ranking.py
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import math


def _normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-1 range"""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def _calculate_similarity_score(similarity: float) -> float:
    """
    Convert similarity score (cosine similarity) to ranking score.
    Similarity ranges from -1 to 1, we normalize to 0-1.
    """
    return (similarity + 1) / 2


def _calculate_rating_score(rating: float, rating_count: int) -> float:
    """
    Calculate weighted rating score using Bayesian average.
    Accounts for both rating value and number of reviews.
    
    Formula: (R * v + C * m) / (v + m)
    where:
    - R = average rating for the restaurant
    - v = number of reviews for the restaurant
    - m = minimum reviews required (confidence threshold)
    - C = mean rating across all restaurants
    """
    C = 4.0  # Assumed average rating
    m = 10   # Minimum reviews threshold
    
    if rating == 0:
        return 0.0
    
    # Bayesian average
    weighted_rating = (rating * rating_count + C * m) / (rating_count + m)
    
    # Normalize to 0-1 (assuming max rating is 5)
    return weighted_rating / 5.0


def _match_attributes(restaurant: Dict[str, Any], user_attributes: Dict[str, Any]) -> float:
    """
    Calculate attribute matching score based on user preferences.
    
    Checks:
    - Price band match
    - Dietary restrictions compatibility
    - Cuisine/region match
    - Style preferences
    """
    score = 0.0
    max_score = 0.0
    
    # Price band matching (weight: 0.15)
    if user_attributes.get('price_band'):
        max_score += 0.15
        restaurant_price = restaurant.get('priceLevel', 'PRICE_LEVEL_UNSPECIFIED')
        user_price = user_attributes['price_band']
        
        # Map price levels
        price_map = {
            'budget': ['PRICE_LEVEL_FREE', 'PRICE_LEVEL_INEXPENSIVE'],
            'mid': ['PRICE_LEVEL_MODERATE'],
            'upscale': ['PRICE_LEVEL_EXPENSIVE', 'PRICE_LEVEL_VERY_EXPENSIVE']
        }
        
        if user_price in price_map and restaurant_price in price_map.get(user_price, []):
            score += 0.15
        elif restaurant_price == 'PRICE_LEVEL_UNSPECIFIED':
            score += 0.05  # Partial credit for unknown
    
    # Dietary restrictions (weight: 0.25)
    if user_attributes.get('diet'):
        max_score += 0.25
        restaurant_types = restaurant.get('types', [])
        restaurant_name = restaurant.get('name', '').lower()
        
        diet_restrictions = [d.lower() for d in user_attributes['diet']]
        
        # Check for vegetarian/vegan options
        if any('vegetarian' in d or 'vegan' in d for d in diet_restrictions):
            if any(t in restaurant_types for t in ['vegetarian_restaurant', 'vegan_restaurant']):
                score += 0.25
            elif 'vegetarian' in restaurant_name or 'vegan' in restaurant_name:
                score += 0.15
            else:
                score += 0.05  # Assume most restaurants have some options
        else:
            score += 0.15  # Neutral if no dietary restrictions
    
    # Cuisine/Region matching (weight: 0.35)
    if user_attributes.get('region'):
        max_score += 0.35
        restaurant_types = [t.lower() for t in restaurant.get('types', [])]
        restaurant_name = restaurant.get('name', '').lower()
        user_regions = [r.lower() for r in user_attributes['region']]
        
        # Direct cuisine type match
        matches = 0
        for region in user_regions:
            if any(region in t for t in restaurant_types):
                matches += 1
            elif region in restaurant_name:
                matches += 0.5
        
        if matches > 0:
            score += min(0.35, matches * 0.15)  # Cap at weight
        else:
            score += 0.05  # Minimal score for no match
    
    # Style preferences (weight: 0.25)
    if user_attributes.get('style'):
        max_score += 0.25
        restaurant_types = [t.lower() for t in restaurant.get('types', [])]
        user_styles = [s.lower() for s in user_attributes['style']]
        
        style_matches = 0
        for style in user_styles:
            if style == 'casual' and 'casual' in ' '.join(restaurant_types):
                style_matches += 1
            elif style == 'fine dining' and any(t in restaurant_types for t in ['fine_dining', 'upscale']):
                style_matches += 1
            elif style == 'street food' and any(t in restaurant_types for t in ['food_truck', 'street_food', 'food_cart']):
                style_matches += 1
        
        if style_matches > 0:
            score += min(0.25, style_matches * 0.12)
    
    # Return normalized score (0-1)
    if max_score == 0:
        return 0.5  # Neutral if no attributes to match
    
    return score / max_score


def _calculate_distance_score(distance_km: Optional[float]) -> float:
    """
    Calculate distance score with decay function.
    Closer restaurants get higher scores.
    
    Uses exponential decay: score = e^(-distance/k)
    where k controls the decay rate
    """
    if distance_km is None or distance_km == 0:
        return 1.0  # Unknown distance or same location
    
    # Decay constant (restaurants within 2km get >50% score)
    k = 2.0
    
    # Exponential decay
    score = math.exp(-distance_km / k)
    
    return score


@tool("rank_restaurants_by_profile")
def rank_restaurants_by_profile(
    candidates: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    top_n: int = 5,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Rank restaurants using multi-factor scoring algorithm.
    
    Args:
        candidates: List of restaurant dicts with similarity scores from vector search
        user_profile: User profile with keywords, attributes (price_band, diet, style, region)
        top_n: Number of top results to return (default: 5)
        weights: Optional custom weights for scoring factors
                 Default: similarity=0.35, rating=0.25, attributes=0.25, distance=0.15
    
    Returns:
        Dictionary with ranked results and scoring details
    
    Scoring Algorithm:
        1. Similarity Score (35%): From vector embedding match (Pinecone)
        2. Rating Score (25%): Bayesian average of rating + review count
        3. Attribute Match (25%): Match against user preferences (cuisine, price, diet, style)
        4. Distance Score (15%): Proximity to user location (exponential decay)
        
    Each restaurant gets a final score (0-1) and is ranked accordingly.
    """
    if not candidates:
        return {
            "ranked_results": [],
            "total_candidates": 0,
            "top_n": top_n,
            "error": None
        }
    
    # Default weights
    default_weights = {
        "similarity": 0.35,
        "rating": 0.25,
        "attributes": 0.25,
        "distance": 0.15
    }
    
    if weights:
        default_weights.update(weights)
    
    w = default_weights
    user_attributes = user_profile.get('attributes', {})
    
    # Score each candidate
    scored_results = []
    
    for candidate in candidates:
        # Extract fields
        similarity = candidate.get('score', 0.0)  # From Pinecone
        rating = candidate.get('rating', 0.0)
        rating_count = candidate.get('userRatingCount', 0)
        distance_km = candidate.get('distance_km')  # Optional
        
        # Calculate component scores
        similarity_score = _calculate_similarity_score(similarity)
        rating_score = _calculate_rating_score(rating, rating_count)
        attribute_score = _match_attributes(candidate, user_attributes)
        distance_score = _calculate_distance_score(distance_km)
        
        # Weighted final score
        final_score = (
            w['similarity'] * similarity_score +
            w['rating'] * rating_score +
            w['attributes'] * attribute_score +
            w['distance'] * distance_score
        )
        
        # Add scoring details to result
        scored_result = candidate.copy()
        scored_result['final_score'] = round(final_score, 4)
        scored_result['score_breakdown'] = {
            'similarity': round(similarity_score, 3),
            'rating': round(rating_score, 3),
            'attributes': round(attribute_score, 3),
            'distance': round(distance_score, 3)
        }
        
        scored_results.append(scored_result)
    
    # Sort by final score (descending)
    ranked = sorted(scored_results, key=lambda x: x['final_score'], reverse=True)
    
    # Return top N
    top_results = ranked[:top_n]
    
    return {
        "ranked_results": top_results,
        "total_candidates": len(candidates),
        "top_n": top_n,
        "weights_used": w,
        "error": None
    }


@tool("filter_by_attributes")
def filter_by_attributes(
    candidates: List[Dict[str, Any]],
    required_attributes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Filter restaurants by hard requirements before ranking.
    
    Args:
        candidates: List of restaurant dicts
        required_attributes: Hard filters (e.g., {"min_rating": 4.0, "max_price": "MODERATE"})
    
    Returns:
        Dictionary with filtered results and filter stats
    
    Supported filters:
        - min_rating: Minimum rating (e.g., 4.0)
        - max_price: Maximum price level
        - required_types: Must include these types (e.g., ["thai_restaurant"])
        - exclude_types: Must NOT include these types
        - open_now: Boolean, filter by open status
    """
    if not candidates:
        return {
            "filtered_results": [],
            "original_count": 0,
            "filtered_count": 0,
            "filters_applied": required_attributes
        }
    
    filtered = []
    
    for candidate in candidates:
        # Check min_rating
        if 'min_rating' in required_attributes:
            min_rating = required_attributes['min_rating']
            if candidate.get('rating', 0.0) < min_rating:
                continue
        
        # Check max_price
        if 'max_price' in required_attributes:
            max_price = required_attributes['max_price']
            price_order = ['PRICE_LEVEL_FREE', 'PRICE_LEVEL_INEXPENSIVE', 
                          'PRICE_LEVEL_MODERATE', 'PRICE_LEVEL_EXPENSIVE', 
                          'PRICE_LEVEL_VERY_EXPENSIVE']
            
            restaurant_price = candidate.get('priceLevel', 'PRICE_LEVEL_UNSPECIFIED')
            if restaurant_price in price_order and max_price in price_order:
                if price_order.index(restaurant_price) > price_order.index(max_price):
                    continue
        
        # Check required_types
        if 'required_types' in required_attributes:
            required = required_attributes['required_types']
            restaurant_types = candidate.get('types', [])
            if not any(req in restaurant_types for req in required):
                continue
        
        # Check exclude_types
        if 'exclude_types' in required_attributes:
            excluded = required_attributes['exclude_types']
            restaurant_types = candidate.get('types', [])
            if any(exc in restaurant_types for exc in excluded):
                continue
        
        # Check open_now
        if 'open_now' in required_attributes:
            if required_attributes['open_now'] != candidate.get('isOpen', True):
                continue
        
        # Passed all filters
        filtered.append(candidate)
    
    return {
        "filtered_results": filtered,
        "original_count": len(candidates),
        "filtered_count": len(filtered),
        "filters_applied": required_attributes
    }


__all__ = ["rank_restaurants_by_profile", "filter_by_attributes"]
