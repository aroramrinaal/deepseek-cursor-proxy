# DeepSeek Platform Usage Bridge

This experimental Chrome extension forwards the JSON response that DeepSeek's
own Usage page receives to the local proxy. It does not read, save, or transmit
the DeepSeek Platform bearer token, cookies, or API key.

## Install

1. Start the proxy: `deepseek start`.
2. Print the local bridge key: `deepseek bridge-key`.
3. In Chrome, open `chrome://extensions`, enable **Developer mode**, and choose
   **Load unpacked**. Select this `browser-bridge` folder.
4. Open the extension's **Details** page, then **Extension options**. Paste the
   local bridge key and leave the proxy URL as `http://127.0.0.1:9000`.
5. Open and refresh `https://platform.deepseek.com/usage` while signed in.
6. Run `deepseek stats` to display the live platform summary.

The latest summary stays in proxy memory only. Refresh the DeepSeek Usage page
after restarting the proxy.
