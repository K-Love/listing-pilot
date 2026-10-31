import assert from "node:assert/strict";
import { describe, test } from "node:test";

import handler, { resetLimitsForTests, useMemoryLimitsForTests } from "./functions/api.mjs";

useMemoryLimitsForTests();
delete process.env.OPENAI_API_KEY;
const SECRET = "sk-test-secret-value";

function call(path, body, headers = {}) {
  const requestHeaders = { ...headers };
  if (body && !requestHeaders["content-type"]) requestHeaders["content-type"] = "application/json";
  return handler(new Request(`https://preview.example${path}`, {
    method: body ? "POST" : "GET",
    headers: Object.keys(requestHeaders).length ? requestHeaders : undefined,
    body: body ? JSON.stringify(body) : undefined,
  }));
}

async function withEnv(vars, fn) {
  const previous = new Map();
  for (const [key, value] of Object.entries(vars)) {
    previous.set(key, process.env[key]);
    if (value == null) delete process.env[key];
    else process.env[key] = value;
  }
  const previousFetch = globalThis.fetch;
  resetLimitsForTests();
  try {
    return await fn();
  } finally {
    for (const [key, value] of previous) {
      if (value == null) delete process.env[key];
      else process.env[key] = value;
    }
    globalThis.fetch = previousFetch;
    resetLimitsForTests();
  }
}

function mockChat(content, capture, status = 200) {
  globalThis.fetch = async (url, options) => {
    capture.calls = (capture.calls || 0) + 1;
    capture.url = String(url);
    capture.urls = capture.urls || [];
    capture.urls.push(String(url));
    capture.body = JSON.parse(options.body);
    capture.bodies = capture.bodies || [];
    capture.bodies.push(capture.body);
    capture.auth = options.headers.Authorization;
    if (status !== 200) return new Response("nope", { status });
    return new Response(JSON.stringify({
      choices: [{ message: { content } }],
    }), { status: 200, headers: { "content-type": "application/json" } });
  };
}

const LISTING = {
  property_details: {
    address: "123 Maple Street",
    beds: 4,
    baths: 3,
    sqft: 2400,
    price: 650000,
    features: ["pool"],
  },
  tone: "luxury",
  length: "short",
};

describe("hosted api", { concurrency: false }, () => {

test("health stays in demo mode", async () => {
  await withEnv({ OPENAI_API_KEY: null, AI_BASE_URL: null }, async () => {
    const response = await call("/api/health");
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.equal(payload.ai_mode, "demo");
    assert.equal(payload.host, "netlify");
    assert.equal(payload.provider_host, "api.openai.com");
    assert.equal(JSON.stringify(payload).includes("sk-"), false);
  });
});

test("listing, email, and outreach respond", async () => {
  const listing = await call("/api/listing-writer", {
    property_details: { address: "123 Maple Street", beds: 4, baths: 3, sqft: 2400, price: 650000 },
    tone: "luxury",
    length: "short",
  });
  assert.equal(listing.status, 200);
  const listingBody = await listing.json();
  assert.match(listingBody.listing_text, /4-bedroom/);
  assert.ok(listingBody.word_count > 10);

  const emails = await call("/api/email", {
    recipient_type: "buyer",
    num_emails: 2,
    context: { first_name: "Alex", agent_name: "Sarah Johnson", address: "123 Maple Street" },
  });
  const emailBody = await emails.json();
  assert.equal(emailBody.emails.length, 2);
  assert.match(emailBody.emails[0].body, /Sarah Johnson/);

  const outreach = await call("/api/outreach", {
    target_list: [{ name: "Alex Rivera", email: "alex@example.com", type: "buyer" }],
    sequence_template: "open_house",
  });
  const outreachBody = await outreach.json();
  assert.equal(outreachBody.total_contacts, 1);
  assert.match(outreachBody.preview, /Alex Rivera/);
});

test("cma returns an inline pdf", async () => {
  const response = await call("/api/cma", {
    address: "456 Oak Avenue",
    comps: [{ address: "100 Maple St", price: 635000, sqft: 2350, beds: 4, baths: 3, sold_date: "2025-05-15" }],
  });
  const payload = await response.json();
  assert.ok(payload.estimated_value > 0);
  assert.match(payload.cma_pdf_url, /^data:application\/pdf;base64,/);
  const pdf = Buffer.from(payload.cma_pdf_url.split(",")[1], "base64");
  assert.equal(pdf.subarray(0, 4).toString(), "%PDF");
});

test("bad json is rejected", async () => {
  const response = await handler(new Request("https://preview.example/api/email", {
    method: "POST",
    body: "{",
  }));
  assert.equal(response.status, 400);
});

test("live listing uses the configured chat endpoint", async () => {
  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_BASE_URL: "https://routellm.abacus.ai/v1",
    AI_MODEL: "route-llm",
    OPENAI_MODEL: "gpt-4o-mini",
  }, async () => {
    const capture = {};
    mockChat("A live listing written for you.", capture);
    const response = await call("/api/listing-writer", LISTING);
    const payload = await response.json();
    assert.equal(response.status, 200);
    assert.equal(payload.ai_mode, "live");
    assert.equal(payload.listing_text, "A live listing written for you.");
    assert.equal(capture.url, "https://routellm.abacus.ai/v1/chat/completions");
    assert.equal(capture.auth, `Bearer ${SECRET}`);
    assert.equal(capture.body.model, "route-llm");
    assert.equal(capture.body.max_tokens, 600);
    assert.equal(capture.body.messages[0].role, "system");
    assert.match(capture.body.messages[0].content, /expert real estate copywriter/);
    assert.match(capture.body.messages[1].content, /second person/);
    assert.equal(JSON.stringify(payload).includes(SECRET), false);
  });
});

test("max tokens and input length are capped", async () => {
  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_BASE_URL: "https://api.openai.com/v1/chat/completions",
    AI_MODEL: null,
    OPENAI_MODEL: "gpt-4o-mini",
    AI_MAX_TOKENS: "40",
  }, async () => {
    const capture = {};
    mockChat("Capped listing.", capture);
    const response = await call("/api/listing-writer", LISTING);
    const payload = await response.json();
    assert.equal(payload.listing_text, "Capped listing.");
    assert.equal(capture.url, "https://api.openai.com/v1/chat/completions");
    assert.equal(capture.body.model, "gpt-4o-mini");
    assert.equal(capture.body.max_tokens, 40);
  });

  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_MAX_INPUT_CHARS: "20",
  }, async () => {
    let called = false;
    globalThis.fetch = async () => {
      called = true;
      throw new Error("should not be called");
    };
    const response = await call("/api/listing-writer", LISTING);
    const payload = await response.json();
    assert.equal(called, false);
    assert.equal(payload.ai_mode, "demo");
    assert.match(payload.listing_text, /4-bedroom/);
    assert.match(payload.notice, /too long/);
    assert.equal(JSON.stringify(payload).includes(SECRET), false);
  });
});

test("provider failures and rate limits fall back to demo output", async () => {
  await withEnv({ OPENAI_API_KEY: SECRET, AI_BASE_URL: "https://api.openai.com/v1" }, async () => {
    globalThis.fetch = async () => {
      throw new Error(`connect failed Bearer ${SECRET}`);
    };
    const response = await call("/api/listing-writer", LISTING);
    const payload = await response.json();
    assert.equal(payload.ai_mode, "demo");
    assert.match(payload.listing_text, /4-bedroom/);
    assert.match(payload.notice, /sample output/);
    assert.equal(JSON.stringify(payload).includes(SECRET), false);
  });

  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_RATE_LIMIT_PER_HOUR: "1",
    AI_DAILY_CAP: "100",
  }, async () => {
    const capture = {};
    mockChat("First live listing.", capture);
    const first = await (await call("/api/listing-writer", LISTING, { "x-nf-client-connection-ip": "203.0.113.5" })).json();
    const second = await (await call("/api/listing-writer", LISTING, { "x-nf-client-connection-ip": "203.0.113.5" })).json();
    const other = await (await call("/api/listing-writer", LISTING, { "x-nf-client-connection-ip": "203.0.113.9" })).json();
    assert.equal(first.ai_mode, "live");
    assert.equal(second.ai_mode, "demo");
    assert.match(second.notice, /Hourly/);
    assert.match(second.listing_text, /4-bedroom/);
    assert.equal(other.ai_mode, "live");
    assert.equal(capture.calls, 2);
  });

  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_RATE_LIMIT_PER_HOUR: "0",
    AI_DAILY_CAP: "1",
  }, async () => {
    mockChat("Only one today.", {});
    const first = await (await call("/api/email", {
      recipient_type: "buyer",
      num_emails: 1,
      context: { first_name: "Alex" },
    }, { "x-forwarded-for": "198.51.100.4" })).json();
    const second = await (await call("/api/email", {
      recipient_type: "buyer",
      num_emails: 1,
      context: { first_name: "Alex" },
    }, { "x-forwarded-for": "198.51.100.8" })).json();
    assert.equal(first.ai_mode, "live");
    assert.match(first.emails[0].subject, /Only one today|Follow-up|Subject/);
    assert.equal(second.ai_mode, "demo");
    assert.match(second.notice, /daily/);
    assert.match(second.emails[0].body, /Alex|there/);
  });
});

test("cma, social, email, and custom outreach use the model", async () => {
  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_BASE_URL: "https://api.openai.com/v1",
    AI_MODEL: "gpt-4o-mini",
  }, async () => {
    const capture = {};
    mockChat("Subject: Saturday showing\n\nHi Alex, the model wrote this.", capture);
    const emails = await (await call("/api/email", {
      recipient_type: "buyer",
      num_emails: 2,
      context: { first_name: "Alex", agent_name: "Sarah Johnson", address: "123 Maple Street" },
    })).json();
    assert.equal(emails.ai_mode, "live");
    assert.equal(emails.emails.length, 2);
    assert.equal(emails.emails[0].subject, "Saturday showing");
    assert.match(emails.emails[0].body, /model wrote this/);
    assert.equal(emails.emails[0].send_delay_days, 0);
    assert.equal(emails.emails[1].send_delay_days, 3);
    assert.match(capture.bodies[0].messages[0].content, /email #1/);

    mockChat("Model CMA narrative.", {});
    const cma = await (await call("/api/cma", {
      address: "456 Oak Avenue",
      comps: [{ address: "100 Maple St", price: 635000, sqft: 2350, beds: 4, baths: 3, sold_date: "2025-05-15" }],
    })).json();
    assert.equal(cma.ai_mode, "live");
    assert.equal(cma.cma_summary, "Model CMA narrative.");
    assert.ok(cma.estimated_value > 0);
    assert.match(cma.cma_pdf_url, /^data:application\/pdf;base64,/);

    const socialCapture = {};
    mockChat("Just listed — message me.", socialCapture);
    const social = await (await call("/api/social", {
      property_id: "123-maple",
      tone: "luxury",
      platform: "all",
      property_details: { address: "123 Maple Street", beds: 4, baths: 3, sqft: 2400, price: 650000, highlight: "pool" },
    })).json();
    assert.equal(social.ai_mode, "live");
    assert.equal(social.posts.length, 4);
    assert.deepEqual(social.posts.map((post) => post.platform), ["instagram", "facebook", "twitter", "linkedin"]);
    assert.equal(socialCapture.calls, 4);
    assert.ok(social.posts[0].hashtags.includes("#LuxuryRealEstate"));
    assert.match(socialCapture.bodies[0].messages[0].content, /instagram post/);

    let outreachCalls = 0;
    globalThis.fetch = async () => {
      outreachCalls += 1;
      return new Response(JSON.stringify({
        choices: [{ message: { content: "Step 1 (Day 0): Hello — A custom note." } }],
      }), { status: 200 });
    };
    const stock = await (await call("/api/outreach", {
      target_list: [{ name: "Alex Rivera", email: "alex@example.com", type: "buyer" }],
      sequence_template: "open_house",
    })).json();
    assert.equal(outreachCalls, 0);
    assert.equal(stock.ai_mode, "demo");
    assert.match(stock.preview, /Alex Rivera/);

    const custom = await (await call("/api/outreach", {
      target_list: [{ name: "Alex Rivera", email: "alex@example.com", type: "buyer" }],
      sequence_template: "custom",
      custom_message: "Invite them to a private tour",
    })).json();
    assert.equal(outreachCalls, 1);
    assert.equal(custom.ai_mode, "live");
    assert.match(custom.preview, /custom note/);
    assert.equal(JSON.stringify(custom).includes(SECRET), false);
  });
});

test("an oversized body is rejected before a model call", async () => {
  await withEnv({ OPENAI_API_KEY: SECRET, AI_MAX_BODY_CHARS: "40" }, async () => {
    let called = false;
    globalThis.fetch = async () => {
      called = true;
      throw new Error(SECRET);
    };
    const response = await call("/api/listing-writer", LISTING);
    assert.equal(response.status, 413);
    const payload = await response.json();
    assert.match(payload.detail, /too large/);
    assert.equal(called, false);
    assert.equal(JSON.stringify(payload).includes(SECRET), false);
  });
});

test("health reports live mode and the provider host only", async () => {
  await withEnv({
    OPENAI_API_KEY: SECRET,
    AI_BASE_URL: `https://${SECRET}@routellm.abacus.ai/v1`,
    AI_MODEL: "route-llm",
  }, async () => {
    const response = await call("/api/health");
    const payload = await response.json();
    assert.equal(payload.ai_mode, "live");
    assert.equal(payload.provider_host, "routellm.abacus.ai");
    assert.equal(payload.host, "netlify");
    const encoded = JSON.stringify(payload);
    assert.equal(encoded.includes(SECRET), false);
    assert.equal(encoded.includes("route-llm"), false);
  });
});
});
