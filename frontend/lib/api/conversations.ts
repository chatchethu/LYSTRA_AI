import { fetchApi } from "./client";
import { Conversation, Message } from "../../types/chat";

export const conversationsClient = {
  list: () => fetchApi<Conversation[]>("/api/v1/conversations"),
  getMessages: (id: string, signal?: AbortSignal) =>
    fetchApi<Message[]>(`/api/v1/conversations/${id}/messages`, { signal }),
  delete: (id: string) => fetchApi(`/api/v1/conversations/${id}`, { method: "DELETE" }),
};
