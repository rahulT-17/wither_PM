import { buildFrontend } from "./build.mjs";
import { startServer } from "./serve.mjs";

await buildFrontend();
await startServer();
