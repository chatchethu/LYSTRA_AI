import { fetchApi } from "./client";

export const filesClient = {
  upload: (formData: FormData) => fetchApi("/api/v1/files/upload", {
    method: "POST",
    body: formData,
  }),
};
