import * as React from "react";
import { useAsk } from "../api/use-ask";
import type { ChatMessage, AskStyle } from "../types";
import { useViewState } from "@/features/areas";
import { ApiError } from "@/lib/api/errors";

export function useConversation() {
  const { area } = useViewState();
  const askMutation = useAsk();

  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [style, setStyle] = React.useState<AskStyle>("standard");
  const [cooldown, setCooldown] = React.useState<number | null>(null);

  // Countdown timer for 429 rate limiting
  React.useEffect(() => {
    if (cooldown === null || cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev && prev > 1 ? prev - 1 : null));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const sendMessage = React.useCallback(
    async (customText?: string) => {
      const textToSend = (customText !== undefined ? customText : input).trim();
      if (!textToSend) return;
      if (textToSend.length > 500) return;

      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `asst-${Date.now() + 1}`;
      const now = new Date().toISOString();

      const userMsg: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: textToSend,
        timestamp: now,
      };

      const pendingMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        timestamp: now,
        isPending: true,
      };

      setMessages((prev) => [...prev, userMsg, pendingMsg]);
      if (customText === undefined) {
        setInput("");
      }

      try {
        const envelope = await askMutation.mutateAsync({
          question: textToSend,
          area_id: area,
          style,
        });

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: envelope.data.answer,
                  response: envelope.data,
                  isPending: false,
                }
              : m
          )
        );
      } catch (err) {
        let isRateLimited = false;
        let retryAfterSeconds = 60;
        let errorMessage = "Failed to communicate with PyroScope assistant";

        if (err instanceof ApiError) {
          if (err.status === 429) {
            isRateLimited = true;
            retryAfterSeconds = err.retryAfter || 60;
            setCooldown(retryAfterSeconds);
            errorMessage = `Rate limited. Please wait ${retryAfterSeconds} seconds before querying again.`;
          } else {
            errorMessage = err.message;
          }
        } else if (err instanceof Error) {
          errorMessage = err.message;
        }

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: errorMessage,
                  error: errorMessage,
                  isPending: false,
                  isRateLimited,
                  retryAfterSeconds: isRateLimited ? retryAfterSeconds : undefined,
                }
              : m
          )
        );
      }
    },
    [input, area, style, askMutation]
  );

  const retryLast = React.useCallback(() => {
    // Find last user message
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser) {
      sendMessage(lastUser.content);
    }
  }, [messages, sendMessage]);

  const clearConversation = React.useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    input,
    setInput,
    style,
    setStyle,
    isSubmitting: askMutation.isPending,
    cooldown,
    sendMessage,
    retryLast,
    clearConversation,
  };
}
