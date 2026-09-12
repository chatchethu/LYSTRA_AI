import { fetchApi } from "./client";
import { Tool } from "../../types/tools";

export const toolsClient = {
  list: () => fetchApi<Tool[]>("/api/v1/tools"),
};
