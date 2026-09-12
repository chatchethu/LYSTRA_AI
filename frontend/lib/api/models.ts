import { fetchApi } from "./client";

export const modelsClient = {
  list: () => fetchApi<any[]>("/api/v1/models")
};
