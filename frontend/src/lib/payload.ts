import type { RestaurantCard, SupervisorPayload } from "../types/whatseat";

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function coerceString(value: unknown): string | undefined {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? trimmed : undefined;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (isRecord(value)) {
    if (typeof value.text === "string") {
      return value.text.trim() || undefined;
    }
    if (typeof value.name === "string") {
      return value.name.trim() || undefined;
    }
  }
  return undefined;
}

function coerceNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
}

function coerceBoolean(value: unknown): boolean | undefined {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    if (value.toLowerCase() === "true") {
      return true;
    }
    if (value.toLowerCase() === "false") {
      return false;
    }
  }
  return undefined;
}

function toArray(value: unknown): unknown[] {
  if (Array.isArray(value)) {
    return value;
  }
  if (value == null) {
    return [];
  }
  return [value];
}

function dedupeStrings(values: (string | undefined)[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    if (!value) {
      continue;
    }
    const key = value.trim();
    if (!key || seen.has(key.toLowerCase())) {
      continue;
    }
    seen.add(key.toLowerCase());
    result.push(value.trim());
  }
  return result;
}

function pick(record: UnknownRecord, ...candidates: string[]): unknown {
  for (const candidate of candidates) {
    if (candidate in record) {
      return record[candidate];
    }
    if (candidate.includes(".")) {
      const segments = candidate.split(".");
      let cursor: unknown = record;
      let matched = true;
      for (const segment of segments) {
        if (!isRecord(cursor) || !(segment in cursor)) {
          matched = false;
          break;
        }
        cursor = (cursor as UnknownRecord)[segment];
      }
      if (matched) {
        return cursor;
      }
    }
    const normalized = candidate
      .replace(/\./g, "_")
      .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
      .toLowerCase();
    for (const key of Object.keys(record)) {
      const comparable = key
        .replace(/\./g, "_")
        .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
        .toLowerCase();
      if (comparable === normalized) {
        return record[key];
      }
    }
  }
  return undefined;
}

function extractStringList(value: unknown): string[] {
  const values = toArray(value).map((item) => coerceString(item));
  return dedupeStrings(values);
}

function extractPhotoUrls(value: unknown): string[] {
  const candidates = toArray(value)
    .map((item) => {
      if (typeof item === "string") {
        return item.trim();
      }
      if (isRecord(item)) {
        const byUrl = coerceString(pick(item, "url", "uri", "photo_url", "photoUri", "image", "imageUrl"));
        if (byUrl) {
          return byUrl;
        }
        const reference = coerceString(pick(item, "photo_reference", "photoReference", "name"));
        if (reference && reference.startsWith("http")) {
          return reference;
        }
      }
      return undefined;
    })
    .filter((entry): entry is string => typeof entry === "string" && !!entry);
  return dedupeStrings(candidates);
}

function normalizeOpens(value: unknown): RestaurantCard["opens"] | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const openNow = coerceBoolean(pick(value, "open_now", "openNow", "is_open", "isOpen"));
  const closesAt = coerceString(pick(value, "closes_at", "closesAt", "close_time", "closeTime", "closing_time", "closingTime", "next_close_time", "nextCloseTime"));
  if (openNow == null && !closesAt) {
    return undefined;
  }
  return {
    today_is_open: openNow ?? undefined,
    closes_at: closesAt,
  };
}

function normalizeCard(raw: UnknownRecord): RestaurantCard | null {
  const placeId =
    coerceString(
      pick(
        raw,
        "place_id",
        "placeId",
        "id",
        "places_id",
        "places.id",
        "places.placeId",
        "google_place_id",
        "googlePlaceId",
        "location_id",
        "locationId",
      ),
    ) ??
    coerceString(pick(raw, "google_maps_uri", "googleMapsUri", "maps_url", "mapsUrl", "url")) ??
    coerceString(pick(raw, "name", "displayName", "title"));

  if (!placeId) {
    return null;
  }

  const name =
    coerceString(
      pick(
        raw,
        "name",
        "displayName",
        "display_name",
        "title",
        "places_displayName",
        "places.displayName",
      ),
    ) ?? coerceString(pick(raw, "places.displayName.text", "displayName.text")) ?? placeId;

  const address = coerceString(
    pick(
      raw,
      "formatted_address",
      "formattedAddress",
      "address",
      "vicinity",
      "location",
      "places_formattedAddress",
      "places.formattedAddress",
    ),
  );

  const googleMapsUri = coerceString(
    pick(
      raw,
      "google_maps_uri",
      "googleMapsUri",
      "maps_uri",
      "mapsUri",
      "maps_url",
      "mapsUrl",
      "places_googleMapsUri",
      "places.googleMapsUri",
    ),
  );

  const deeplink =
    coerceString(
      pick(
        raw,
        "deeplink",
        "deep_link",
        "directions_uri",
        "directionsUri",
        "directions_url",
        "directionsUrl",
        "navigation_url",
        "navigationUrl",
        "route_url",
        "routeUrl",
      ),
    ) ?? googleMapsUri;

  const priceLevel = coerceString(pick(raw, "price_level", "priceLevel", "places_priceLevel", "places.priceLevel"));
  const rating = coerceNumber(pick(raw, "rating", "average_rating", "avgRating", "places_rating", "places.rating"));
  const userRatingCount = coerceNumber(
    pick(
      raw,
      "user_rating_count",
      "userRatingCount",
      "user_ratings_total",
      "userRatingsTotal",
      "review_count",
      "reviewCount",
      "places_userRatingCount",
      "places.userRatingCount",
    ),
  );

  const distanceMeters = coerceNumber(
    pick(raw, "distance_meters", "distanceMeters", "distance", "distance_in_meters", "distanceInMeters"),
  );
  const distanceKm = distanceMeters != null ? distanceMeters / 1000 : coerceNumber(pick(raw, "distance_km", "distanceKm"));

  const types = extractStringList(pick(raw, "types", "place_types", "categories", "cuisines", "places_types", "places.types"));
  const tags = extractStringList(pick(raw, "tags", "labels", "features", "attributes", "keywords"));
  const why = extractStringList(pick(raw, "why", "reasons", "highlights", "justifications", "notes", "topReasons"));

  const photos = extractPhotoUrls(
    pick(raw, "photos", "photo_urls", "photoUrls", "images", "imageUrls", "gallery", "photoUris", "photo_uris", "places_photos", "places.photos"),
  );

  const summary = coerceString(
    pick(
      raw,
      "summary",
      "description",
      "short_description",
      "shortDescription",
      "overview",
      "places.generativeSummary.overview",
      "places.generativeSummary",
    ),
  );

  const opens = normalizeOpens(
    pick(
      raw,
      "opens",
      "opening_hours",
      "openingHours",
      "current_opening_hours",
      "currentOpeningHours",
      "places_currentOpeningHours",
      "places.currentOpeningHours",
    ),
  );

  return {
    place_id: placeId,
    name,
    address,
    google_maps_uri: googleMapsUri,
    distance_km: distanceKm,
    price_level: priceLevel,
    rating,
    user_rating_count: userRatingCount,
    types,
    tags,
    why,
    photos,
    opens,
    deeplink,
    summary,
  };
}

function collectCandidateArrays(record: UnknownRecord): unknown[] {
  const candidates: unknown[] = [];
  const keysToInspect = [
    "cards",
    "items",
    "results",
    "recommendations",
    "restaurants",
    "candidates",
    "data",
    "places",
    "payload.cards",
    "payload.items",
  ];

  for (const key of keysToInspect) {
    const value = pick(record, key);
    if (Array.isArray(value)) {
      candidates.push(...value);
    }
  }

  return candidates.length ? candidates : [];
}

export function normalizeSupervisorPayload(raw: unknown): SupervisorPayload | null {
  if (!raw) {
    return null;
  }

  if (Array.isArray(raw)) {
    const cards = raw
      .map((item) => (isRecord(item) ? normalizeCard(item) : null))
      .filter((card): card is RestaurantCard => card !== null);
    if (cards.length) {
      return { cards };
    }
    return null;
  }

  if (!isRecord(raw)) {
    return null;
  }

  let rationale = coerceString(pick(raw, "rationale", "summary", "explanation", "reasoning"));
  const cards: RestaurantCard[] = [];
  const seen = new Set<string>();

  const directCards = pick(raw, "cards");
  if (Array.isArray(directCards)) {
    for (const item of directCards) {
      if (!isRecord(item)) {
        continue;
      }
      const normalized = normalizeCard(item);
      if (normalized && !seen.has(normalized.place_id)) {
        seen.add(normalized.place_id);
        cards.push(normalized);
      }
    }
  }

  if (!cards.length) {
    const candidateItems = collectCandidateArrays(raw);
    for (const item of candidateItems) {
      if (!isRecord(item)) {
        continue;
      }
      const normalized = normalizeCard(item);
      if (normalized && !seen.has(normalized.place_id)) {
        seen.add(normalized.place_id);
        cards.push(normalized);
      }
    }
  }

  if (!cards.length) {
    for (const value of Object.values(raw)) {
      if (!isRecord(value)) {
        continue;
      }
      const nested = normalizeSupervisorPayload(value);
      if (nested?.cards?.length) {
        for (const card of nested.cards) {
          if (!seen.has(card.place_id)) {
            seen.add(card.place_id);
            cards.push(card);
          }
        }
      }
      if (!rationale && nested?.rationale) {
        rationale = nested.rationale;
      }
    }
  }

  if (!cards.length) {
    const maybeSingleCard = normalizeCard(raw);
    if (maybeSingleCard) {
      cards.push(maybeSingleCard);
    }
  }

  if (!cards.length) {
    return null;
  }

  return {
    cards,
    rationale: rationale ?? undefined,
  };
}
