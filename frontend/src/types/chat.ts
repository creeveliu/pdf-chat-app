import type { AskContext, Citation } from "@/lib/api";

export type BaseChatMessage = {
  id: string;
  content: string;
  createdAt: string;
};

export type SystemChatMessage = BaseChatMessage & {
  role: "system";
  tone?: "default" | "success" | "error";
};

export type UserChatMessage = BaseChatMessage & {
  role: "user";
};

export type AssistantChatMessage = BaseChatMessage & {
  role: "assistant";
  citations: Citation[];
  contexts: AskContext[];
  isStreaming?: boolean;
};

export type ChatMessage = SystemChatMessage | UserChatMessage | AssistantChatMessage;
