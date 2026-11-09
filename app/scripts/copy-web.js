// Copies the shared app screens from the server into the Android app and writes config.js.
// SERVER_URL = default club server baked into the app (optional — users can enter it on first launch)
// APP_VERSION = build number; the app shows "update available" when the Pi has a newer one.
const fs = require("fs"), path = require("path");
const www = path.join(__dirname, "..", "www");
fs.mkdirSync(www, { recursive: true });
fs.copyFileSync(path.join(__dirname, "..", "..", "server", "static", "index.html"), path.join(www, "index.html"));
const server = (process.env.SERVER_URL || "").trim().replace(/\/+$/, "");
const version = parseInt(process.env.APP_VERSION || "1", 10) || 1;
fs.writeFileSync(path.join(www, "config.js"),
  `window.SPEARHEAD_SERVER=${JSON.stringify(server)};window.SPEARHEAD_VERSION=${version};\n`);
console.log(`www ready (server: ${server || "asked on first launch"}, build ${version})`);
