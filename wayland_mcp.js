#!/usr/bin/env node

// Node.js MCP bridge for wayland_mcp Python server with logging

import fetch from "node-fetch";
import fs from "fs";
import readline from "readline";

function log(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  try {
    fs.appendFileSync("wayland_mcp.log", logMessage);
  } catch (e) {
    // ignore logging errors
  }
  console.error(logMessage.trim());
}

async function handleRequest(req) {
  const { tool, arguments: args } = req;
  log(`Received request: ${JSON.stringify(req)}`);

  try {
    if (tool === "execute_task") {
      log(`Forwarding to Python server: ${JSON.stringify(args)}`);
      const response = await fetch("http://127.0.0.1:5000/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args),
      });
      const data = await response.json();
      log(`Response from Python server: ${JSON.stringify(data)}`);
      return { result: data };
    } else if (tool === "capture_screenshot") {
      log("capture_screenshot not implemented");
      return { error: "capture_screenshot not implemented" };
    } else if (tool === "compare_images") {
      log("compare_images not implemented");
      return { error: "compare_images not implemented" };
    } else {
      log(`Unknown tool: ${tool}`);
      return { error: `Unknown tool: ${tool}` };
    }
  } catch (e) {
    log(`Error handling request: ${e.stack || e.message}`);
    return { error: e.message };
  }
}

async function main() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false,
  });

  rl.on("line", async (line) => {
    try {
      log(`Received MCP line: ${line}`);
      const req = JSON.parse(line);
      const res = await handleRequest(req);
      const output = JSON.stringify(res);
      log(`Sending MCP response: ${output}`);
      process.stdout.write(output + "\n");
    } catch (e) {
      log(`Error processing MCP line: ${e.stack || e.message}`);
      const errorOutput = JSON.stringify({ error: e.message });
      process.stdout.write(errorOutput + "\n");
    }
  });
}

main();