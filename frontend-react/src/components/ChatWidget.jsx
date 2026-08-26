import { useEffect, useRef, useState } from "react";
import { useChat } from "../context/ChatContext";
import { parseAnswer, CLAIM_TAG_MAP } from "../helpers";

export default function ChatWidget() {
  const { open, closeChat, activeProductName, messages, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const messagesRef = useRef(null);
  const inputRef = useRef(null);
  const panelRef = useRef(null);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") closeChat();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, closeChat]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query) return;
    setInput("");
    setSending(true);
    await sendMessage(query);
    setSending(false);
  };

  return (
    <>
      <div
        className={`chat-panel${open ? "" : " hidden"}`}
        role="dialog"
        aria-modal="false"
        aria-label="NutriMart Assistant chat"
        ref={panelRef}
      >
        <div className="chat-header">
          <div className="chat-header-title">
            <span className="chat-header-app">NutriMart Assistant</span>
            {activeProductName && <span className="chat-header-product">{activeProductName}</span>}
          </div>
          <button className="close-btn" onClick={closeChat} aria-label="Close chat">
            &times;
          </button>
        </div>

        <div className="chat-messages" ref={messagesRef} role="log" aria-live="polite" aria-label="Conversation">
          {messages.length === 0 && (
            <div className="chat-empty-state">
              {activeProductName
                ? `💬 Ask me anything about ${activeProductName} — ingredients, allergens, nutrition, FSSAI compliance.`
                : "💬 Ask me anything about this product."}
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`msg ${msg.role}${msg.kind === "pending" ? " pending" : ""}${msg.kind === "error" || msg.kind === "rate_limited" ? " error" : ""}`}
            >
              <span className="sr-only">{msg.role === "user" ? "You said: " : "Assistant: "}</span>
              {msg.kind === "rate_limited" && (
                <>
                  <span className="msg-error-icon" aria-hidden="true">⏳</span>
                  You're sending messages a bit fast — please wait {msg.retryAfter ? `${msg.retryAfter}s` : "a moment"} and try again.
                </>
              )}
              {msg.kind === "pending" && (
                <span className="typing-dots" aria-label="Assistant is typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              )}
              {msg.kind === "error" && (
                <>
                  <span className="msg-error-icon" aria-hidden="true">⚠</span>
                  Sorry, something went wrong reaching the assistant. Is the backend running?
                </>
              )}
              {msg.kind === "text" && msg.text}
              {msg.kind === "streaming" && (
                <>
                  {msg.text}
                  <span className="stream-cursor" aria-hidden="true" />
                </>
              )}
              {msg.kind === "answer" && (
                <>
                  {parseAnswer(msg.text).map((part, i) =>
                    part.type === "tag" ? (
                      <span key={i} className={`claim-tag ${CLAIM_TAG_MAP[part.value] || "fact"}`}>
                        {part.value}
                      </span>
                    ) : (
                      <span key={i}>{part.value}</span>
                    )
                  )}
                </>
              )}
            </div>
          ))}
        </div>

        <form className="chat-form" onSubmit={handleSubmit}>
          <label htmlFor="chat-input" className="sr-only">
            Ask a question
          </label>
          <input
            id="chat-input"
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about ingredients, allergens, safety..."
            autoComplete="off"
          />
          <button type="submit" disabled={sending}>
            Send
          </button>
        </form>
      </div>
    </>
  );
}
