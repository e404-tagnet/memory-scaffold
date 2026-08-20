"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const { isLoggedIn, login, signup, logout } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"login" | "signup">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch("/api/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: userMsg }),
      });

      if (!res.ok) throw new Error("Chat failed");

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let reply = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          reply += decoder.decode(value);
          setMessages((prev) => {
            const rest = prev.filter((m) => m.role !== "assistant" || m.content !== reply);
            return [...rest, { role: "assistant", content: reply }];
          });
        }
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: " + (e as Error).message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-full max-w-sm p-6 bg-freyja-panel rounded-xl shadow-xl">
          <h1 className="text-2xl font-bold mb-6 text-freyja-accent">FREYJA</h1>
          <div className="flex gap-2 mb-4">
            <button
              className={`flex-1 py-2 rounded ${tab === "login" ? "bg-freyja-accent text-black" : "bg-gray-800"}`}
              onClick={() => setTab("login")}
            >
              Log In
            </button>
            <button
              className={`flex-1 py-2 rounded ${tab === "signup" ? "bg-freyja-accent text-black" : "bg-gray-800"}`}
              onClick={() => setTab("signup")}
            >
              Sign Up
            </button>
          </div>
          <input
            className="w-full mb-3 p-2 rounded bg-gray-900 border border-gray-700"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full mb-4 p-2 rounded bg-gray-900 border border-gray-700"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (tab === "login" ? login(username, password) : signup(username, password))}
          />
          <button
            className="w-full py-2 bg-freyja-teal text-black font-semibold rounded hover:opacity-90"
            onClick={() => (tab === "login" ? login(username, password) : signup(username, password))}
          >
            {tab === "login" ? "Log In" : "Create Account"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto p-4">
      <header className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold text-freyja-accent">FREYJA</h1>
        <button className="text-sm text-gray-400 hover:text-white" onClick={logout}>
          Log out
        </button>
      </header>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[80%] p-3 rounded-lg ${
              m.role === "user"
                ? "ml-auto bg-freyja-accent text-black"
                : "bg-freyja-panel text-gray-200"
            }`}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div className="bg-freyja-panel text-gray-400 p-3 rounded-lg max-w-[80%]">Thinking…</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <input
          className="flex-1 p-3 rounded-lg bg-freyja-panel border border-gray-700 text-white"
          placeholder="Say something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          disabled={loading}
        />
        <button
          className="px-6 py-3 bg-freyja-teal text-black font-semibold rounded-lg hover:opacity-90 disabled:opacity-50"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
