# Airlock Blog Post -- Gemini Image Generation Prompts

> Style Bible: Modern, clean, minimalist tech illustration. Dark theme with deep navy (#1a1a2e) backgrounds, electric blue (#00d4ff) accents, and crisp white text/elements. Flat design or subtle isometric perspective. No stock-photo realism -- these should feel like custom-made tech diagrams and illustrations. Consistent visual language across all seven images. Subtle code/terminal motifs throughout.

---

### Image 1: Hero / Cover Image
**Filename:** `airlock-blog-hero.png`
**Dimensions:** 1200x630
**Prompt:** A wide-format hero banner illustration with a deep navy (#1a1a2e) background. In the center, a glowing translucent shield icon rendered in electric blue (#00d4ff) with a subtle hexagonal mesh texture, positioned between two abstract nodes: on the left, a minimal flat-design application window (white outline, small terminal-style code lines inside), and on the right, a stylized brain or neural-network icon representing an LLM, glowing faintly in violet-blue. Between the app and the brain, thin data-stream lines flow left to right, but the shield intercepts them, and the lines change color from red (unsafe) to green (safe) as they pass through. At the top-left corner, the word "AIRLOCK" in clean white sans-serif uppercase lettering with a subtle electric-blue glow. Along the very bottom of the image, a faint strip of monospace terminal text is barely visible, reading fragments like `pii_findings: 0 ... status: clean ... latency: 0.4ms`. The overall mood is secure, professional, and high-tech. No photorealistic elements. Flat illustration style with subtle depth from soft glows and drop shadows. Color palette restricted to deep navy, electric blue (#00d4ff), white, and muted red (#ff4757) for danger accents.

**Alt Text:** Airlock hero banner showing a glowing security shield intercepting data streams flowing from an application to an LLM, with unsafe red streams turning safe green as they pass through the proxy.

**Placement:** Top of blog post, immediately below the title and subtitle. This is the first visual the reader sees.

---

### Image 2: The Problem -- Unprotected PII Leakage
**Filename:** `airlock-blog-problem.png`
**Dimensions:** 800x500
**Prompt:** A flat-design illustration on a deep navy (#1a1a2e) background depicting the danger of unprotected LLM API calls. On the left side, a minimal chat interface window (white rounded rectangle outline) with three chat bubbles inside. The user chat bubbles contain partially visible fake PII rendered in small monospace font: an email address, a credit card number with digits, and an SSN -- all highlighted with a soft red (#ff4757) glow to signal danger. From the chat window, a thick arrow made of dashed lines flows to the right, carrying small floating document icons and data fragments, all tinted red. The arrow points directly to a large cloud icon on the right labeled "Third-Party LLM API" in small white text. There is no shield, no proxy, no protection in between -- just an open, unguarded path. Above the arrow, a caution triangle icon with an exclamation mark glows in amber/yellow. Below the arrow, faint white monospace text reads: `POST /v1/chat/completions -- no scanning -- no redaction -- no audit trail`. The overall tone is alarming but clean -- it should make the viewer feel uneasy about the unprotected flow. Flat illustration, no 3D, no photorealism. Colors: deep navy background, red/amber danger accents, white outlines and text.

**Alt Text:** Illustration showing unprotected user data including emails, credit card numbers, and Social Security Numbers flowing directly from a chat interface to a third-party LLM API with no security layer, highlighting the PII leakage problem.

**Placement:** Below the "The Problem Nobody Wants to Talk About" heading, after the opening paragraph of that section.

---

### Image 3: Architecture Diagram -- The Airlock Proxy Pipeline
**Filename:** `airlock-blog-architecture.png`
**Dimensions:** 800x500
**Prompt:** A clean, professional architecture diagram on a deep navy (#1a1a2e) background, illustrating the Airlock proxy pipeline. Three main nodes arranged horizontally from left to right: (1) "Your App" -- represented as a minimal flat application window icon with a small code bracket symbol inside, outlined in white. (2) "Airlock" in the center -- represented as a larger rounded rectangle with an electric blue (#00d4ff) border and a subtle blue glow, containing the word "AIRLOCK" at the top and six small icon-label pairs stacked vertically inside: a magnifying glass for "PII Detection", a shield for "Injection Defense", a speedometer for "Rate Limiting", a dollar sign for "Cost Tracking", an outbound arrow for "Response Scan", and a document for "Logging". (3) "LLM API" on the right -- represented by a cloud icon with a small brain/neural network symbol inside, outlined in white. Arrows connect the three nodes: a solid white arrow from Your App to Airlock labeled "localhost:8080", and a solid white arrow from Airlock to LLM API labeled "api.openai.com". Below Airlock, a small downward arrow points to a minimal log file icon with the label "Structured JSON Logs". The layout is spacious, uncluttered, and easy to follow at a glance. Flat design, no gradients, minimal shadows. Color palette: navy background, electric blue for Airlock emphasis, white for other elements and text.

**Alt Text:** Architecture diagram showing the Airlock proxy sitting between Your App and the LLM API, with six security features inside the proxy: PII Detection, Injection Defense, Rate Limiting, Cost Tracking, Response Scanning, and Structured Logging.

**Placement:** In the "What Airlock Is (and Isn't)" section, replacing or supplementing the ASCII architecture diagram in the code block.

---

### Image 4: Demo Screenshot Mock -- Terminal Catching PII
**Filename:** `airlock-blog-demo.png`
**Dimensions:** 800x500
**Prompt:** A stylized mock terminal screenshot on a deep navy (#1a1a2e) background. The image shows a realistic-looking but illustrated terminal window with a dark charcoal (#0d1117) terminal body, a top bar with three colored dots (red, yellow, green) in the top-left corner, and the title "Terminal -- airlock" in the title bar. Inside the terminal, the content is rendered in monospace font with syntax coloring. The first section shows a curl command in white/light gray sending a JSON payload to `localhost:8080/v1/chat/completions`. Within the JSON payload, the text `My SSN is 123-45-6789 and my email is john@example.com` is visible, with the SSN and email highlighted in red (#ff4757) with a subtle underline. Below the curl command, a horizontal thin line separates the request from the response. The response section shows a formatted JSON response with an `_airlock` object. Inside it: `"pii_findings": 2` is highlighted in electric blue (#00d4ff), and `"pii_types": ["ssn", "email"]` is highlighted in amber/yellow. At the very bottom of the terminal, a single log line reads: `INFO | pii_detected | types=ssn,email | action=redacted | latency=0.3ms` in a dim green color. The overall feel should be a polished, designed version of a real terminal -- not a raw screenshot, but an illustrated rendition that is immediately readable. Flat style, crisp text, no blur or photorealism.

**Alt Text:** Stylized terminal screenshot showing a curl request containing a Social Security Number and email address being sent to Airlock, with the JSON response highlighting that two PII findings were detected and redacted.

**Placement:** In the "See It in Action: A Live Demo" section, after the first curl example and response JSON block.

---

### Image 5: Pipeline Steps -- The 8-Step Security Pipeline
**Filename:** `airlock-blog-pipeline.png`
**Dimensions:** 800x500
**Prompt:** A vertical flowchart illustration on a deep navy (#1a1a2e) background depicting Airlock's eight-step security pipeline. Eight rounded rectangle nodes are arranged in a single vertical column, connected by downward-pointing arrows with a subtle electric blue (#00d4ff) glow. Each node has a small icon on its left side and a label in white sans-serif text. The eight steps from top to bottom are: (1) Speedometer icon -- "Rate Limit Check", (2) Document/parse icon -- "Read & Parse Request", (3) Magnifying glass icon with red accent -- "PII Scan & Redact", (4) Shield icon with warning symbol -- "Prompt Injection Scan", (5) Arrow/send icon -- "Forward to Upstream LLM", (6) Eye/scan icon -- "Response Scan", (7) Dollar/coin icon -- "Cost Tracking & Budget Check", (8) Log/file icon -- "Structured Log & Return". Steps 3 and 4 have a subtle red-to-green gradient on their left border to indicate the transition from dangerous input to safe output. Step 5 has a slightly larger visual presence as the midpoint where the request leaves the network. The entire flowchart fits comfortably in the frame with generous padding. To the left of step 3, a tiny callout bubble reads "regex-based, sub-ms". To the right of step 7, a tiny callout bubble reads "tiktoken estimates". Clean, minimal, flat design. No 3D perspective. Colors: navy, electric blue, white, with red and green accents only on steps 3-4.

**Alt Text:** Vertical flowchart showing Airlock's eight-step security pipeline: Rate Limit Check, Read and Parse Request, PII Scan and Redact, Prompt Injection Scan, Forward to Upstream LLM, Response Scan, Cost Tracking and Budget Check, and Structured Log and Return.

**Placement:** In the "How It Works Under the Hood" section, replacing or supplementing the ASCII pipeline diagram.

---

### Image 6: Tradeoffs -- Regex vs ML Detection
**Filename:** `airlock-blog-tradeoffs.png`
**Dimensions:** 800x500
**Prompt:** A side-by-side comparison illustration on a deep navy (#1a1a2e) background, split vertically into two panels with a thin white divider line in the middle. The left panel is titled "Regex-Based (Airlock Today)" in electric blue (#00d4ff) text at the top. Below it, a vertical list of attributes, each with a small icon and label: a lightning bolt icon with "Sub-millisecond latency" in green (#2ed573), a checkmark icon with "Deterministic & auditable" in green, a gear icon with "Zero GPU / zero dependencies" in green, a document icon with "Human-readable rules in YAML" in green, and a warning triangle icon with "~90% coverage, misses obfuscated PII" in amber/yellow. The right panel is titled "ML-Based (Future Plugin)" in a muted gray-blue text at the top. Below it, a similar vertical list: a turtle/slow icon with "50-200ms added latency" in amber, a question mark icon with "Probabilistic, harder to audit" in amber, a server icon with "Requires GPU or API call" in amber, a brain icon with "Catches novel/obfuscated attacks" in green, and a chart-up icon with "Higher recall, fewer false negatives" in green. At the bottom of the image, spanning both panels, a subtle callout bar in dark blue reads: "Airlock's position: ship the fast deterministic layer now, add ML as an opt-in plugin later." in small white italic text. The overall design communicates an honest, balanced comparison without favoring one approach unfairly. Flat icons, clean typography, no 3D. Colors: navy, electric blue, white, green for pros, amber for tradeoffs.

**Alt Text:** Side-by-side comparison of regex-based detection (Airlock today) versus ML-based detection (future plugin), showing tradeoffs in latency, auditability, dependencies, coverage, and recall, with Airlock's position being to ship the fast deterministic layer now and add ML later.

**Placement:** In the "Where Airlock Will Let You Down (And Why I Shipped It Anyway)" section, after the paragraph about regex-based detection.

---

### Image 7: Roadmap -- Future Features
**Filename:** `airlock-blog-roadmap.png`
**Dimensions:** 800x500
**Prompt:** A horizontal timeline roadmap illustration on a deep navy (#1a1a2e) background. A single horizontal line runs from left to right across the center of the image, with a subtle electric blue (#00d4ff) gradient glow. The left end of the line is marked with a filled circle and labeled "v0.1 -- Today" in white text. Along the timeline to the right, six milestone markers are evenly spaced, each represented by a small circle node on the line with a vertical stem connecting to a card above or below (alternating above and below the line for visual variety). The six milestones and their cards are: (1) Above -- a small streaming icon with the label "Streaming Passthrough" and subtitle "SSE chunks, optional response scan bypass". (2) Below -- a small database icon with "Redis Rate Limiting" and subtitle "Shared state for horizontal scaling". (3) Above -- a small telemetry/graph icon with "OpenTelemetry Export" and subtitle "Traces & metrics to your observability stack". (4) Below -- a small brain icon with "ML Injection Detection" and subtitle "Optional plugin, higher recall". (5) Above -- a small puzzle-piece icon with "Plugin System" and subtitle "Custom scanners, no forking required". (6) Below -- a small dashboard/monitor icon with "Admin Dashboard" and subtitle "Web UI for costs, findings, rate limits". The first two milestones are slightly brighter (near-term priority), the middle two are medium brightness, and the last two are slightly dimmer (longer-term). The rightmost end of the timeline fades out with a subtle "..." to indicate the roadmap continues. Clean, minimal, flat design. No 3D. Colors: navy, electric blue, white text, with varying opacity to indicate priority.

**Alt Text:** Horizontal timeline roadmap for Airlock showing six planned features: Streaming Passthrough, Redis Rate Limiting, OpenTelemetry Export, ML Injection Detection, Plugin System, and Admin Dashboard, arranged from near-term to longer-term priorities.

**Placement:** In the "What's on the Roadmap" section, after the introductory sentence and before or alongside the bullet-point list of features.

---

## Usage Notes

- **Generate images one at a time** in Gemini, using each prompt above verbatim.
- After generation, review each image for visual consistency with the others (color palette, icon style, typography weight).
- If Gemini adds unwanted photorealistic elements or 3D renders, append the following to the prompt: *"Strictly flat 2D vector illustration style. No 3D rendering, no photorealism, no gradients except subtle glows. Clean edges, solid fills."*
- For text legibility, regenerate if any on-image text is misspelled or illegible -- Gemini sometimes garbles small text.
- All images should be exported/saved as PNG with transparency disabled (solid navy background).
- Compress final PNGs to under 300KB each for web performance.
