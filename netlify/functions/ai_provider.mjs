/**
 * OpenAI-compatible Chat Completions client for the hosted function.
 * Prompts match backend/ai so live copy follows the same instructions
 * as the Python server. The key is read from the environment and is never
 * returned or logged.
 */

import { createHash } from "node:crypto";

export const FAIL_NOTICE = "The model call failed, so this is sample output.";
export const LONG_NOTICE = "This request is too long for a live generation. Showing sample output.";
export const HOUR_NOTICE = "Hourly limit reached for this network. Showing sample output instead of a live generation.";
export const DAY_NOTICE = "The daily live-generation limit has been reached. Showing sample output.";
export const PARTIAL_NOTICE = "Part of this result is sample copy because a model call failed.";

const LISTING_SYSTEM = (
  "You are an expert real estate copywriter who crafts compelling, "
  + "accurate MLS listing descriptions that attract qualified buyers."
);

const LENGTH_TARGETS = { short: 100, medium: 200, long: 350 };
const PLATFORM_LIMITS = { twitter: 280, instagram: 2200, facebook: 63206, linkedin: 3000 };
const HASHTAGS = {
  luxury: ["#LuxuryRealEstate", "#DreamHome", "#LuxuryLiving", "#HighEnd", "#EstateLife"],
  excited: ["#JustListed", "#NewListing", "#HomeSweetHome", "#RealEstate", "#ForSale"],
  professional: ["#RealEstate", "#PropertyForSale", "#HomeBuying", "#RealEstateAgent"],
  casual: ["#HomeGoals", "#HouseHunting", "#NewHome", "#RealEstate", "#MovingDay"],
};
const EMAIL_DELAYS = [0, 3, 7, 14, 21];

const memoryCounts = new Map();
let memoryOnly = false;
let resolvedStore;

export class AiFallback extends Error {
  constructor(notice) {
    super(notice);
    this.notice = notice;
    this.name = "AiFallback";
  }
}

export function useMemoryLimitsForTests() {
  memoryOnly = true;
  memoryCounts.clear();
  resolvedStore = undefined;
}

export function resetLimitsForTests() {
  memoryCounts.clear();
}

function configuredInt(name, fallback) {
  const raw = process.env[name];
  if (raw == null || String(raw).trim() === "") return fallback;
  const value = Number(raw);
  if (!Number.isFinite(value) || value < 0) return fallback;
  return Math.floor(value);
}

export function redact(text) {
  let out = String(text ?? "");
  const key = (process.env.OPENAI_API_KEY || "").trim();
  if (key) out = out.split(key).join("[redacted]");
  out = out.replace(/Bearer\s+\S+/gi, "Bearer [redacted]");
  out = out.replace(/sk-[A-Za-z0-9_-]{8,}/g, "[redacted]");
  return out;
}

export function readAiConfig() {
  const apiKey = (process.env.OPENAI_API_KEY || "").trim();
  const baseInput = (process.env.AI_BASE_URL || "https://api.openai.com/v1").trim();
  const model = (process.env.AI_MODEL || process.env.OPENAI_MODEL || "gpt-4o-mini").trim() || "gpt-4o-mini";
  let providerHost = "";
  let chatUrl = "";
  try {
    const url = new URL(baseInput);
    providerHost = url.hostname;
    if (url.protocol === "http:" || url.protocol === "https:") {
      const base = baseInput.replace(/\/+$/, "");
      chatUrl = base.endsWith("/chat/completions") ? base : `${base}/chat/completions`;
    }
  } catch {
    providerHost = "";
  }
  return {
    apiKey,
    model,
    providerHost,
    chatUrl,
    configured: Boolean(apiKey),
    callable: Boolean(apiKey && chatUrl),
  };
}

function inputCap() {
  const cap = configuredInt("AI_MAX_INPUT_CHARS", 8000);
  if (cap === 0) return Infinity;
  return cap > 0 ? cap : 8000;
}

export function maxBodyChars() {
  const cap = configuredInt("AI_MAX_BODY_CHARS", 24000);
  if (cap === 0) return Infinity;
  return cap > 0 ? cap : 24000;
}

export function clampMaxTokens(requested) {
  const cap = configuredInt("AI_MAX_TOKENS", 800);
  const limit = cap > 0 ? cap : 800;
  const asked = Number.isFinite(Number(requested)) ? Math.floor(Number(requested)) : limit;
  return Math.max(1, Math.min(asked, limit));
}

export function clientIp(req) {
  const direct = req.headers.get("x-nf-client-connection-ip");
  if (direct && direct.trim()) return direct.trim();
  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded) {
    const first = forwarded.split(",")[0].trim();
    if (first) return first;
  }
  return "unknown";
}

function hashIp(ip) {
  return createHash("sha256").update(String(ip || "unknown")).digest("hex").slice(0, 32);
}

function hourStamp() {
  return new Date().toISOString().slice(0, 13);
}

function dayStamp() {
  return new Date().toISOString().slice(0, 10);
}

function memoryStore() {
  return {
    async getCount(key) {
      return memoryCounts.get(key) || 0;
    },
    async increment(key) {
      const next = (memoryCounts.get(key) || 0) + 1;
      memoryCounts.set(key, next);
      return next;
    },
  };
}

function wrapBlobStore(store) {
  return {
    async getCount(key) {
      const value = await store.get(key, { type: "json" });
      return value && typeof value.count === "number" ? value.count : 0;
    },
    async increment(key) {
      const count = (await this.getCount(key)) + 1;
      await store.setJSON(key, { count });
      return count;
    },
  };
}

async function activeStore() {
  if (memoryOnly) return memoryStore();
  if (resolvedStore) return resolvedStore;
  try {
    const { openBlobStore } = await import("./ai_limits.mjs");
    const store = openBlobStore();
    await store.get("keyprose-limit-probe", { type: "json" });
    resolvedStore = wrapBlobStore(store);
    return resolvedStore;
  } catch {
    console.error("[api] Netlify Blobs is unavailable; using in-memory rate limits for this instance");
    resolvedStore = memoryStore();
    return resolvedStore;
  }
}

export async function reserveGeneration(ip) {
  const perHour = configuredInt("AI_RATE_LIMIT_PER_HOUR", 10);
  const perDay = configuredInt("AI_DAILY_CAP", 200);
  const store = await activeStore();
  const hourKey = `ip:${hashIp(ip)}:${hourStamp()}`;
  const dayKey = `day:${dayStamp()}`;
  if (perHour > 0 && await store.getCount(hourKey) >= perHour) {
    return { ok: false, notice: HOUR_NOTICE };
  }
  if (perDay > 0 && await store.getCount(dayKey) >= perDay) {
    return { ok: false, notice: DAY_NOTICE };
  }
  if (perHour > 0) await store.increment(hourKey);
  if (perDay > 0) await store.increment(dayKey);
  return { ok: true };
}

function commas(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0";
  return number.toLocaleString("en-US");
}

function dollars0(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0";
  return number.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

export function listingPrompt(details, tone, length) {
  const targetWords = LENGTH_TARGETS[length] ?? 200;
  const features = Array.isArray(details.features) ? details.features.filter(Boolean) : [];
  const featuresStr = features.join(", ") || "modern finishes";
  const beds = details.beds ?? 3;
  const baths = details.baths ?? 2;
  const sqft = Number.isFinite(Number(details.sqft)) ? Number(details.sqft) : 1800;
  const address = details.address || "a prime location";
  const year = details.year_built ? `, built in ${details.year_built}` : "";
  const price = Number.isFinite(Number(details.price)) ? Number(details.price) : 0;
  return (
    `Write a ${tone} real estate listing description for a `
    + `${beds}-bedroom, ${baths}-bathroom home `
    + `at ${address}. `
    + `The home is ${commas(sqft)} sq ft${year}. `
    + `Key features: ${featuresStr}. `
    + `Price: $${commas(price)}. `
    + `Target approximately ${targetWords} words. `
    + "Do not include the price in the listing text. "
    + "Write in second person (you/your). End with a call to action."
  );
}

export function listingSystem() {
  return LISTING_SYSTEM;
}

export function cmaPrompt(address, comps, stats) {
  const median = dollars0(stats.median);
  const low = dollars0(stats.low);
  const high = dollars0(stats.high);
  const ppsf = Number(stats.ppsf || 0).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return (
    `You are a licensed real estate appraiser. Analyze these ${comps.length} `
    + `comparable sales for the subject property at ${address}.\n\n`
    + `Comparable Sales:\n${JSON.stringify(comps, null, 2)}\n\n`
    + `Statistical summary: median=$${median}, `
    + `range=$${low}–$${high}, `
    + `avg $/sqft=$${ppsf}\n\n`
    + "Provide a 3-4 sentence professional CMA summary including: "
    + "estimated market value, price range, market trend commentary, "
    + "and a recommended list price. Be specific with numbers."
  );
}

export function socialPlans(propertyId, tone, platform, details) {
  const info = details || {};
  const names = platform === "all"
    ? ["instagram", "facebook", "twitter", "linkedin"]
    : [String(platform || "instagram").toLowerCase()];
  const tags = (HASHTAGS[tone] || HASHTAGS.excited).slice(0, 3);
  return names.map((name) => {
    const limit = PLATFORM_LIMITS[name] || 2200;
    const sqft = Number.isFinite(Number(info.sqft)) ? Number(info.sqft) : 0;
    const price = Number.isFinite(Number(info.price)) ? Number(info.price) : 0;
    const prompt = (
      `Write a ${tone} ${name} post for a real estate listing.\n`
      + `Property: ${info.beds ?? "None"}bd/${info.baths ?? "None"}ba, `
      + `${commas(sqft)} sqft at ${info.address || propertyId}.\n`
      + `Price: $${commas(price)}\n`
      + `Highlight: ${info.highlight || "beautiful home"}\n`
      + `Platform character limit: ${limit}\n`
      + "Include relevant hashtags. End with a call to action."
    );
    return { platform: name, prompt, hashtags: tags, maxTokens: 400 };
  });
}

export function emailPlans(recipientType, context, numEmails) {
  const requested = Math.min(7, Math.max(1, Number(numEmails) || 3));
  const count = Math.min(requested, 5);
  return Array.from({ length: count }, (_, index) => {
    const step = index + 1;
    const delay = EMAIL_DELAYS[index];
    const prompt = (
      `Write email #${step} in a ${requested}-email sequence for a ${recipientType} `
      + `in real estate. Context: ${JSON.stringify(context)}. `
      + `This is sent ${delay} days after the first contact. `
      + "Include: subject line (prefix with 'Subject: '), then the email body. "
      + "Keep it under 200 words. Professional but warm tone. Clear CTA."
    );
    return { step, delay, prompt, maxTokens: 350 };
  });
}

export function parseEmailDraft(raw, step) {
  const lines = String(raw || "").trim().split("\n");
  const subject = (lines[0] || "").replaceAll("Subject:", "").trim() || `Follow-up #${step}`;
  const body = lines.length > 1 ? lines.slice(1).join("\n").trim() : String(raw || "").trim();
  return { subject, body };
}

export function outreachPrompt(contacts, sequenceTemplate, customMessage, steps) {
  const shown = contacts.slice(0, 5).map((contact) => {
    const name = contact.name || "Contact";
    const type = contact.type || "lead";
    return `${name} (${type})`;
  });
  let summary = shown.join(", ");
  if (contacts.length > 5) summary += ` and ${contacts.length - 5} more`;
  const custom = customMessage ? `Custom message context: ${customMessage}` : "";
  return (
    `Create a ${steps}-step real estate outreach sequence for these contacts: ${summary}.\n`
    + `Template type: ${sequenceTemplate}.\n`
    + `${custom}\n`
    + "For each step, provide: Day number, Subject line, 1-sentence preview.\n"
    + "Format: 'Step N (Day X): Subject — Preview'"
  );
}

export async function chatText({ prompt, system, maxTokens }) {
  const config = readAiConfig();
  if (!config.callable) {
    throw new AiFallback("The model endpoint is not configured, so this is sample output.");
  }
  const user = String(prompt || "");
  const systemText = system ? String(system) : "";
  if (user.length + systemText.length > inputCap()) {
    throw new AiFallback(LONG_NOTICE);
  }
  const messages = [];
  if (systemText) messages.push({ role: "system", content: systemText });
  messages.push({ role: "user", content: user });
  let response;
  try {
    response = await fetch(config.chatUrl, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: config.model,
        messages,
        max_tokens: clampMaxTokens(maxTokens),
        temperature: 0.7,
      }),
      signal: AbortSignal.timeout(18_000),
    });
  } catch (error) {
    if (error instanceof AiFallback) throw error;
    throw new AiFallback(FAIL_NOTICE);
  }
  if (!response.ok) throw new AiFallback(FAIL_NOTICE);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new AiFallback(FAIL_NOTICE);
  }
  const content = data?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || !content.trim()) throw new AiFallback(FAIL_NOTICE);
  return content.trim();
}

export { LISTING_SYSTEM };
