import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { postChat } from "../api";

const ChatContext = createContext(null);

// Timestamp-prefixed so ids stay unique across a page reload too — a
// restored thread (see loadInitialThreads below) already contains ids
// from a previous session's counter, and a plain per-session counter
// starting back at 0 would collide with those and duplicate React keys.
let idCounter = 0;
function uid() {
  idCounter += 1;
  return `m${Date.now()}-${idCounter}`;
}

function newSessionId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `sess-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

// One thread (message history + its own backend session_id) PER PRODUCT,
// not one flat conversation for the whole tab. Before this, every "Ask
// about this" click reused the same session_id/messages array regardless
// of which product you'd been asking about, so a Cadbury Dairy Milk
// question and an Amul Dark Chocolate question landed in the same
// scrolling thread with nothing marking where one ended and the other
// began — and worse, the backend's conversation/state.py memory (known
// facts, last topic) carried over between genuinely unrelated products
// too, since it was one session_id for both. Keying by product_id fixes
// both: each product gets its own message list AND its own session_id,
// so backend follow-up resolution never mixes context across products.
// A product with no id (defensive only — every real call site passes one,
// see pages/ProductPage.jsx and components/ProductCard.jsx) falls back to
// a shared "__general__" bucket.
const GENERAL_KEY = "__general__";

function threadKey(productId) {
  return productId || GENERAL_KEY;
}

function emptyThread() {
  return { messages: [], sessionId: newSessionId() };
}

// Same cosmetic client-side persistence pattern as CartContext/
// RecentlyViewedContext — localStorage only, no server-side history.
// Persisting session_id alongside each thread's messages is a real bonus,
// not just cosmetic: api/session_store.py's conversation memory is
// in-memory on the BACKEND process, which survives a frontend page
// refresh just fine (only a backend restart clears it) — so keeping the
// same session_id after a refresh means follow-up resolution
// (conversation/resolve.py) keeps working across the refresh too, not
// just the message bubbles looking persisted.
const STORAGE_KEY = "nutrimart_chat_threads";

// Only terminal message kinds are meaningful across a reload — a
// "pending"/"streaming" bubble reflects an in-flight request tied to this
// tab's JS runtime (the setInterval reveal, the fetch promise), which a
// reload always kills. Restoring one as-is would freeze a permanent
// "..." typing indicator with no request ever coming back to resolve it.
function sanitizeMessages(messages) {
  if (!Array.isArray(messages)) return [];
  return messages.filter(
    (m) => m && (m.kind === "text" || m.kind === "answer" || m.kind === "error" || m.kind === "rate_limited")
  );
}

function loadInitialThreads() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    if (!parsed || typeof parsed !== "object") return {};
    const result = {};
    for (const [key, thread] of Object.entries(parsed)) {
      if (!thread || typeof thread !== "object") continue;
      result[key] = {
        sessionId: typeof thread.sessionId === "string" ? thread.sessionId : newSessionId(),
        messages: sanitizeMessages(thread.messages),
      };
    }
    return result;
  } catch {
    return {};
  }
}

// Groq's response arrives as one complete string (the pipeline's
// groundedness check needs the full answer before it can annotate a claim,
// so true token-by-token SSE streaming isn't a fit here — see
// generation/groundedness.py). This instead reveals the already-complete
// answer progressively on the client, purely for a smoother, more "live"
// feel; claim-tag/source-panel rendering only kicks in once the reveal
// finishes, so the regex-based claim parsing never runs against a
// truncated mid-tag string.
const REVEAL_TICK_MS = 20;
const REVEAL_TOTAL_TICKS = 40;

function revealAnswer(fullText, onTick, onDone) {
  const charsPerTick = Math.max(3, Math.ceil(fullText.length / REVEAL_TOTAL_TICKS));
  let i = 0;
  const timer = setInterval(() => {
    i += charsPerTick;
    if (i >= fullText.length) {
      clearInterval(timer);
      onDone();
    } else {
      onTick(fullText.slice(0, i));
    }
  }, REVEAL_TICK_MS);
  return timer;
}

export function ChatProvider({ children }) {
  const [open, setOpen] = useState(false);
  const [activeProductId, setActiveProductId] = useState(null);
  const [activeProductName, setActiveProductName] = useState(null);
  const [threads, setThreads] = useState(loadInitialThreads);

  useEffect(() => {
    try {
      const toSave = {};
      for (const [key, thread] of Object.entries(threads)) {
        toSave[key] = { sessionId: thread.sessionId, messages: sanitizeMessages(thread.messages) };
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
    } catch {
      // Storage unavailable — threads still work in-memory for this tab.
    }
  }, [threads]);

  const activeKey = threadKey(activeProductId);
  const activeThread = threads[activeKey];
  const messages = activeThread ? activeThread.messages : [];

  const openChat = useCallback((productId, productName) => {
    const key = threadKey(productId);
    setThreads((t) => (t[key] ? t : { ...t, [key]: emptyThread() }));
    setActiveProductId(productId || null);
    setActiveProductName(productName || null);
    setOpen(true);
  }, []);

  const closeChat = useCallback(() => setOpen(false), []);

  const updateThreadMessages = useCallback((key, updater) => {
    setThreads((t) => {
      const current = t[key] || emptyThread();
      return { ...t, [key]: { ...current, messages: updater(current.messages) } };
    });
  }, []);

  const sendMessage = useCallback(
    async (query) => {
      const key = activeKey;
      const sessionId = (threads[key] || emptyThread()).sessionId;
      const userMsg = { id: uid(), role: "user", kind: "text", text: query };
      const pendingId = uid();
      updateThreadMessages(key, (m) => [...m, userMsg, { id: pendingId, role: "bot", kind: "pending" }]);

      try {
        const data = await postChat(query, activeProductId, sessionId);
        const meta = {
          route: data.route,
          sources: data.sources || [],
          confidence: data.confidence,
          topScore: data.top_score,
        };

        updateThreadMessages(key, (m) =>
          m.map((msg) => (msg.id === pendingId ? { id: pendingId, role: "bot", kind: "streaming", text: "" } : msg))
        );

        revealAnswer(
          data.answer,
          (partial) => {
            updateThreadMessages(key, (m) => m.map((msg) => (msg.id === pendingId ? { ...msg, text: partial } : msg)));
          },
          () => {
            updateThreadMessages(key, (m) =>
              m.map((msg) => (msg.id === pendingId ? { id: pendingId, role: "bot", kind: "answer", text: data.answer, ...meta } : msg))
            );
          }
        );
      } catch (err) {
        // api.js::postChat() throws "RATE_LIMITED:<seconds>" specifically
        // for a 429 — surfaced as its own kind so it doesn't read as
        // "the backend is down" (a real, distinct case a user can act on
        // differently: wait a bit, vs. the generic apology text).
        const isRateLimited = err instanceof Error && err.message.startsWith("RATE_LIMITED:");
        const retryAfter = isRateLimited ? err.message.split(":")[1] : null;
        updateThreadMessages(key, (m) =>
          m.map((msg) =>
            msg.id === pendingId
              ? { id: pendingId, role: "bot", kind: isRateLimited ? "rate_limited" : "error", retryAfter }
              : msg
          )
        );
      }
    },
    [activeKey, activeProductId, threads, updateThreadMessages]
  );

  const value = useMemo(
    () => ({ open, openChat, closeChat, activeProductId, activeProductName, messages, sendMessage }),
    [open, openChat, closeChat, activeProductId, activeProductName, messages, sendMessage]
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  return useContext(ChatContext);
}
