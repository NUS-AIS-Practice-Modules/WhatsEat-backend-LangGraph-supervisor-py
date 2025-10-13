import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import type { RestaurantCard, SupervisorPayload } from "types/whatseat";

interface RecommendationGridProps {
  payload: SupervisorPayload;
  onRequestMore?: () => void | Promise<void>;
  disableRequestMore?: boolean;
}

// 详情页组件
function RestaurantDetails({ card, onBack }: { card: RestaurantCard; onBack: () => void }) {
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
  const [animateIn, setAnimateIn] = useState(false);

  useEffect(() => {
    setActiveIndex(0);
  }, [card.place_id, photos.join("|")]);

  useEffect(() => {
    setAnimateIn(false);
    const frame = requestAnimationFrame(() => setAnimateIn(true));
    return () => cancelAnimationFrame(frame);
  }, [card.place_id]);

  const showPrevious = () => {
    setActiveIndex((index) => (index === 0 ? photos.length - 1 : index - 1));
  };

  const showNext = () => {
    setActiveIndex((index) => (index === photos.length - 1 ? 0 : index + 1));
  };

  const handleSelect = (index: number) => {
    setActiveIndex(index);
  };

  const currentPhoto = photos.length > 0 ? photos[activeIndex] ?? photos[0] : null;
  const hasMultiple = photos.length > 1;

  return (
    <div className="flex w-full justify-center px-2 sm:px-4 perspective-1200">
      <div
        className={clsx(
          "w-full max-w-3xl origin-left",
          animateIn && "animate-restaurant-flip",
        )}
      >
        <div className="mx-auto flex max-h-[78vh] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          {/* 顶部导航栏 */}
          <div className="flex flex-none items-center justify-between bg-orange-600 px-5 py-3">
            <h2 className="text-left text-white text-base font-semibold lg:text-lg">{card.name}</h2>
            <button
              onClick={onBack}
              className="rounded bg-orange-700 px-3 py-1 text-xs text-white transition-colors hover:bg-orange-800"
            >
              ← 返回列表
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 pb-5 pt-4">
            {/* 图片轮播区域 */}
            {currentPhoto ? (
              <div className="relative mb-5 h-60 w-full overflow-hidden rounded-lg lg:h-64">
                <img
                  src={currentPhoto}
                  alt={`${card.name} 图片 ${activeIndex + 1}`}
                  loading="lazy"
                  className="h-full w-full object-cover"
                />
                {hasMultiple && (
                  <>
                    <button
                      type="button"
                      aria-label="上一张图片"
                      onClick={showPrevious}
                      className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 px-3 py-2 text-white text-2xl transition hover:bg-black/70"
                    >
                      ‹
                    </button>
                    <button
                      type="button"
                      aria-label="下一张图片"
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
                          aria-label={`显示图片 ${index + 1}`}
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
              </div>
            ) : (
              <div className="mb-5 flex h-60 w-full items-center justify-center rounded-lg bg-slate-100 text-slate-500 lg:h-64">
                暂无图片
              </div>
            )}

            {/* 详细信息区域 */}
            <div className="space-y-5 text-left">
              {/* 基本信息 */}
              <div className="flex items-start justify-between border-b pb-3">
                <div className="flex-1">
                  <span className="text-sm uppercase tracking-wide text-slate-500">{typeLabel}</span>
                  <h3 className="mt-1 text-xl font-bold text-slate-900">{card.name}</h3>
                  {card.address && (
                    <p className="mt-2 flex items-start gap-2 text-slate-600">
                      <span className="text-slate-400">📍</span>
                      {card.address}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <span className="text-xl font-bold text-orange-600">{priceLabel}</span>
                </div>
              </div>

              {/* 摘要 */}
              {card.summary && (
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="leading-relaxed text-slate-700">{card.summary}</p>
                </div>
              )}

              {/* 详细信息网格 */}
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {ratingText && (
                  <div className="rounded-lg border border-slate-200 bg-white p-3">
                    <dt className="mb-1 text-xs uppercase tracking-wide text-slate-500">⭐ 评分</dt>
                    <dd className="text-base font-semibold text-slate-900">{ratingText}</dd>
                  </div>
                )}
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <dt className="mb-1 text-xs uppercase tracking-wide text-slate-500">💰 价格</dt>
                  <dd className="text-base font-semibold text-slate-900">{priceLabel}</dd>
                </div>
                {distance && (
                  <div className="rounded-lg border border-slate-200 bg-white p-3">
                    <dt className="mb-1 text-xs uppercase tracking-wide text-slate-500">📏 距离</dt>
                    <dd className="text-base font-semibold text-slate-900">{distance}</dd>
                  </div>
                )}
                {openStatus && (
                  <div className="rounded-lg border border-slate-200 bg-white p-3">
                    <dt className="mb-1 text-xs uppercase tracking-wide text-slate-500">🕒 营业状态</dt>
                    <dd className="text-base font-semibold text-slate-900">{openStatus}</dd>
                  </div>
                )}
              </div>

              {/* 类型标签 */}
              {typeList.length > 0 && (
                <div>
                  <p className="mb-2 text-sm uppercase tracking-wide text-slate-500">餐厅类型</p>
                  <div className="flex flex-wrap gap-1.5">
                    {typeList.map((type, index) => (
                      <span
                        key={`type-${index}`}
                        className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
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
                  <p className="mb-2 text-sm uppercase tracking-wide text-slate-500">特色标签</p>
                  <div className="flex flex-wrap gap-1.5">
                    {card.tags.map((tag) => (
                      <span
                        key={`tag-${tag}`}
                        className="rounded-full border border-orange-400 px-3 py-1 text-xs font-medium text-orange-600"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 推荐理由 */}
              {card.why && card.why.length > 0 && (
                <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
                  <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-orange-800">
                    💡 为什么推荐这家
                  </p>
                  <ul className="space-y-1.5 text-sm text-slate-700">
                    {card.why.map((reason, index) => (
                      <li key={`reason-${index}`} className="flex items-start gap-2">
                        <span className="mt-1 text-orange-500">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="flex flex-col gap-3 pt-4 sm:flex-row">
                {card.deeplink && (
                  <a
                    href={card.deeplink}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 rounded-lg bg-orange-600 px-5 py-2.5 text-center text-sm font-medium text-white transition-colors hover:bg-orange-700"
                  >
                    📍 获取路线
                  </a>
                )}
                {!card.deeplink && card.google_maps_uri && (
                  <a
                    href={card.google_maps_uri}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 rounded-lg bg-orange-600 px-5 py-2.5 text-center text-sm font-medium text-white transition-colors hover:bg-orange-700"
                  >
                    📍 在 Google Maps 上查看
                  </a>
                )}
                <button
                  onClick={onBack}
                  className="flex-1 rounded-lg border-2 border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                >
                  返回列表
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const GENERIC_TYPES = new Set(["point_of_interest", "establishment", "food", "store", "health", "gym"]);
const GAP_PX = 16; // Tailwind gap-4 size in px
const RIGHT_SCROLL_EPSILON = 0.5;
const TAIL_PADDING_PX = 32;

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

export function RecommendationGrid({ payload, onRequestMore, disableRequestMore }: RecommendationGridProps) {
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  if (!payload.cards?.length) {
    return null;
  }

  const updateScrollState = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) {
      setCanScrollRight(false);
      return;
    }

    const { scrollLeft, scrollWidth, clientWidth } = container;
    const maxScrollLeft = Math.max(0, scrollWidth - clientWidth);
    const remaining = Math.max(0, maxScrollLeft - scrollLeft);
    setCanScrollRight(remaining > RIGHT_SCROLL_EPSILON);
  }, []);

  const scrollByCard = useCallback((direction: "left" | "right") => {
    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    const firstCard = container.querySelector("article") as HTMLElement | null;
    const baseWidth = firstCard?.getBoundingClientRect().width ?? container.getBoundingClientRect().width / 2;
    const amount = baseWidth + GAP_PX;

    container.scrollBy({
      left: direction === "left" ? -amount : amount,
      behavior: "smooth",
    });
    requestAnimationFrame(updateScrollState);
  }, [updateScrollState]);

  const handleScroll = useCallback(() => {
    updateScrollState();
  }, [updateScrollState]);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    handleScroll();

    const handleResize = () => handleScroll();
    window.addEventListener("resize", handleResize);

    if (typeof window !== "undefined" && "ResizeObserver" in window) {
      resizeObserverRef.current = new ResizeObserver(() => handleScroll());
      resizeObserverRef.current.observe(container);
    }

    return () => {
      window.removeEventListener("resize", handleResize);
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
    };
  }, [handleScroll, payload.cards?.length]);

  useEffect(() => {
    handleScroll();
  }, [handleScroll, payload.cards]);

  // 查找选中的餐厅
  const selectedCard = selectedPlaceId
    ? payload.cards.find((card) => card.place_id === selectedPlaceId)
    : null;

  // 如果选中了餐厅，显示详情页
  if (selectedCard) {
    return <RestaurantDetails card={selectedCard} onBack={() => setSelectedPlaceId(null)} />;
  }

  // 否则显示卡片列表
  return (
    <div className="space-y-4">
      <div className="relative mx-auto max-w-6xl">
        <div
          className="pointer-events-none absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-white via-white/80 to-transparent transition-opacity duration-200 sm:w-16"
          aria-hidden="true"
          style={{ opacity: canScrollRight ? 1 : 0 }}
        />
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="carousel-scroll flex gap-4 overflow-x-auto scroll-smooth pb-6 pl-4 pr-4 snap-x snap-mandatory sm:pl-6 sm:pr-6 lg:pl-8 lg:pr-8"
        >
          {payload.cards.map((card) => (
            <article
              key={card.place_id}
              onClick={(event) => {
                const container = scrollContainerRef.current;
                if (container) {
                  const cardElement = event.currentTarget as HTMLElement;
                  const containerRect = container.getBoundingClientRect();
                  const cardRect = cardElement.getBoundingClientRect();
                  const currentLeft = container.scrollLeft;
                  const cardCenter = cardRect.left + cardRect.width / 2;
                  const containerCenter = containerRect.left + containerRect.width / 2;
                  const delta = cardCenter - containerCenter;
                  container.scrollTo({ left: currentLeft + delta, behavior: "smooth" });
                }
                setSelectedPlaceId(card.place_id);
              }}
              className="flex h-full w-[260px] flex-shrink-0 flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all hover:border-orange-300 hover:shadow-lg snap-start sm:w-[300px] md:w-[320px] xl:w-[360px]"
            >
              <CardImage card={card} />
              <CardBody card={card} />
            </article>
          ))}
          {onRequestMore ? (
            <div className="flex h-full w-[260px] flex-shrink-0 items-center justify-center snap-start sm:w-[300px] md:w-[320px] xl:w-[360px]">
              <button
                type="button"
                onClick={() => {
                  if (!disableRequestMore && onRequestMore) {
                    void onRequestMore();
                  }
                }}
                disabled={disableRequestMore}
                className={
                  "inline-flex h-100 min-w-[110px] items-center justify-center gap-2 rounded-full border border-brand/50 bg-white px-4 text-sm font-semibold text-brand transition hover:bg-brand/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand " +
                  (disableRequestMore ? "cursor-not-allowed opacity-60" : "")
                }
              >
                <span>More restaurants</span>
                <span aria-hidden="true">→</span>
              </button>
            </div>
          ) : null}
          <div className="flex h-full w-14 flex-shrink-0 items-center justify-center snap-start sm:w-16">
            <button
              type="button"
              aria-label="Scroll right"
              onClick={() => scrollByCard("right")}
              disabled={!canScrollRight}
              className={
                "inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 bg-white text-xl text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand " +
                (canScrollRight ? "" : "cursor-not-allowed opacity-40")
              }
            >
              <span aria-hidden="true">›</span>
            </button>
          </div>
          <div aria-hidden="true" className="flex-shrink-0" style={{ width: `${TAIL_PADDING_PX}px` }} />
        </div>
      </div>
      {payload.rationale ? (
        <p className="rounded-lg border border-dashed border-brand/40 bg-brand/5 p-4 text-sm text-slate-700">
          {payload.rationale}
        </p>
      ) : null}
    </div>
  );
}
