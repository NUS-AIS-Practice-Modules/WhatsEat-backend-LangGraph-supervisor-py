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
  if (card.photos?.length) {
    return (
      <img
        src={card.photos[0]}
        alt={`${card.name} cover`}
        className="h-40 w-full rounded-t-lg object-cover"
      />
    );
  }

  return (
    <div className="flex h-40 w-full items-center justify-center rounded-t-lg bg-slate-100 text-sm text-slate-500">
      Photo unavailable
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
        {card.google_maps_uri ? (
          <a
            href={card.google_maps_uri}
            target="_blank"
            rel="noreferrer"
            className="break-all text-xs text-slate-400 hover:text-slate-600"
          >
            {card.google_maps_uri}
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
