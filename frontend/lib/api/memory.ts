import { fetchApi } from "./client";
import { Memory } from "../../types/memory";

export const memoryClient = {
  list: (filter?: string) => fetchApi<Memory[]>(`/api/v1/memory${filter ? `?memory_type=${filter}` : ""}`),
  delete: (id: string) => fetchApi(`/api/v1/memory/${id}`, { method: "DELETE" }),
};
