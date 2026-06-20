(() => {
  const summaryPath = "/api/v0/users/get_user_summary";

  const publish = (payload) => {
    if (payload && typeof payload === "object") {
      window.postMessage({ source: "deepseek-platform-usage-bridge", payload }, "*");
    }
  };

  const isSummaryRequest = (input) => {
    const url = typeof input === "string" ? input : input?.url;
    return typeof url === "string" && url.includes(summaryPath);
  };

  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await originalFetch.apply(this, args);
    if (isSummaryRequest(args[0])) {
      response.clone().json().then(publish).catch(() => {});
    }
    return response;
  };

  const originalOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    if (isSummaryRequest(url)) {
      this.addEventListener("load", () => {
        try {
          publish(JSON.parse(this.responseText));
        } catch {
          // The Usage page controls this response; ignore non-JSON failures.
        }
      });
    }
    return originalOpen.call(this, method, url, ...rest);
  };
})();
