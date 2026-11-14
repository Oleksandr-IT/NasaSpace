Prompt for figma

GENERAL (paste first, keep for every screen)

Design a desktop web dashboard (1440 px wide) called "Field Shift".
It helps US farmers compare crop-rotation options for one field, using NASA climate data and USDA soil data.
Users are farmers aged 35–70 with little technical experience. They read it on a laptop in an office or a truck.
It must look like a practical tool made by a small team, not a startup landing page.

Visual style
- Calm, plain, utilitarian, like a good weather service or a USDA data tool, but more modern.
- Background: warm off-white #F7F5F0. Cards: white with a 1 px border #E2DED5. No shadows, or a very subtle one.
- Text: near-black #1F2421 and grey #5C625D.
- One accent colour: muted field green #3F6B3A for buttons, links and selected states.
- Status colours only for data meaning: amber #B7791F for warning, brick red #A1392B for high risk, blue #2F6690 for water or rain. Never use them for decoration.
- Font: "IBM Plex Sans" (or "Source Sans 3"). Body text 16 px, labels 13 px, headings 20–28 px, regular and semibold only.
- Corner radius 6 px. 8 px spacing grid. Plenty of white space, but dense enough to show real data.
- Icons: simple 1.5 px line icons (Lucide style), only where they help, at most one per card.

Do NOT use
- gradients, glassmorphism, neon, purple or blue-violet palettes, glowing effects
- hero sections, big marketing headlines, stock photos of farmers, 3D illustrations, emoji
- "AI sparkle" icons, robot imagery, "Powered by AI" badges
- radar or spider charts, donut charts, gauges, decorative charts with fake data
- more than 2 levels of cards inside cards

Layout for every screen
- Top bar, 56 px: "Field Shift" wordmark on the left in semibold text, no logo graphic. Then a step indicator "1 Field — 2 Conditions — 3 Compare" and a "How it works" link on the right.
- Content area max 1200 px wide, centred.
- Thin footer note on every screen: "This tool supports, not replaces, your judgment and local agronomist advice. Data: NASA POWER, USDA SSURGO, USDA Cropland Data Layer."

Use realistic content: a field in Story County, Iowa. Current rotation: corn → soybean. Numbers: frost-free season 162 days, last spring frost Apr 28, first fall frost Oct 7, growing degree days 1,580, May–Sep rainfall 560 mm, 4 days above 35 °C, soil Clarion loam, 3.5% organic matter, 4% slope.


SCREEN 1 — Choose field and priorities

Two columns.
Left (60%): a map of central Iowa with satellite-style or light terrain tiles. A single pin on the selected field and a small popup: "Story County, IA · 42.00, -93.60". Above the map: a search input "Search address or paste coordinates" and 3 small chips: "Demo: Iowa corn–soy", "Demo: Kansas wheat", "Demo: North Carolina".
Right (40%): a white card titled "What matters most to you?"
- 4 sliders, 1 to 5, each with a one-line plain-language hint: Save water; Build soil health; Reduce erosion; Income from crops.
- 3 toggles: "I can irrigate", "I have livestock (need forage)", "I have equipment for small grains".
- Primary button, full width: "Analyze this field".


SCREEN 2 — Field conditions

Page title "Your field at a glance" with the location underneath in grey.
Row of 5 equal stat cards: each has a small label, a big number and one grey line of context:
"Frost-free season 162 days — Apr 28 to Oct 7", "Growing degree days 1,580 — base 10 °C", "Season rainfall 560 mm — May–Sep average", "Heat days 4 — above 35 °C per year", "Soil Clarion loam — 3.5% organic matter, 4% slope".
Below, a wide card "A typical year on this field": a 12-month combo chart, blue bars for monthly rainfall and a dark line for average temperature. Under the x-axis, a thin horizontal band showing when the field is covered by a crop (green) and when it is bare (light brown, labelled "Bare soil: Oct–Apr").
Below, two cards side by side:
- "What changed in 30 years": 3 small line charts (sparklines with axis labels) for summer max temperature, season rainfall and root-zone soil moisture, each with one sentence like "+0.2 °C per decade".
- "Things to watch": a list of 3 short warnings with an amber or red left border, for example "In 3 of 10 years the last frost came after May 5".
At the bottom, a primary button "Compare rotation options".


SCREEN 3 — Compare rotations

Title "4 rotation options for your field". Under it a segmented control "Typical year | Dry year (like 2012) | Wet year".
4 columns of equal width, one card per option. The first column is "Your current rotation" with a grey "Current" tag. The others: "A · Add winter cereal rye", "B · Corn → soybean → wheat + clover", "C · Swap corn for sorghum".
Each card has:
- An overall score, for example "74 / 100", in large text.
- 6 labelled horizontal bars, 0–100: Water use, Soil health, Erosion control, Pest break, Income, Weather risk.
- A mini 3-year calendar: 3 rows (Year 1–3) by 12 months, with coloured blocks for each crop and a small legend.
- A link "Why this option →".
The best option for the chosen priorities has a thin green border and a small tag "Best match for your priorities". No trophies, no stars.

SCREEN 4 — Option details

Back link "← All options". Title "B · Corn → soybean → wheat + clover".
Left column (65%), 5 sections with small headings and short text:
1. Why we suggest it
2. Evidence from your data: list rows with a value, a source tag ("NASA POWER", "SSURGO", "USDA CDL") and a confidence tag ("Measured", "Model", "Reference")
3. Possible benefits
4. What we don't know
5. Check with a local expert: highlighted with a light amber background
Right column (35%): a sticky card with the score bars from screen 3 and a "Download summary (PDF)" secondary button.

