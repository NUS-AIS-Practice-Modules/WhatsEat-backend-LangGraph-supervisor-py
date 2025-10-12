import type { SupervisorPayload } from "@types/whatseat";

interface RecommendationGridProps {
  payload: SupervisorPayload;
}

export function RecommendationGrid({ payload }: RecommendationGridProps) {
  if (!payload.cards?.length) {
    return null;
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {payload.cards.map((card) => (
        <article key={card.place_id} className="flex flex-col gap-3 rounded-md border border-slate-800 bg-slate-900/80 p-4">
          <header className="flex flex-col gap-1">
            <h3 className="text-lg font-semibold text-brand">{card.name}</h3>
            <div className="text-xs uppercase tracking-wide text-slate-400">
              {card.price_level ?? "—"}
              {card.distance_km != null ? ` · ${card.distance_km.toFixed(1)} km away` : null}
            </div>
            {card.tags?.length ? (
              <ul className="flex flex-wrap gap-2 text-[11px] uppercase tracking-wide text-slate-400">
                {card.tags.map((tag) => (
                  <li key={tag} className="rounded border border-slate-800 bg-slate-950 px-2 py-1">
                    {tag}
                  </li>
                ))}
              </ul>
            ) : null}
          </header>
          {card.why?.length ? (
            <div className="rounded-md border border-brand/30 bg-brand-muted/10 p-3 text-sm text-brand">
              <p className="font-medium uppercase tracking-wide text-xs text-brand">Why you'll like it</p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-left text-brand">
                {card.why.map((reason, index) => (
                  <li key={`${card.place_id}-why-${index}`}>{reason}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {card.photos?.length ? (
            <div className="grid grid-cols-3 gap-2">
              {card.photos.slice(0, 3).map((photoUrl, index) => (
                <img
                  key={`${card.place_id}-photo-${index}`}
                  src={photoUrl}
                  alt={`${card.name} photo ${index + 1}`}
                  className="h-20 w-full rounded object-cover"
                />
              ))}
            </div>
          ) : null}
          <footer className="mt-auto flex flex-col gap-2 text-xs text-slate-400">
            {card.opens ? (
              <div>
                {card.opens.today_is_open ? "Open today" : "Closed now"}
                {card.opens.closes_at ? ` · Closes at ${card.opens.closes_at}` : null}
              </div>
            ) : null}
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
          </footer>
        </article>
      ))}
      {payload.rationale ? (
        <p className="md:col-span-2 rounded-md border border-slate-800 bg-slate-950/80 p-4 text-sm text-slate-300">
          {payload.rationale}
        </p>
      ) : null}
    </div>
  );
}
