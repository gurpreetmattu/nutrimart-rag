import { useCallback, useEffect, useRef, useState } from "react";
import { useProducts } from "../context/ProductsContext";
import { categoryMeta } from "../categoryMeta";

// Cosmetic only, same spirit as helpers.js's price jitter — no real
// promo/CMS backend exists, so slides are a small hand-picked list tied to
// categories that are actually in the catalog. Clicking one filters the
// grid below to that category rather than linking anywhere, since there's
// no dedicated landing page per promo. The big background glyph reuses
// categoryMeta's own icon set (same ones ProductMedia falls back to) so
// this doesn't need any new artwork.
const SLIDES = [
  { category: "chocolate_confectionery", headline: "Chocolate cravings? Sorted.", sub: "Up to 30% off top brands" },
  { category: "chips_namkeen", headline: "Snack o'clock", sub: "Chips & namkeen, delivered in minutes" },
  { category: "dairy", headline: "Fresh dairy, daily", sub: "Milk, curd & more at doorstep speed" },
  { category: "health_drink", headline: "Fuel your day", sub: "Health drinks & protein, restocked" },
];

const AUTO_ADVANCE_MS = 5000;

export default function PromoCarousel() {
  const { setCategory } = useProducts();
  const [index, setIndex] = useState(0);
  const timerRef = useRef(null);

  const resetTimer = useCallback(() => {
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setIndex((i) => (i + 1) % SLIDES.length), AUTO_ADVANCE_MS);
  }, []);

  useEffect(() => {
    resetTimer();
    return () => clearInterval(timerRef.current);
  }, [resetTimer]);

  const goTo = (i) => {
    setIndex(i);
    resetTimer();
  };

  const handleSlideClick = (slide) => {
    setCategory(slide.category);
    document.querySelector(".grid")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="promo-carousel">
      <div className="promo-track" style={{ transform: `translateX(-${index * 100}%)` }}>
        {SLIDES.map((slide) => {
          const meta = categoryMeta(slide.category);
          return (
            <button
              key={slide.category}
              className="promo-slide"
              style={{ background: `linear-gradient(135deg, ${meta.gradient[0]}, ${meta.gradient[1]})` }}
              onClick={() => handleSlideClick(slide)}
            >
              <svg
                viewBox="0 0 64 64"
                fill="white"
                className="promo-slide-icon"
                aria-hidden="true"
                dangerouslySetInnerHTML={{ __html: meta.icon }}
              />
              <div className="promo-slide-text">
                <div className="promo-slide-headline">{slide.headline}</div>
                <div className="promo-slide-sub">{slide.sub}</div>
                <span className="promo-slide-cta">Shop now →</span>
              </div>
            </button>
          );
        })}
      </div>
      <div className="promo-dots" role="tablist" aria-label="Promo slides">
        {SLIDES.map((slide, i) => (
          <button
            key={slide.category}
            className={`promo-dot${i === index ? " active" : ""}`}
            onClick={() => goTo(i)}
            role="tab"
            aria-selected={i === index}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
