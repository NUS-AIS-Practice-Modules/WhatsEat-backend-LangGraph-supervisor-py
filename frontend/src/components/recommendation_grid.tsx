import { useEffect, useMemo, useState } from "react";
import type { RestaurantCard, SupervisorPayload } from "types/whatseat";
import type { LocationCoordinates } from "../hooks/use_location";

interface RecommendationGridProps {
  payload: SupervisorPayload;
  userLocation: LocationCoordinates | null;
}

// 详情页组件
function RestaurantDetails({ card, onBack, userLocation }: { card: RestaurantCard; onBack: () => void; userLocation: LocationCoordinates | null }) {
  const priceLabel = formatPriceLevel(card.price_level);
  const typeLabel = resolvePrimaryType(card);
  const ratingText = renderRating(card);
  const openStatus = renderOpenStatus(card);
  const distance = renderDistance(card);
  const typeList = card.types?.map((item) => normalizeLabel(item)) ?? [];

  const photos = useMemo(
    () =>
      (card.photos ?? [])
        .map((url) => url.trim())
        .filter((url) => !!url),
    [card.photos],
  );
  const [activeIndex, setActiveIndex] = useState(0);
  const [showMap, setShowMap] = useState(false);
  const [lastPhotoIndex, setLastPhotoIndex] = useState(0);

  useEffect(() => {
    setActiveIndex(0);
    setShowMap(false);
  }, [card.place_id, photos.join("|")]);

  const showPrevious = () => {
    setActiveIndex((index) => (index === 0 ? photos.length - 1 : index - 1));
  };

  const showNext = () => {
    setActiveIndex((index) => (index === photos.length - 1 ? 0 : index + 1));
  };

  const handleSelect = (index: number) => {
    setActiveIndex(index);
  };

  const toggleMapView = () => {
    if (!showMap) {
      setLastPhotoIndex(activeIndex);
    }
    setShowMap(!showMap);
  };

  const currentPhoto = photos.length > 0 ? photos[activeIndex] ?? photos[0] : null;
  const hasMultiple = photos.length > 1;

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      {/* 顶部导航栏 */}
      <div className="bg-orange-600 px-6 py-4 flex justify-between items-center">
        <h2 className="text-white text-xl font-semibold">{card.name}</h2>
        <button
          onClick={onBack}
          className="text-white text-sm bg-orange-700 hover:bg-orange-800 px-4 py-2 rounded transition-colors"
        >
          ← Back to List
        </button>
      </div>

      <div className="p-6">
        {/* 图片轮播/地图区域 - 根据模式切换不同的容器 */}
        {!showMap ? (
          // 轮播图模式 - 使用原来的图片容器
          currentPhoto ? (
            <div className="relative h-96 w-full overflow-hidden rounded-lg mb-6">
              <img
                src={currentPhoto}
                alt={`${card.name} photo ${activeIndex + 1}`}
                loading="lazy"
                className="h-full w-full object-cover"
              />
              {hasMultiple && (
                <>
                  <button
                    type="button"
                    aria-label="Previous image"
                    onClick={showPrevious}
                    className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 px-3 py-2 text-white text-2xl transition hover:bg-black/70"
                  >
                    ‹
                  </button>
                  <button
                    type="button"
                    aria-label="Next image"
                    onClick={showNext}
                    className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 px-3 py-2 text-white text-2xl transition hover:bg-black/70"
                  >
                    ›
                  </button>
                  <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-2">
                    {photos.map((_, index) => (
                      <button
                      key={`photo-dot-${index}`}
                      type="button"
                      aria-label={`Show image ${index + 1}`}
                      onClick={() => handleSelect(index)}
                        className={
                          "h-3 w-3 rounded-full border-2 border-white transition " +
                          (index === activeIndex ? "bg-white" : "bg-white/50 hover:bg-white/80")
                        }
                      />
                    ))}
                  </div>
                </>
              )}
              {/* 左下角地图切换按钮 */}
              {userLocation && card.address && (
                <button
                  type="button"
                  onClick={toggleMapView}
                  className="absolute bottom-4 left-4 w-24 h-24 rounded-xl overflow-hidden border-3 border-white shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  aria-label="Switch to navigation map"
                >
                  <div className="w-full h-full bg-orange-500 flex items-center justify-center">
                    <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                  </div>
                </button>
              )}
            </div>
          ) : (
            <div className="flex h-96 w-full items-center justify-center rounded-lg bg-slate-100 text-slate-500 mb-6">
              No images available
            </div>
          )
        ) : (
          // 地图模式 - 使用专门的 iframe 容器
          userLocation && card.address ? (
            <div className="relative h-96 w-full overflow-hidden rounded-lg mb-6 bg-white">
              {/* 使用 iframe 渲染完整的 HTML 地图 */}
              <iframe
                srcDoc={`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Route Map</title>
  <style>
    body { margin:0; padding:0; }
    #map { width: 100%; height: 100vh; }
  </style>
</head>
<body>
<div id="map"></div>
<script>
  const ORIGIN = { lat: ${userLocation.latitude}, lng: ${userLocation.longitude} };
  const DEST_ADDR = "${card.address.replace(/"/g, '\\"')}";
  
  let map, dirSvc, dirRenderer;
  function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
      center: ORIGIN, zoom: 13
    });
    dirSvc = new google.maps.DirectionsService();
    dirRenderer = new google.maps.DirectionsRenderer({ map: map });
    
    dirSvc.route({
      origin: ORIGIN,
      destination: DEST_ADDR,
      travelMode: google.maps.TravelMode.DRIVING
    }, (res, status) => {
      if (status === 'OK') {
        dirRenderer.setDirections(res);
      } else {
        alert('Unable to load route: ' + status);
      }
    });
  }
  window.initMap = initMap;
</script>
<script async defer src="https://maps.googleapis.com/maps/api/js?key=AIzaSyB5yMwQo7k6ilAjWviqhVph_UrGKQMXL6Q&callback=initMap"></script>
</body>
</html>`}
                className="h-full w-full border-0"
                title="Navigation Map"
              />
              {/* 左下角照片切换按钮 */}
              <button
                type="button"
                onClick={toggleMapView}
                className="absolute bottom-4 left-4 w-24 h-24 rounded-xl overflow-hidden border-3 border-white shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-orange-500 z-10"
                aria-label="Back to gallery"
              >
                <img
                  src={photos[lastPhotoIndex] ?? photos[0]}
                  alt="Back to gallery"
                  className="w-full h-full object-cover"
                />
              </button>
            </div>
          ) : null
        )}

        {/* 详细信息区域 */}
        <div className="space-y-6">
          {/* 基本信息 */}
          <div className="flex justify-between items-start border-b pb-4">
            <div className="flex-1">
              <span className="text-sm uppercase tracking-wide text-slate-500">{typeLabel}</span>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{card.name}</h3>
              {card.address && (
                <p className="text-slate-600 mt-2 flex items-start gap-2">
                  <span className="text-slate-400">📍</span>
                  {card.address}
                </p>
              )}
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-orange-600">{priceLabel}</span>
            </div>
          </div>

          {/* 摘要 */}
          {card.summary && (
            <div className="bg-slate-50 rounded-lg p-4">
              <p className="text-slate-700 leading-relaxed">{card.summary}</p>
            </div>
          )}

          {/* 详细信息网格 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ratingText && (
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <dt className="text-xs uppercase tracking-wide text-slate-500 mb-2">⭐ Rating</dt>
                <dd className="text-lg font-semibold text-slate-900">{ratingText}</dd>
              </div>
            )}
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <dt className="text-xs uppercase tracking-wide text-slate-500 mb-2">💰 Price</dt>
              <dd className="text-lg font-semibold text-slate-900">{priceLabel}</dd>
            </div>
            {distance && (
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <dt className="text-xs uppercase tracking-wide text-slate-500 mb-2">📏 Distance</dt>
                <dd className="text-lg font-semibold text-slate-900">{distance}</dd>
              </div>
            )}
            {openStatus && (
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <dt className="text-xs uppercase tracking-wide text-slate-500 mb-2">🕒 Status</dt>
                <dd className="text-lg font-semibold text-slate-900">{openStatus}</dd>
              </div>
            )}
          </div>

          {/* 类型标签 */}
          {typeList.length > 0 && (
            <div>
              <p className="text-sm uppercase tracking-wide text-slate-500 mb-3">Restaurant Types</p>
              <div className="flex flex-wrap gap-2">
                {typeList.map((type, index) => (
                  <span
                    key={`type-${index}`}
                    className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm"
                  >
                    {type}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 标签 */}
          {card.tags && card.tags.length > 0 && (
            <div>
              <p className="text-sm uppercase tracking-wide text-slate-500 mb-3">Features</p>
              <div className="flex flex-wrap gap-2">
                {card.tags.map((tag) => (
                  <span
                    key={`tag-${tag}`}
                    className="px-3 py-1 border border-orange-400 text-orange-600 rounded-full text-sm font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 推荐理由 */}
          {card.why && card.why.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-5">
              <p className="text-sm font-semibold uppercase tracking-wide text-orange-800 mb-3">
                💡 Why We Recommend
              </p>
              <ul className="space-y-2 text-slate-700">
                {card.why.map((reason, index) => (
                  <li key={`reason-${index}`} className="flex items-start gap-2">
                    <span className="text-orange-500 mt-1">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            {card.deeplink && (
              <a
                href={card.deeplink}
                target="_blank"
                rel="noreferrer"
                className="flex-1 bg-orange-600 hover:bg-orange-700 text-white font-medium py-3 px-6 rounded-lg text-center transition-colors"
              >
                📍 Get Directions
              </a>
            )}
            {!card.deeplink && card.google_maps_uri && (
              <a
                href={card.google_maps_uri}
                target="_blank"
                rel="noreferrer"
                className="flex-1 bg-orange-600 hover:bg-orange-700 text-white font-medium py-3 px-6 rounded-lg text-center transition-colors"
              >
                📍 View on Google Maps
              </a>
            )}
            <button
              onClick={onBack}
              className="flex-1 bg-white border-2 border-slate-300 text-slate-700 font-medium py-3 px-6 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Back to List
            </button>
          </div>
        </div>
      </div>
    </div>
  );
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

export function RecommendationGrid({ payload, userLocation }: RecommendationGridProps) {
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);

  if (!payload.cards?.length) {
    return null;
  }

  // 查找选中的餐厅
  const selectedCard = selectedPlaceId 
    ? payload.cards.find((card) => card.place_id === selectedPlaceId)
    : null;

  // 如果选中了餐厅，显示详情页
  if (selectedCard) {
    return <RestaurantDetails card={selectedCard} onBack={() => setSelectedPlaceId(null)} userLocation={userLocation} />;
  }

  // 否则显示卡片列表
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {payload.cards.map((card) => (
          <article 
            key={card.place_id} 
            onClick={() => setSelectedPlaceId(card.place_id)}
            className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm cursor-pointer hover:shadow-lg hover:border-orange-300 transition-all"
          >
            <CardImage card={card} />
            <CardBody card={card} />
          </article>
        ))}
      </div>
      {payload.rationale ? (
        <p className="rounded-lg border border-dashed border-brand/40 bg-brand/5 p-4 text-sm text-slate-700">
          {payload.rationale}
        </p>
      ) : null}
    </div>
  );
}
