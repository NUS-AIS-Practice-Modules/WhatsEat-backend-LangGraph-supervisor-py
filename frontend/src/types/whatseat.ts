export interface RestaurantCard {
  place_id: string;
  name: string;
  address?: string;
  google_maps_uri?: string;
  distance_km?: number;
  price_level?: string;
  rating?: number;
  user_rating_count?: number;
  types?: string[];
  tags?: string[];
  why?: string[];
  photos?: string[];
  opens?: {
    today_is_open?: boolean;
    closes_at?: string;
  };
  deeplink?: string;
  rationale?: string;
}

export interface SupervisorPayload {
  cards: RestaurantCard[];
  rationale?: string;
}
