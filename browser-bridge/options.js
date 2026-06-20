const proxyUrl = document.querySelector("#proxy-url");
const bridgeToken = document.querySelector("#bridge-token");
const status = document.querySelector("#status");

chrome.storage.local.get({ proxyUrl: "http://127.0.0.1:9000", bridgeToken: "" }, (settings) => {
  proxyUrl.value = settings.proxyUrl;
  bridgeToken.value = settings.bridgeToken;
});

document.querySelector("#save").addEventListener("click", () => {
  chrome.storage.local.set({ proxyUrl: proxyUrl.value.trim(), bridgeToken: bridgeToken.value.trim() }, () => {
    status.textContent = "Saved";
    setTimeout(() => { status.textContent = ""; }, 1500);
  });
});
