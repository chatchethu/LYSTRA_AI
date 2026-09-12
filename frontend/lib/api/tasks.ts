import { fetchApi } from "./client";
import { Task } from "../../types/tasks";

export const tasksClient = {
  list: () => fetchApi<Task[]>("/api/v1/agent/tasks/"),
  get: (id: string) => fetchApi<Task>(`/api/v1/agent/tasks/${id}`),
  cancel: (id: string) => fetchApi(`/api/v1/agent/tasks/${id}/cancel`, { method: "POST" }),
  approve: (taskId: string, stepId: string) => fetchApi(`/api/v1/agent/tasks/${taskId}/approve/${stepId}`, { method: "POST" }),
  reject: (taskId: string, stepId: string) => fetchApi(`/api/v1/agent/tasks/${taskId}/reject/${stepId}`, { method: "POST" }),
};
