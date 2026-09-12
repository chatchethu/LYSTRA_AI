import { fetchApi } from "./client";

export const authClient = {
  login: (formData: URLSearchParams) =>
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
      credentials: "include", // Critical: lets browser store the HttpOnly cookies
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Login failed");
      }
      return res.json();
    }),

  register: (data: any) =>
    fetchApi("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () => fetchApi("/api/v1/auth/me"),

  logout: () =>
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
    }),
};
