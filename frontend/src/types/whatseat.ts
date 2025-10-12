export interface RestaurantCard {
  place_id: string;
  name: string;
  distance_km?: number;
  price_level?: string;
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
