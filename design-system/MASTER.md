# Travel Agent — Design System

## Brand
- **Name:** Travel Agent
- **Tagline:** Tu asistente inteligente para viajes económicos
- **Tone:** Amigable, útil, inspirador, confiable

## Color Palette

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| Primary | Emerald-600 (#059669) | Emerald-400 (#34D399) | CTAs, links, accents |
| Background | Teal-50 → Emerald-50 gradient | Zinc-950 → Emerald-950 | Page bg |
| Surface | White | Zinc-800/80 | Cards, chat bubbles |
| Text Primary | Zinc-900 | Zinc-100 | Body text |
| Text Secondary | Zinc-500 | Zinc-400 | Muted text |
| Border | Zinc-200 | Zinc-700 | Card borders |
| Success | Emerald | Emerald | Price badges |

## Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| H1 | Geist Sans | 700 bold | 4xl (2.25rem) |
| Body | Geist Sans | 400 regular | sm (0.875rem) |
| Labels | Geist Sans | 500 medium | xs (0.75rem) uppercase |

## Styles

### Cards
- `rounded-2xl` borders
- `bg-white dark:bg-zinc-800/80`
- `border-zinc-200 dark:border-zinc-700`
- Hover: `shadow-lg -translate-y-0.5 transition-all duration-300`
- Cursor: `cursor-pointer`

### Chat
- User bubbles: `bg-emerald-600 text-white rounded-2xl rounded-tr-sm`
- AI bubbles: `bg-white dark:bg-zinc-800 border shadow-sm rounded-2xl rounded-tl-sm`
- Avatar: `w-8 h-8 rounded-full`

### Input
- `rounded-2xl` with `border-zinc-200`
- Focus: `border-emerald-400 ring-2 ring-emerald-400/20`
- Send button: `bg-emerald-600 hover:bg-emerald-700`

## Effects

- **Navbar:** `bg-white/80 backdrop-blur-lg border-b`
- **Loading:** 3 bouncing dots with emerald color
- **Page bg:** `bg-gradient-to-br from-teal-50 via-white to-emerald-50`

## Accessibility
- Focus rings on interactive elements (ring-emerald-400)
- Min 4.5:1 contrast ratio on all text
- SVG icons only (no emojis as icons)
- `cursor-pointer` on all clickable elements
- Touch targets ≥ 44x44px

## Anti-Patterns
- ❌ Emojis as UI icons → Use SVG icons (Heroicons/Lucide)
- ❌ Scale transforms on hover that shift layout → Use color/shadow transitions
- ❌ Overly transparent backgrounds in light mode → Use bg-white/80 minimum

## i18n
- Supported: es, en
- Default: es
- Detection: URL prefix + browser language
