/**
 * Hosted demo API. Netlify functions support JavaScript, not Python, so this
 * file mirrors the offline generators in backend/ai. Self-hosting still uses
 * backend/server.py, including the OpenAI path.
 */

import { createHash } from "node:crypto";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

function json(status, payload) {
  return new Response(JSON.stringify(payload), { status, headers: JSON_HEADERS });
}

function routeOf(req) {
  const path = new URL(req.url).pathname.replace(/\/+$/, "") || "/";
  const marker = path.indexOf("/api/");
  return marker >= 0 ? path.slice(marker) : path;
}

function money(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value ?? "");
  return number.toLocaleString("en-US");
}

function hashIndex(value, size) {
  const hex = createHash("md5").update(String(value)).digest("hex").slice(0, 8);
  return Number.parseInt(hex, 16) % size;
}

function listingText(details, tone, length) {
  const openers = {
    luxury: [
      "Welcome to an extraordinary residence where sophistication meets comfort.",
      "Indulge in the pinnacle of refined living at this exceptional estate.",
      "Presenting a rare opportunity to own a truly magnificent home.",
    ],
    family: [
      "Welcome home! This warm and inviting property is perfect for growing families.",
      "Create lasting memories in this charming family-friendly retreat.",
      "Everything your family needs — space, comfort, and a neighborhood you'll love.",
    ],
    investment: [
      "Exceptional investment opportunity in a high-demand rental corridor.",
      "Strong cap rate potential with this turnkey income-producing property.",
      "Add this cash-flowing asset to your real estate portfolio today.",
    ],
    casual: [
      "Okay, this one's a gem — and it won't last long!",
      "Love where you live! This adorable home checks every box.",
      "Seriously, you need to see this place in person.",
    ],
    professional: [
      "This well-appointed property offers an exceptional combination of location and value.",
      "Presenting a meticulously maintained residence in a sought-after neighborhood.",
      "A rare opportunity to acquire a move-in ready home with premium finishes throughout.",
    ],
  };
  const chosenTone = openers[String(tone || "").toLowerCase()] ? String(tone).toLowerCase() : "professional";
  const opener = openers[chosenTone][hashIndex(JSON.stringify(details || {}), openers[chosenTone].length)];
  const beds = details.beds ?? 3;
  const baths = details.baths ?? 2;
  const sqft = Number(details.sqft ?? 1800);
  const address = details.address || "this stunning property";
  const features = Array.isArray(details.features) ? details.features.filter(Boolean) : [];
  const year = details.year_built ? `Built in ${details.year_built}, this ` : "This ";
  const neighborhood = details.neighborhood ? ` in the desirable ${details.neighborhood} area` : "";
  const price = Number(details.price) ? ` Listed at $${money(details.price)}.` : "";
  let featureStr = "";
  if (features.length === 1) featureStr = features[0];
  else if (features.length === 2) featureStr = `${features[0]} and ${features[1]}`;
  else if (features.length > 2) featureStr = `${features.slice(0, -1).join(", ")}, and ${features.at(-1)}`;

  const short = `${opener} ${year}${beds}-bedroom, ${baths}-bathroom home${neighborhood} offers ${money(sqft)} sq ft of thoughtfully designed living space.${price}`;
  if (length === "short") return short;
  const extra = featureStr
    ? ` Highlights include ${featureStr}. The open-concept layout flows seamlessly from the gourmet kitchen to the inviting living area, perfect for both everyday living and entertaining. The primary suite is a true retreat, complete with a spa-inspired bath and generous closet space.`
    : " The open-concept layout flows seamlessly from the gourmet kitchen to the inviting living area, perfect for both everyday living and entertaining. The primary suite is a true retreat, complete with a spa-inspired bath and generous closet space.";
  const medium = short + extra;
  if (length !== "long") return medium;
  return medium + " Step outside to a beautifully landscaped backyard — ideal for summer gatherings or quiet evenings under the stars. Additional highlights include updated systems, ample storage throughout, and an attached garage. Conveniently located near top-rated schools, premier dining, boutique shopping, and major commuter routes. Homes like this don't stay on the market long — schedule your private tour today and experience everything this exceptional property has to offer!";
}

function cmaStats(comps) {
  const prices = comps.map((comp) => Number(comp.price)).filter((price) => price > 0);
  const sqfts = comps.map((comp) => Number(comp.sqft)).filter((sqft) => sqft > 0);
  if (!prices.length) return { median: 0, mean: 0, low: 0, high: 0, ppsf: 0 };
  const sorted = [...prices].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  const median = sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  const mean = prices.reduce((sum, price) => sum + price, 0) / prices.length;
  const pairs = comps
    .map((comp) => [Number(comp.price), Number(comp.sqft)])
    .filter(([price, sqft]) => price > 0 && sqft > 0);
  const ppsf = pairs.length ? pairs.reduce((sum, [price, sqft]) => sum + price / sqft, 0) / pairs.length : 0;
  return { median, mean, low: Math.min(...prices) * 0.97, high: Math.max(...prices) * 1.03, ppsf };
}

function roundTo(value, nearest) {
  return Math.round(value / nearest) * nearest;
}

function cmaReport(address, comps) {
  const stats = cmaStats(comps);
  const estimated = stats.median || stats.mean;
  const count = comps.length;
  let summary = `Based on ${count} comparable sale${count === 1 ? "" : "s"} in the subject area, the estimated market value for ${address} is $${money(roundTo(estimated, 1000))}. Recent comparable sales ranged from $${money(roundTo(stats.low, 1000))} to $${money(roundTo(stats.high, 1000))}, with a median sale price of $${money(roundTo(stats.median, 1))}. `;
  if (stats.ppsf > 0) summary += `The average price per square foot among comps is $${stats.ppsf.toFixed(2)}. `;
  summary += "Current market conditions suggest moderate buyer demand with limited inventory, supporting pricing at or slightly above the median comparable. We recommend listing within the suggested range and reviewing after 14 days on market.";
  return {
    cma_summary: summary,
    estimated_value: roundTo(estimated, 1000),
    price_range_low: roundTo(stats.low, 1000),
    price_range_high: roundTo(stats.high, 1000),
    price_per_sqft: stats.ppsf ? Math.round(stats.ppsf * 100) / 100 : null,
    comps_used: count,
    cma_pdf_url: `data:application/pdf;base64,${pdfBase64([
      "KeyProse - CMA Report",
      "Sample report, not an appraisal.",
      "",
      `Subject: ${address}`,
      `Estimated value: $${money(roundTo(estimated, 1000))}`,
      `Range: $${money(roundTo(stats.low, 1000))} - $${money(roundTo(stats.high, 1000))}`,
      stats.ppsf ? `Price per sq ft: $${stats.ppsf.toFixed(2)}` : "Price per sq ft: n/a",
      "",
      ...wrap(summary, 88),
      "",
      "Comparable sales",
      ...comps.slice(0, 8).map((comp) => `${comp.address || "Comp"}  $${money(comp.price)}  ${comp.sqft || ""} sq ft`),
    ])}`,
  };
}

function wrap(text, width) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (next.length > width) {
      if (line) lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function pdfBase64(lines) {
  let y = 760;
  const commands = [];
  for (const raw of lines) {
    const text = String(raw).replace(/[^\x20-\x7E]/g, " ").slice(0, 95);
    const safe = text.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
    commands.push(`BT /F1 11 Tf 48 ${y} Td (${safe}) Tj ET`);
    y -= 16;
    if (y < 48) break;
  }
  const stream = commands.join("\n");
  const objects = [
    "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
    "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
    "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n",
    `4 0 obj<< /Length ${stream.length} >>stream\n${stream}\nendstream\nendobj\n`,
    "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
  ];
  let body = "%PDF-1.4\n";
  const offsets = [0];
  for (const object of objects) {
    offsets.push(body.length);
    body += object;
  }
  const xref = body.length;
  body += `xref\n0 ${objects.length + 1}\n`;
  body += "0000000000 65535 f \n";
  for (let index = 1; index < offsets.length; index += 1) {
    body += `${String(offsets[index]).padStart(10, "0")} 00000 n \n`;
  }
  body += `trailer<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return Buffer.from(body, "latin1").toString("base64");
}

function socialPosts(propertyId, tone, platform, details) {
  const info = details || {
    address: propertyId,
    beds: 3,
    baths: 2,
    sqft: 1800,
    price: 550000,
    highlight: "Open floor plan, updated kitchen, large backyard",
  };
  const address = info.address || "this stunning property";
  const beds = info.beds ?? 3;
  const baths = info.baths ?? 2;
  const sqft = Number(info.sqft ?? 1800);
  const price = Number(info.price) ? `$${money(info.price)}` : "Call for price";
  const highlight = info.highlight || `${beds} bed / ${baths} bath / ${money(sqft)} sqft`;
  const templates = {
    twitter: [
      `Just listed! ${beds}bd/${baths}ba - ${price}. ${highlight} Message for a showing.`,
      `New to market: ${beds}-bed home at ${price}. ${highlight}`,
      `Don't miss this one. ${beds}bd/${baths}ba, ${money(sqft)} sqft - ${price}.`,
    ],
    instagram: [
      `JUST LISTED\n\n${address}\n${beds} bedrooms | ${baths} bathrooms | ${money(sqft)} sq ft\n${price}\n\n${highlight}\n\nMessage to schedule a private showing.`,
    ],
    facebook: [
      `NEW LISTING\n\n${beds}-bedroom, ${baths}-bathroom home.\n${address}\n${money(sqft)} square feet\nListed at ${price}\n\nHighlights: ${highlight}\n\nContact me to schedule a showing.`,
    ],
    linkedin: [
      `New listing.\n\n${beds} bed / ${baths} bath | ${money(sqft)} sq ft\n${address}\n${price}\n\n${highlight}\n\nReach out to schedule a showing.`,
    ],
  };
  const hashtags = {
    luxury: ["#LuxuryRealEstate", "#DreamHome", "#LuxuryLiving"],
    excited: ["#JustListed", "#NewListing", "#HomeSweetHome"],
    professional: ["#RealEstate", "#PropertyForSale", "#HomeBuying"],
    casual: ["#HomeGoals", "#HouseHunting", "#NewHome"],
  };
  const names = platform === "all" ? ["instagram", "facebook", "twitter", "linkedin"] : [String(platform || "instagram").toLowerCase()];
  const seed = hashIndex(propertyId || address, 3);
  return names.map((name) => {
    const options = templates[name] || templates.instagram;
    const content = options[seed % options.length];
    return {
      platform: name,
      content,
      hashtags: (hashtags[tone] || hashtags.excited).concat(["#AustinRealEstate", "#ATXHomes"]),
      character_count: content.length,
    };
  });
}

const EMAILS = {
  buyer: [
    ["New listing: {address}", "Hi {first_name},\n\nI just listed {address}. {beds} bedrooms, {baths} bathrooms, {sqft} sq ft, listed at ${price:,}.\n\nHighlights: {highlight}.\n\nWould you like a private showing this weekend?\n\n{agent_name}\n{agent_phone}", 0],
    ["Following up on {address}", "Hi {first_name},\n\nChecking back on {address}. Happy to answer questions or set a time to walk through it.\n\n{agent_name}\n{agent_phone}", 3],
    ["Still available: {address}", "Hi {first_name},\n\n{address} is still available. If you want to see it, I can arrange a showing today.\n\n{agent_name}\n{agent_phone}", 7],
  ],
  seller: [
    ["A current value range for {address}", "Hi {first_name},\n\nHomes near {address} are trading around ${estimated_value:,} in this {market_condition}. I can walk through a no-obligation CMA whenever you want.\n\n{agent_name}\n{agent_phone}", 0],
    ["Your valuation is ready", "Hi {first_name},\n\nI have a preliminary look at {address}. Reply or call {agent_phone} and I will share the details.\n\n{agent_name}", 4],
  ],
  investor: [
    ["Investment note: {address}", "Hi {first_name},\n\n{address} is listed at ${price:,}, about {beds} bed / {baths} bath, {sqft} sq ft, with an illustrative {cap_rate}% cap rate. Ask me for the rent roll before you rely on that figure.\n\n{agent_name}\n{agent_phone}", 0],
  ],
  past_client: [
    ["Checking in", "Hi {first_name},\n\nIt has been a while. If you want a current value for your home, I can run a quick comparison. Referrals are welcome too.\n\n{agent_name}\n{agent_phone}", 0],
  ],
  cold_lead: [
    ["Market note for {month} {year}", "Hi {first_name},\n\nA short market snapshot: median price ${median_price:,}, about {avg_dom} days on market, inventory {inventory_level}. Reply if you want this narrowed to your neighborhood.\n\n{agent_name}\n{agent_phone}", 0],
  ],
};

function fill(template, context) {
  const data = {
    first_name: "there",
    agent_name: "Your Agent",
    agent_phone: "(512) 555-0100",
    address: "the property",
    beds: 3,
    baths: 2,
    sqft: "1,800",
    price: 550000,
    highlight: "modern finishes and a great location",
    market_condition: "seller's market",
    estimated_value: 600000,
    cap_rate: "6.2",
    month: "July",
    year: "2025",
    median_price: 485000,
    avg_dom: 18,
    inventory_level: "low (2.1 months supply)",
    ...context,
  };
  return template.replace(/\{(\w+)(,)?\}/g, (_, key, comma) => {
    const value = data[key];
    if (comma && typeof value === "number") return money(value);
    return value == null ? "" : String(value);
  });
}

function emailsFor(recipientType, context, numEmails) {
  const key = String(recipientType || "buyer").toLowerCase().replaceAll(" ", "_");
  const templates = EMAILS[key] || EMAILS.buyer;
  const count = Math.min(Math.max(Number(numEmails) || 3, 1), templates.length);
  return templates.slice(0, count).map(([subject, body, delay], index) => ({
    subject: fill(subject, context || {}),
    body: fill(body, context || {}),
    recipient_type: recipientType,
    sequence_step: index + 1,
    send_delay_days: delay,
  }));
}

const SEQUENCES = {
  new_listing: { steps: 4, days: 14, preview: "Step 1 (Day 0): Just listed.\nStep 2 (Day 3): Photos and open house.\nStep 3 (Day 7): Showing reminder.\nStep 4 (Day 14): Similar listings." },
  price_drop: { steps: 3, days: 5, preview: "Step 1 (Day 0): Price reduced.\nStep 2 (Day 2): Value at the new price.\nStep 3 (Day 5): Final call." },
  open_house: { steps: 3, days: 2, preview: "Step 1 (Day 0): Open house invitation.\nStep 2 (Day 1): Reminder and directions.\nStep 3 (Day 2): Thank-you or sorry-we-missed-you." },
  follow_up: { steps: 5, days: 30, preview: "Step 1 (Day 0): Nice to meet you.\nStep 2 (Day 3): Promised resources.\nStep 3 (Day 7): Check-in.\nStep 4 (Day 14): Matching listings.\nStep 5 (Day 30): Market update." },
  custom: { steps: 3, days: 10, preview: "Step 1 (Day 0): Introduction.\nStep 2 (Day 5): Follow-up.\nStep 3 (Day 10): Closing note." },
};

function outreach(contacts, template, customMessage) {
  const key = SEQUENCES[String(template || "").toLowerCase()] ? String(template).toLowerCase() : "custom";
  const sequence = SEQUENCES[key];
  const first = contacts[0]?.name || "your leads";
  let preview = `Outreach sequence for ${contacts.length} contact(s) starting with ${first}:\n\n${sequence.preview}`;
  if (customMessage && key === "custom") preview = `Custom sequence based on: '${String(customMessage).slice(0, 100)}'\n\n${preview}`;
  return {
    status: "ready",
    preview,
    total_contacts: contacts.length,
    sequence_steps: sequence.steps,
    estimated_send_days: sequence.days,
  };
}

async function readJson(req) {
  const raw = await req.text();
  if (!raw) return {};
  return JSON.parse(raw);
}

export default async function handler(req) {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: JSON_HEADERS });
  const path = routeOf(req);
  try {
    if (req.method === "GET" && path === "/api/health") {
      return json(200, { status: "ok", version: "1.0.0", ai_mode: "demo", host: "netlify" });
    }
    const payload = req.method === "POST" ? await readJson(req) : {};

    if (req.method === "POST" && path === "/api/listing-writer") {
      if (!payload.property_details || typeof payload.property_details !== "object") {
        return json(422, { detail: "property_details is required" });
      }
      const listing_text = listingText(payload.property_details, payload.tone || "professional", payload.length || "medium");
      return json(200, { listing_text, word_count: listing_text.split(/\s+/).filter(Boolean).length });
    }

    if (req.method === "POST" && path === "/api/cma") {
      if (!payload.address || !Array.isArray(payload.comps) || payload.comps.length === 0) {
        return json(422, { detail: "address and at least one comp are required" });
      }
      return json(200, cmaReport(payload.address, payload.comps));
    }

    if (req.method === "POST" && path === "/api/social") {
      if (!payload.property_id) return json(422, { detail: "property_id is required" });
      return json(200, {
        posts: socialPosts(payload.property_id, payload.tone || "excited", payload.platform || "all", payload.property_details),
      });
    }

    if (req.method === "POST" && path === "/api/email") {
      if (!payload.recipient_type || !payload.context || typeof payload.context !== "object") {
        return json(422, { detail: "recipient_type and context are required" });
      }
      return json(200, { emails: emailsFor(payload.recipient_type, payload.context, payload.num_emails) });
    }

    if (req.method === "POST" && path === "/api/outreach") {
      if (!Array.isArray(payload.target_list) || payload.target_list.length === 0) {
        return json(422, { detail: "target_list is required" });
      }
      return json(200, outreach(payload.target_list, payload.sequence_template || "new_listing", payload.custom_message));
    }

    return json(404, { detail: "Not found" });
  } catch (error) {
    if (error instanceof SyntaxError) return json(400, { detail: "Invalid JSON" });
    return json(500, { detail: error.message || "Demo API error" });
  }
}

export const config = {
  path: "/api/*",
};
