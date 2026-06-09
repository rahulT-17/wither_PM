import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const distDir = path.join(projectRoot, "dist");
const indexFile = path.join(distDir, "index.html");
const port = Number(process.env.PORT ?? 5173);

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".js":
      return "text/javascript; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".json":
      return "application/json; charset=utf-8";
    case ".svg":
      return "image/svg+xml";
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".webp":
      return "image/webp";
    default:
      return "application/octet-stream";
  }
}

async function sendFile(response, filePath) {
  const data = await readFile(filePath);
  response.statusCode = 200;
  response.setHeader("Content-Type", contentType(filePath));
  response.end(data);
}

export async function startServer() {
  if (!existsSync(indexFile)) {
    throw new Error(`Build output not found at ${indexFile}. Run npm run build first.`);
  }

  const server = createServer(async (request, response) => {
    try {
      const requestUrl = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);
      let pathname = decodeURIComponent(requestUrl.pathname);

      if (pathname === "/" || !path.extname(pathname)) {
        if (pathname === "/") {
          pathname = "/index.html";
        }
      }

      const resolvedPath = path.resolve(distDir, `.${pathname}`);
      if (!resolvedPath.startsWith(distDir)) {
        response.statusCode = 403;
        response.end("Forbidden");
        return;
      }

      if (existsSync(resolvedPath)) {
        await sendFile(response, resolvedPath);
        return;
      }

      if (!path.extname(pathname)) {
        const jsPath = `${resolvedPath}.js`;
        if (existsSync(jsPath)) {
          await sendFile(response, jsPath);
          return;
        }
      }

      await sendFile(response, indexFile);
    } catch (error) {
      response.statusCode = 500;
      response.end(error instanceof Error ? error.message : "Internal server error");
    }
  });

  await new Promise((resolve) => {
    server.listen(port, "0.0.0.0", () => {
      console.log(`Serving ${distDir} on http://localhost:${port}`);
      resolve();
    });
  });

  return server;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  startServer().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
