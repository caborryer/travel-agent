# Landing Page — Travel Agent

## Layout
- Single-page app with chat at center
- Max-width: `max-w-5xl`
- Padding: `px-4 pt-24 pb-8`

## Sections
1. **Navbar** — Fixed top, brand logo + language toggle
2. **Hero** — Title + subtitle centered
3. **Chat Feed** — Scrollable message list with cards
4. **Chat Input** — Sticky bottom input
5. **Footer** — Copyright/info

## Components
- **Navbar:** Travel Agent logo (globe icon) + "English"/"Español" toggle
- **Hero:** h1 + p tagline
- **ChatMessage:** Avatar + bubble (user right, AI left)
- **DestinationCard:** Card with price, score, season, activities
- **ChatInput:** Rounded input with send button
- **Footer:** Simple text

## States
- **Empty:** Welcome message from AI
- **Loading:** Three bouncing dots + "Searching..."
- **Results:** Message + destination cards grid (1→2→3 cols)
- **Error:** Error message from AI
