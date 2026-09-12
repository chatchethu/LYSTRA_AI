import { getApiUrl } from "./client";

export const chatClient = {
  streamUrl: () => `${getApiUrl()}/api/v1/chat/stream`,
  getStreamHeaders: () => ({
    "Content-Type": "application/json",
    // No Authorization header — authentication is via HttpOnly cookie (credentials: "include")
  }),
};
