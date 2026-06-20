const bridgeSource = "deepseek-platform-usage-bridge";
const defaultSettings = {
  proxyUrl: "http://127.0.0.1:9000",
  bridgeToken: ""
};

const hook = document.createElement("script");
hook.src = chrome.runtime.getURL("page-hook.js");
hook.onload = () => hook.remove();
(document.head || document.documentElement).appendChild(hook);

window.addEventListener("message", async (event) => {
  if (event.source !== window || event.data?.source !== bridgeSource) {
    return;
  }
  const settings = await chrome.storage.local.get(defaultSettings);
  if (!settings.bridgeToken) {
    return;
  }
  fetch(`${settings.proxyUrl.replace(/\/$/, "")}/v1/platform-summary`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-DeepSeek-Bridge-Token": settings.bridgeToken
    },
    body: JSON.stringify(event.data.payload)
  }).catch(() => {});
});
