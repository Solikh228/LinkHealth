import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputPublicDir = path.resolve(__dirname, "..", ".output", "public");
const ssrPath = path.resolve(__dirname, "..", ".output", "server", "_ssr", "ssr.mjs");

async function generate() {
  if (!fs.existsSync(ssrPath)) {
    console.error("SSR entry not found:", ssrPath);
    process.exit(1);
  }
  const ssrUrl = pathToFileURL(ssrPath).href;
  const ssr = await import(ssrUrl);
  const fetchHandler = ssr.default?.fetch ?? ssr.fetch;
  if (!fetchHandler) {
    console.error("fetch handler not found in ssr.mjs");
    process.exit(1);
  }

  const res = await fetchHandler(new Request("http://localhost:8000/"));
  const html = await res.text();
  const targetFile = path.join(outputPublicDir, "index.html");
  fs.writeFileSync(targetFile, html, "utf-8");
  console.log(`[build] Successfully generated static ${targetFile} (${html.length} bytes)`);
}

generate().catch((err) => {
  console.error("Error generating static index.html:", err);
  process.exit(1);
});
