import { useEffect, useMemo, useState } from "react";
import type { RestaurantCard, SupervisorPayload } from "types/whatseat";

interface RecommendationGridProps {
  payload: SupervisorPayload;
}

const GENERIC_TYPES = new Set(["point_of_interest", "establishment", "food", "store", "health", "gym"]);

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
      return normalizeLabel(picked);
    }
    return normalizeLabel(card.types[0]);
  }
  return "Restaurant";
}

function normalizeLabel(label: string): string {
  return label.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function renderRating(card: RestaurantCard): string | null {
  if (card.rating == null) {
    return null;
  }
  if (card.user_rating_count) {
    return `${card.rating.toFixed(1)} / 5 · ${card.user_rating_count.toLocaleString()} reviews`;
  }
  return `${card.rating.toFixed(1)} / 5`;
}

function renderOpenStatus(card: RestaurantCard): string | null {
  if (!card.opens) {
    return null;
  }
  if (card.opens.today_is_open) {
    return card.opens.closes_at ? `Open now · Closes at ${card.opens.closes_at}` : "Open now";
  }
  return "Closed now";
}

function renderDistance(card: RestaurantCard): string | null {
  if (card.distance_km == null) {
    return null;
  }
  return `${card.distance_km.toFixed(1)} km away`;
}

function CardImage({ card }: { card: RestaurantCard }) {
  const photos = useMemo(
    () =>
      (card.photos ?? [])
        .slice(0, 3)
        .map((url) => url.trim())
        .filter((url) => !!url),
    [card.photos],
  );
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    setActiveIndex(0);
  }, [card.place_id, photos.join("|")]);

  if (!photos.length) {
    return (
      <div className="flex h-40 w-full items-center justify-center rounded-t-lg bg-slate-100 text-sm text-slate-500">
        Photo unavailable
      </div>
    );
  }

  const showPrevious = () => {
    setActiveIndex((index) => (index === 0 ? photos.length - 1 : index - 1));
  };

  const showNext = () => {
    setActiveIndex((index) => (index === photos.length - 1 ? 0 : index + 1));
  };

  const handleSelect = (index: number) => {
    setActiveIndex(index);
  };

  const currentPhoto = photos[activeIndex] ?? photos[0];
  const hasMultiple = photos.length > 1;

  return (
    <div className="relative h-40 w-full overflow-hidden rounded-t-lg">
      <img
        src={currentPhoto}
        alt={`${card.name} cover ${activeIndex + 1}`}
        loading="lazy"
        decoding="async"
        className="h-full w-full object-cover"
      />
      {hasMultiple ? (
        <>
          <button
            type="button"
            aria-label="Show previous photo"
            onClick={(event) => {
              event.stopPropagation();
              showPrevious();
            }}
            className="group absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/40 px-2 py-1 text-white transition hover:bg-black/60 focus:outline-none focus:ring-2 focus:ring-white/70"
          >
            <span className="text-lg leading-none">‹</span>
          </button>
          <button
            type="button"
            aria-label="Show next photo"
            onClick={(event) => {
              event.stopPropagation();
              showNext();
            }}
            className="group absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/40 px-2 py-1 text-white transition hover:bg-black/60 focus:outline-none focus:ring-2 focus:ring-white/70"
          >
            <span className="text-lg leading-none">›</span>
          </button>
          <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1">
            {photos.map((_, index) => (
              <button
                key={`${card.place_id}-photo-${index}`}
                type="button"
                aria-label={`Show photo ${index + 1}`}
                onClick={(event) => {
                  event.stopPropagation();
                  handleSelect(index);
                }}
                className={
                  "h-2.5 w-2.5 rounded-full border border-white/80 transition " +
                  (index === activeIndex ? "bg-white" : "bg-white/50 hover:bg-white/80")
                }
              >
                <span className="sr-only">{`Photo ${index + 1}`}</span>
              </button>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

function CardBody({ card }: { card: RestaurantCard }) {
  const priceLabel = formatPriceLevel(card.price_level);
  const typeLabel = resolvePrimaryType(card);
  const ratingText = renderRating(card);
  const openStatus = renderOpenStatus(card);
  const distance = renderDistance(card);
  const typeList = card.types?.map((item) => normalizeLabel(item)) ?? [];

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <header className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-slate-500">{typeLabel}</span>
        <h3 className="text-lg font-semibold text-slate-900">{card.name}</h3>
        {card.address ? <p className="text-sm text-slate-600">{card.address}</p> : null}
        {card.summary ? (
          <p className="text-sm leading-relaxed text-slate-600">{card.summary}</p>
        ) : null}
      </header>
      <dl className="grid grid-cols-1 gap-2 text-sm text-slate-600">
        {ratingText ? (
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Rating</dt>
            <dd>{ratingText}</dd>
          </div>
        ) : null}
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Price</dt>
          <dd>{priceLabel}</dd>
        </div>
        {distance ? (
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Distance</dt>
            <dd>{distance}</dd>
          </div>
        ) : null}
        {openStatus ? (
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Status</dt>
            <dd>{openStatus}</dd>
          </div>
        ) : null}
        {typeList.length ? (
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Types</dt>
            <dd>{typeList.join(" · ")}</dd>
          </div>
        ) : null}
      </dl>
      {card.tags?.length ? (
        <ul className="flex flex-wrap gap-2 text-xs uppercase tracking-wide text-brand">
          {card.tags.map((tag) => (
            <li key={`${card.place_id}-tag-${tag}`} className="rounded-full border border-brand/40 px-2 py-1">
              {tag}
            </li>
          ))}
        </ul>
      ) : null}
      {card.why?.length ? (
        <div className="rounded-md border border-brand/20 bg-brand/5 p-3 text-sm text-brand">
          <p className="text-xs font-semibold uppercase tracking-wide">Why you'll love it</p>
          <ul className="mt-2 space-y-1 pl-4 text-left text-brand">
            {card.why.map((reason, index) => (
              <li key={`${card.place_id}-reason-${index}`} className="list-disc">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="mt-auto flex flex-col gap-2 text-sm">
        {card.deeplink ? (
          <a
            href={card.deeplink}
            target="_blank"
            rel="noreferrer"
            className="text-brand hover:text-brand-muted"
          >
            Get directions →
          </a>
        ) : null}
        {!card.deeplink && card.google_maps_uri ? (
          <a
            href={card.google_maps_uri}
            target="_blank"
            rel="noreferrer"
            className="text-brand hover:text-brand-muted"
          >
            View on Google Maps →
          </a>
        ) : null}
      </div>
    </div>
  );
}

export function RecommendationGrid({ payload }: RecommendationGridProps) {
  if (!payload.cards?.length) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {payload.cards.map((card) => (
        <article key={card.place_id} className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <CardImage card={card} />
          <CardBody card={card} />
        </article>
      ))}
      {payload.rationale ? (
        <p className="md:col-span-2 xl:col-span-3 rounded-lg border border-dashed border-brand/40 bg-brand/5 p-4 text-sm text-slate-700">
          {payload.rationale}
        </p>
      ) : null}
    </div>
  );
}
