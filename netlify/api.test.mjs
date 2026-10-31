import assert from "node:assert/strict";
import test from "node:test";

import handler from "./functions/api.mjs";

function call(path, body) {
  return handler(new Request(`https://preview.example${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  }));
}

test("health stays in demo mode", async () => {
  const response = await call("/api/health");
  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.ai_mode, "demo");
  assert.equal(payload.host, "netlify");
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
