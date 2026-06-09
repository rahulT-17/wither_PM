import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { copyFile, mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { build as esbuild } from "esbuild";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const distDir = path.join(projectRoot, "dist");
const apiBaseUrl = process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

function buildHtml() {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="WITHER - Bloomberg-inspired weather intelligence dashboard" />
    <title>WITHER</title>
    <link rel="stylesheet" href="/styles.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/main.js"></script>
  </body>
</html>
`;
}

export async function buildFrontend() {
  await rm(distDir, { recursive: true, force: true });
  await mkdir(distDir, { recursive: true });

  execFileSync(
    process.execPath,
    [path.join(projectRoot, "node_modules", "typescript", "bin", "tsc"), "-p", path.join(projectRoot, "tsconfig.build.json")],
    { stdio: "inherit" },
  );

  await esbuild({
    entryPoints: [path.join(projectRoot, "src", "main.tsx")],
    bundle: true,
    format: "esm",
    platform: "browser",
    target: ["es2020"],
    outfile: path.join(distDir, "main.js"),
    sourcemap: true,
    define: {
      "import.meta.env": JSON.stringify({
        VITE_API_BASE_URL: apiBaseUrl,
      }),
    },
    logLevel: "info",
  });

  const stylesheetSource = path.join(projectRoot, "src", "styles.css");
  const stylesheetTarget = path.join(distDir, "styles.css");
  if (existsSync(stylesheetSource)) {
    await copyFile(stylesheetSource, stylesheetTarget);
  }

  await writeFile(path.join(distDir, "index.html"), buildHtml(), "utf8");

  console.log(`Built frontend to ${distDir}`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  buildFrontend().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
