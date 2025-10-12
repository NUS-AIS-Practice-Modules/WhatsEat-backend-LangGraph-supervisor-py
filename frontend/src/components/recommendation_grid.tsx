import { useState } from "react";
import type { RestaurantCard, SupervisorPayload } from "types/whatseat";

interface RecommendationGridProps {
  payload: SupervisorPayload;
}

const GENERIC_TYPES = new Set([
  "point_of_interest",
  "establishment",
  "food",
  "store",
  "health",
  "gym",
]);

function formatPriceLevel(value?: string): string {
  if (!value) {
    return "—";
  }
  if (/^\$+$/.test(value)) {
    return value;
  }
  if (value.startsWith("PRICE_LEVEL_")) {
    const normalized = value.replace("PRICE_LEVEL_", "").toLowerCase();
    return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
  }
  return value;
}

function resolvePrimaryType(card: RestaurantCard): string {
  if (card.types?.length) {
    const picked = card.types.find((type) => !GENERIC_TYPES.has(type.toLowerCase()));
    if (picked) {
      return picked.replace(/_/g, " ");
    }
  }
  return "Restaurant";
}

function normalizeTypeLabel(label: string): string {
  return label.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatOpenStatus(card: RestaurantCard): string {
  if (!card.opens) {
    return "Hours unavailable";
  }
  if (card.opens.today_is_open) {
    return card.opens.closes_at ? `Open now · Closes at ${card.opens.closes_at}` : "Open now";
  }
  return "Closed now";
}

export function RecommendationGrid({ payload }: RecommendationGridProps) {
  if (!payload.cards?.length) {
    return null;
  }

  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  const handleToggle = (placeId: string) => {
    setExpandedCards((previous) => ({
      ...previous,
      [placeId]: !previous[placeId],
    }));
  };

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {payload.cards.map((card) => {
        const isExpanded = Boolean(expandedCards[card.place_id]);
        const primaryType = normalizeTypeLabel(resolvePrimaryType(card));
        const priceLabel = formatPriceLevel(card.price_level);
        const typeList =
          card.types
            ?.map((type) => normalizeTypeLabel(type))
            .filter((label): label is string => Boolean(label)) ?? [];
        const ratingText =
          card.rating != null
            ? `${card.rating.toFixed(1)}/5${card.user_rating_count ? ` (${card.user_rating_count.toLocaleString()} reviews)` : ""}`
            : null;
        const openStatus = card.opens ? formatOpenStatus(card) : null;

        return (
          <article key={card.place_id} className="flex flex-col gap-3 rounded-md border border-slate-200 bg-white p-4 shadow-sm">
            <button
              type="button"
              onClick={() => handleToggle(card.place_id)}
              aria-expanded={isExpanded}
              className="flex w-full flex-col gap-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            >
              <header className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500">
                  {primaryType}
                </span>
                <h3 className="text-lg font-semibold text-brand">{card.name}</h3>
                {card.address ? (
                  <p className="text-sm text-slate-600">{card.address}</p>
                ) : null}
                {ratingText ? <span className="text-sm text-slate-200">Rating: {ratingText}</span> : null}
                <span className="text-xs uppercase tracking-wide text-slate-600">
                  Price: {priceLabel}
                </span>
                {typeList.length ? (
                  <p className="text-xs uppercase tracking-wide text-slate-600">
                    Types: {typeList.join(" · ")}
                  </p>
                ) : null}
              </header>
              <span className="text-xs text-brand">
                {isExpanded ? "Hide details ↑" : "Show details ↓"}
              </span>
            </button>
            {card.google_maps_uri ? (
              <a
                href={card.google_maps_uri}
                target="_blank"
                rel="noreferrer"
                className="break-all text-xs text-brand hover:text-brand-muted"
              >
                {card.google_maps_uri}
              </a>
            ) : null}
            {isExpanded ? (
              <div className="flex flex-col gap-3 text-sm text-slate-300">
                <span className="text-xs uppercase tracking-wide text-slate-600">
                  Price: {priceLabel}
                </span>
                <span className="text-xs uppercase tracking-wide text-slate-600">
                  Primary Type: {primaryType}
                </span>
                {openStatus ? <span className="text-xs text-slate-400">{openStatus}</span> : null}
                {card.distance_km != null ? (
                  <div className="text-xs uppercase tracking-wide text-slate-600">
                    {card.distance_km.toFixed(1)} km away
                  </div>
                ) : null}
                {card.tags?.length ? (
                  <ul className="flex flex-wrap gap-2 text-[11px] uppercase tracking-wide text-slate-600">
                    {card.tags.map((tag) => (
                      <li key={`${card.place_id}-tag-${tag}`} className="rounded border border-slate-800 bg-slate-950 px-2 py-1">
                        {tag}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {card.why?.length ? (
                  <div className="rounded-md border border-brand/30 bg-brand-muted/10 p-3 text-sm text-brand">
                    <p className="font-medium uppercase tracking-wide text-[11px] text-brand">Why you'll like it</p>
                    <ul className="mt-2 list-disc space-y-1 pl-4 text-left text-brand">
                      {card.why.map((reason, index) => (
                        <li key={`${card.place_id}-why-${index}`}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {card.photos?.[0] ? (
                  <div className="grid grid-cols-3 gap-2">
                    {card.photos.slice(0, 4).map((photoUrl, index) => (
                      <img
                        key={`${card.place_id}-photo-${index}`}
                        src={photoUrl}
                        alt={`${card.name} photo ${index + 1}`}
                        className="h-20 w-full rounded object-cover"
                      />
                    ))}
                  </div>
                ) : null}
                {card.deeplink ? (
                  <a
                    href={card.deeplink}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-brand hover:text-brand-muted"
                  >
                    Get directions →
                  </a>
                ) : null}
              </div>
            ) : null}
          </article>
        );
      })}
      {payload.rationale ? (
        <p className="md:col-span-2 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          {payload.rationale}
        </p>
      ) : null}
    </div>
  );
}
