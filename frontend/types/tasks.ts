export interface Task {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
}
