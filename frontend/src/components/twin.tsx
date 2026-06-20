"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, ChevronDown } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function Twin() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowScrollButton(false);
  };

  const handleMessagesScroll = () => {
    const el = messagesContainerRef.current;
    if (!el) return;
    setShowScrollButton(el.scrollHeight - el.scrollTop - el.clientHeight > 80);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: input,
            session_id: sessionId || undefined,
          }),
        }
      );

      if (!response.ok) throw new Error("Failed to send message");

      let assistantMessageId: string | null = null;
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let receivedSessionId = sessionId;
      let buffer = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.session_id && !receivedSessionId) {
                  setSessionId(data.session_id);
                  receivedSessionId = data.session_id;
                }

                if (data.content) {
                  if (!assistantMessageId) {
                    setIsStreaming(true);
                    assistantMessageId = (Date.now() + 1).toString();
                    setMessages((prev) => [
                      ...prev,
                      {
                        id: assistantMessageId!,
                        role: "assistant",
                        content: data.content,
                        timestamp: new Date(),
                      },
                    ]);
                  } else {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === assistantMessageId
                          ? { ...msg, content: msg.content + data.content }
                          : msg
                      )
                    );
                  }
                }

                if (data.error) throw new Error(data.error);

                if (data.done) {
                  setIsLoading(false);
                  setIsStreaming(false);
                  return;
                }
              } catch (e) {
                console.error("Error parsing SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Card className="relative flex h-full flex-col overflow-hidden shadow-2xl shadow-black/40">
      <CardHeader className="border-b border-border bg-secondary/70">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-[#fbf1c7]">
              <Bot className="h-6 w-6 text-primary" />
              Tanmay&apos;s Digital Twin
            </CardTitle>
            <CardDescription>Ask about Tanmay&apos;s work, projects, and technical experience.</CardDescription>
          </div>
          <Badge className="gap-1">
            <Sparkles className="h-3 w-3" /> Live chat
          </Badge>
        </div>
      </CardHeader>

      <CardContent
        ref={messagesContainerRef}
        onScroll={handleMessagesScroll}
        className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 pb-4 pt-6"
      >
        {messages.length === 0 && (
          <div className="mx-auto mt-16 max-w-sm rounded-xl border border-border bg-muted/60 p-6 text-center text-muted-foreground">
            <Bot className="mx-auto mb-3 h-12 w-12 text-primary" />
            <p className="font-medium text-foreground">Hello! I&apos;m Tanmay&apos;s Digital Twin.</p>
            <p className="mt-2 text-sm">Ask me anything about Tanmay.</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {message.role === "assistant" && (
              <Avatar>
                <Bot className="h-5 w-5 text-primary" />
              </Avatar>
            )}

            <div className={`flex max-w-[75%] flex-col ${message.role === "user" ? "items-end text-right" : "items-start text-left"}`}>
              <div
                className={`w-fit max-w-full rounded-xl border px-3 py-2 shadow-sm ${
                  message.role === "user"
                    ? "border-accent/50 bg-accent text-accent-foreground"
                    : "border-border bg-muted text-foreground"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
              </div>
              <p className="mt-1 px-1 text-xs text-muted-foreground">
                {message.timestamp.toLocaleTimeString(undefined, {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>

            {message.role === "user" && (
              <Avatar className="bg-accent">
                <User className="h-5 w-5 text-accent-foreground" />
              </Avatar>
            )}
          </div>
        ))}

        {isLoading && !isStreaming && (
          <div className="flex justify-start gap-3">
            <Avatar>
              <Bot className="h-5 w-5 text-primary" />
            </Avatar>
            <div className="rounded-xl border border-border bg-muted p-3">
              <div className="flex space-x-2">
                <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground delay-100" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground delay-200" />
              </div>
            </div>
          </div>
        )}

        {showScrollButton && (
          <div className="sticky bottom-0 flex justify-center">
            <button
              className="flex h-8 w-8 items-center justify-center rounded-full border border-white/20 bg-background/40 text-white shadow-sm backdrop-blur hover:bg-white/10"
              onClick={scrollToBottom}
              aria-label="Scroll to bottom"
            >
              <ChevronDown className="h-5 w-5" />
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </CardContent>

      <CardFooter className="border-t border-border bg-secondary/60 p-2">
        <div className="flex w-full items-center gap-2">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask about Tanmay..."
            disabled={isLoading}
            className="h-9"
          />
          <Button className="h-9 shrink-0 px-3" onClick={sendMessage} disabled={!input.trim() || isLoading} aria-label="Send message">
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
