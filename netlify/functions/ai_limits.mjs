/**
 * Netlify Blobs store for shared rate limits.
 * Loaded only when a live generation needs a counter, so tests and demo
 * mode do not require the package to be installed.
 */
import { getStore } from "@netlify/blobs";

export function openBlobStore() {
  return getStore("keyprose-ai-limits", { consistency: "strong" });
}
