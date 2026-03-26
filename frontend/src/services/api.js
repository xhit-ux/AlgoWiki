import axios from "axios";

const METHOD_OVERRIDE_HEADER = "X-HTTP-Method-Override";
const OVERRIDDEN_METHODS = new Set(["put", "patch", "delete"]);

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

function getRetryAfterSeconds(response) {
  const raw = response?.headers?.["retry-after"];
  const seconds = Number(raw);
  if (Number.isFinite(seconds) && seconds > 0) {
    return Math.ceil(seconds);
  }
  return null;
}

function normalizeRateLimitError(error) {
  const response = error?.response;
  if (!response || response.status !== 429) {
    return error;
  }

  const waitSeconds = getRetryAfterSeconds(response);
  const requestUrl = String(error?.config?.url || "");
  let detail = waitSeconds
    ? `Too many requests. Please retry in ${waitSeconds} seconds.`
    : "Too many requests. Please retry later.";

  if (requestUrl.includes("/auth/login/")) {
    detail = waitSeconds
      ? `Too many login attempts. Please retry in ${waitSeconds} seconds.`
      : "Too many login attempts. Please retry later.";
  } else if (requestUrl.includes("/auth/register")) {
    detail = waitSeconds
      ? `Too many registration attempts. Please retry in ${waitSeconds} seconds.`
      : "Too many registration attempts. Please retry later.";
  }

  if (typeof response.data === "string") {
    response.data = { detail };
  } else if (response.data && typeof response.data === "object") {
    response.data = {
      ...response.data,
      detail,
    };
  } else {
    response.data = { detail };
  }

  if (waitSeconds) {
    response.data.retry_after_seconds = waitSeconds;
  }
  return error;
}

api.interceptors.request.use((config) => {
  const method = String(config.method || "get").toLowerCase();
  if (OVERRIDDEN_METHODS.has(method)) {
    config.headers = {
      ...(config.headers || {}),
      [METHOD_OVERRIDE_HEADER]: method.toUpperCase(),
    };
    config.method = "post";
  }

  const token = localStorage.getItem("algowiki_token");
  if (token) {
    config.headers = {
      ...(config.headers || {}),
    };
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error?.config;
    if (!config) throw error;

    const status = error?.response?.status || 0;
    if (status === 429) {
      throw normalizeRateLimitError(error);
    }

    const method = (config.method || "get").toLowerCase();

    if (status === 401) {
      const hasToken = Boolean(localStorage.getItem("algowiki_token"));
      if (hasToken) {
        localStorage.removeItem("algowiki_token");
        localStorage.removeItem("algowiki_user");
        window.dispatchEvent(new CustomEvent("algowiki:auth-invalid"));
      }

      // Public GET endpoints should recover after dropping stale token.
      if (method === "get" && hasToken && !config.__retryWithoutAuth) {
        const retryConfig = {
          ...config,
          __retryWithoutAuth: true,
          headers: { ...(config.headers || {}) },
        };
        if (retryConfig.headers.Authorization) {
          delete retryConfig.headers.Authorization;
        }
        return api.request(retryConfig);
      }
      throw error;
    }

    if ((config.method || "get").toLowerCase() !== "get") throw error;
    if (config.__retryOnce) throw error;

    const isNetworkError = !error?.response;
    const canRetry = isNetworkError || status >= 500;
    if (!canRetry) throw error;

    config.__retryOnce = true;
    await new Promise((resolve) => window.setTimeout(resolve, 250));
    return api.request(config);
  }
);

export default api;
