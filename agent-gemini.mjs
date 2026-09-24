// agent-gemini.mjs — Phase 1: "Chat with your codebase" — Gemini edition
// Run with:  node agent-gemini.mjs "how does this project work?"
// Requires:  npm i @google/genai   +   GEMINI_API_KEY (or GOOGLE_API_KEY) env var

import { GoogleGenAI } from "@google/genai";
import fs from "node:fs";
import path from "node:path";

const apiKey = process.env.GEMINI_API_KEY ?? process.env.GOOGLE_API_KEY;
if (!apiKey) {
  throw new Error("Set GEMINI_API_KEY (or GOOGLE_API_KEY) before running this script.");
}

const ai = new GoogleGenAI({ apiKey });
const ROOT = process.cwd();
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// The API-key-specific list is more reliable than hard-coding model names: it
// only includes models this key/project can see.  The order below chooses the
// preferred available model first, then falls back to the rest.
const PREFERRED_MODELS = [
  "gemini-3.8-flash",
  "gemini-3.7-flash",
  "gemini-3.5-flash",
  "gemini-3.5-flash-lite",
  "gemini-3.6-flash",
  "gemini-3.1-flash-lite",
];

// These are general text models suitable for this function-calling code agent.
// Do not fall back to image, audio, TTS, research, or computer-use endpoints.
const AGENT_MODELS = [
  ...PREFERRED_MODELS,
  "gemini-2.5-flash",
  "gemini-2.5-pro",
  "gemini-flash-latest",
  "gemini-pro-latest",
];

async function getAvailableModels() {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(apiKey)}`,
  );

  if (!response.ok) {
    throw new Error(`Could not list Gemini models (${response.status}).`);
  }

  const { models = [] } = await response.json();
  const available = models
    .filter((model) => model.supportedGenerationMethods?.includes("generateContent"))
    .map((model) => model.name.replace(/^models\//, ""));

  return AGENT_MODELS.filter((model) => available.includes(model));
}

async function generateWithFallback(request, models, retries = 3) {
  for (const model of models) {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        return await ai.models.generateContent({ ...request, model });
      } catch (error) {
        const status = error.status;

        // This model is unavailable to this request or its quota is exhausted.
        if (status === 404 || status === 429) break;

        // Transient service failures can succeed with a short exponential retry.
        if ([408, 500, 502, 503, 504].includes(status)) {
          await sleep(2 ** attempt * 1000);
          continue;
        }

        throw error;
      }
    }
    console.warn(`Model ${model} failed; trying the next available model.`);
  }

  throw new Error("No available Gemini model could complete the request.");
}

function responseText(response) {
  return response.candidates?.[0]?.content?.parts
    ?.map((part) => part.text ?? "")
    .join("")
    .trim() ?? "";
}

/* ================================================================
   1. THE HANDS — unchanged. The model proposes, you dispose.
   ================================================================ */

function safePath(p) {
  const full = path.resolve(ROOT, p);
  if (!full.startsWith(ROOT)) throw new Error("Path escapes codebase root");
  return full;
}

function listFiles(dirPath = ".") {
  try {
    if (typeof dirPath !== "string") throw new TypeError("dirPath must be a string");
    return fs.readdirSync(safePath(dirPath), { withFileTypes: true })
      .map((e) => (e.isDirectory() ? e.name + "/" : e.name))
      .join("\n");
  } catch (e) { return "Error: " + e.message; }
}

function readFile(filePath) {
  try {
    if (typeof filePath !== "string" || !filePath) {
      throw new TypeError("filePath must be a non-empty string");
    }
    const content = fs.readFileSync(safePath(filePath), "utf8");
    return content.length > 8000
      ? content.slice(0, 8000) + "\n...[truncated]"
      : content;
  } catch (e) { return "Error: " + e.message; }
}

function searchCode(query) {
  try {
    if (typeof query !== "string" || !query.trim()) {
      throw new TypeError("query must be a non-empty string");
    }

    const matches = [];
    const normalizedQuery = query.toLowerCase();
    const SKIP = new Set(["node_modules", ".git", "dist", "build", ".next"]);
    (function walk(dir, depth) {
      if (depth > 4 || matches.length >= 10) return;
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (SKIP.has(entry.name)) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) walk(full, depth + 1);
        else if (/\.(js|ts|jsx|tsx|json|md|py|css|html)$/.test(entry.name)) {
          const lines = fs.readFileSync(full, "utf8").split("\n");
          lines.forEach((line, i) => {
            if (matches.length < 10 && line.toLowerCase().includes(normalizedQuery)) {
              matches.push(`${path.relative(ROOT, full)}:${i + 1}: ${line.trim()}`);
            }
          });
        }
      }
    })(ROOT, 0);
    return matches.length ? matches.join("\n") : "No matches found.";
  } catch (e) {
    return "Error: " + e.message;
  }
}

function runTool(name, args = {}) {
  switch (name) {
    case "list_files": return listFiles(args.dirPath ?? ".");
    case "read_file": return readFile(args.filePath);
    case "search_code": return searchCode(args.query);
    default: return "Error: Unknown tool";
  }
}

/* ================================================================
   2. THE TOOL CATALOG — same tools, different dialect:
   Gemini takes plain "functionDeclarations", no OpenAI-style
   { type: "function" } wrapper.
   ================================================================ */

const functionDeclarations = [
  {
    name: "list_files",
    description: "List files and folders at a path. Use FIRST when exploring an unknown codebase.",
    parameters: {
      type: "object",
      properties: {
        dirPath: { type: "string", description: "Directory path, e.g. '.' or 'src'" },
      },
    },
  },
  {
    name: "read_file",
    description: "Read one file's contents. Use AFTER you know which file is relevant.",
    parameters: {
      type: "object",
      properties: {
        filePath: { type: "string", description: "File path, e.g. 'src/auth.ts'" },
      },
      required: ["filePath"],
    },
  },
  {
    name: "search_code",
    description: "Find files containing a keyword. Use to jump straight to a topic.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "Keyword to search for, e.g. 'login'" },
      },
      required: ["query"],
    },
  },
];

/* ================================================================
   3. THE AGENT LOOP — same think→act→observe cycle, different
   message shape: Gemini uses { role, parts: [...] } instead of
   one flat "content" string.
   ================================================================ */

const SYSTEM =
  "You are an assistant that answers questions about a codebase. " +
  "Explore with tools before answering, but use no more than five tool calls. " +
  "For a broad project question, list the root once. Only read files whose exact paths " +
  "appeared in that listing: read README and package metadata when present; otherwise read " +
  "the most relevant source file. Do not list the root twice. Tool responses beginning with " +
  "'Error:' are failures; all other tool responses are evidence you must use in the answer. " +
  "Use search_code only for a specific, meaningful " +
  "identifier or feature name; never search one-character, punctuation-only, whitespace-only, " +
  "or generic words. Never repeat a tool call with the same arguments. " +
  "When you have enough information (or have used five tools), give a concise final answer " +
  "and cite file names. Only state what you found in the files.";

async function runAgent(userQuestion) {
  const models = await getAvailableModels();
  if (models.length === 0) {
    throw new Error("This API key has no models that support generateContent.");
  }
  console.log(`🤖 Agent model fallback chain: ${models.join(", ")}`);

  const messages = [
    { role: "user", parts: [{ text: userQuestion }] },
  ];
  const observations = [];

  const MAX_TOOL_TURNS = 5;

  for (let i = 1; i <= MAX_TOOL_TURNS; i++) {
    const response = await generateWithFallback({
      contents: messages,
      config: {
        systemInstruction: SYSTEM,
        tools: [{ functionDeclarations }],
      },
    }, models);

    const calls = response.functionCalls; // null when the model answers instead

    if (!calls || calls.length === 0) {
      console.log("\n📣 FINAL ANSWER:\n" + responseText(response));
      return;
    }

    // Preserve Gemini's *original* model content, including non-text metadata
    // such as thoughtSignature on functionCall parts. Reconstructing parts from
    // response.functionCalls drops that signature and causes a 400 next turn.
    const modelContent = response.candidates?.[0]?.content;
    if (!modelContent) {
      throw new Error("Gemini returned function calls without model content.");
    }
    messages.push(modelContent);

    // ...then execute each one ourselves and push the results back.
    for (const call of calls) {
      console.log(`🔧 [step ${i}] ${call.name}(${JSON.stringify(call.args)})`);
      const result = runTool(call.name, call.args);
      observations.push({ name: call.name, args: call.args, result: String(result) });
      messages.push({
        role: "user",
        parts: [{
          functionResponse: { name: call.name, response: { result: String(result) } },
        }],
      });
    }
  }

  // Start a clean final request from the evidence. This prevents a model from
  // continuing the prior function-call sequence after tools are disabled.
  const evidence = observations
    .map(({ name, args, result }) => `Tool: ${name}(${JSON.stringify(args)})\nResult:\n${result}`)
    .join("\n\n");
  const finalResponse = await generateWithFallback({
    contents: `Answer this codebase question: ${userQuestion}\n\n` +
      `Use only the following tool observations as evidence:\n${evidence}`,
    config: {
      systemInstruction: "Give a concise final answer using only the supplied evidence. Do not call tools.",
    },
  }, models);
  const finalText = responseText(finalResponse);
  if (!finalText) throw new Error("Gemini returned no text for the final answer.");
  console.log("\n📣 FINAL ANSWER:\n" + finalText);
}

runAgent(process.argv[2] ?? "How does this project work?");
