# Design Direction

## Product UI Positioning

Wavox should follow an `Operator Console` direction.

This is not a marketing site, a generic SaaS template, or a documentation-first product. It is a real-time control surface for Discord music playback. The interface should feel operational, precise, and composed around live state.

## Design Goals

The UI should communicate:

- confidence in playback state
- clarity under continuous updates
- a premium but restrained visual identity
- product-specific structure instead of template-like sections

The result should feel elegant without becoming decorative.

## Visual Character

### Core Traits

- dark, calm, and focused
- compact without feeling cramped
- technical without feeling cold
- premium without looking glossy or theatrical

### Brand Cues

Use the official `wavox.png` palette as the visual source of truth:

- near-black background
- deep navy surfaces
- cyan as the primary action and active-state color
- magenta as the secondary accent

Color should support emphasis, not carry the entire interface.

## Interface Principles

### 1. Workspace First

The first screen should look like a tool, not a landing page.

- avoid oversized hero composition
- place meaningful product state near the top
- reduce explanatory copy in primary views

### 2. Playback Is the Center

The player is the primary object in the product.

The dashboard should visually revolve around:

- current track
- progress
- controls
- queue context
- synced lyrics

### 3. Dense but Legible

Use screen space efficiently.

- prefer structured density over large empty zones
- keep alignment tight and intentional
- preserve clear spacing between functional groups

### 4. Use Fewer, Stronger Surfaces

Do not build the interface as a field of generic floating cards.

- prefer a few anchored panels with clear roles
- use separators, contrast, and spacing before adding more containers
- avoid giving every block the same visual weight

### 5. State Over Decoration

Live playback state, queue state, lyrics, and guild context should be more visually important than decorative graphics, fake KPIs, or promotional messaging.

## Page Direction

## Home

The home page should act as a product entry point.

- keep the message short
- show what Wavox does immediately
- avoid startup-style feature grids as the main event
- lead the user toward sign-in or dashboard access

The page should feel like the public face of the same system used in the app.

## Dashboard

The dashboard should be structured as an active control workspace.

Recommended composition:

1. top application bar with guild context, navigation, and session controls
2. primary player panel with current track, progress, transport controls, and playback state
3. adjacent queue panel with clear upcoming context
4. dedicated lyrics panel that behaves like a live reading surface
5. optional lower-priority metadata or statistics placed below the main control area

The top of the dashboard should answer, at a glance:

- what is playing
- where playback is
- what happens next
- what guild is being controlled

## Admin

The admin area should inherit the same design language but read as a management surface.

- prioritize tables, lists, summaries, and status groupings
- keep decorative treatment minimal
- distinguish it from the playback workspace by structure, not by inventing a second theme

## Docs

Docs should use the same shell, spacing, and typography as the product.

- no MkDocs-like presentation
- no isolated documentation theme
- maintain a quieter reading rhythm than the dashboard

## Component Rules

### Navigation

- keep navigation compact
- prefer a stable top bar over oversized navigation blocks
- make active context obvious but understated

### Panels

- panels should have explicit roles
- avoid equal-sized, equal-priority card mosaics
- make the main player visibly more important than surrounding panels

### Lists and Tables

- use lists for queue, links, and compact metadata
- use tables for admin and analytical content
- support scanning before ornament

### Buttons and Controls

- primary actions should be limited and obvious
- transport controls should feel tactile and stable
- use color accents mainly for active or primary actions

### Typography

- keep headlines functional
- avoid generic marketing phrasing
- use short labels and concise supporting text

## Do and Don't

| Do | Don't |
|---|---|
| Build around real playback state | Lead with generic feature marketing |
| Use the brand palette with restraint | Flood the UI with glow and gradients |
| Create a clear visual center | Give every panel the same weight |
| Favor operational density | Use oversized empty hero sections |
| Keep docs and app in one design system | Reintroduce a separate docs theme |
| Let layout express product identity | Rely on SaaS-template cards and stat blocks |

## Anti-Patterns to Avoid

- "AI-made" startup hero sections
- symmetrical card grids with no hierarchy
- promotional copy blocks as the dominant content
- placeholder metrics that do not help operation
- excessive blur, glow, or gradient usage
- decorative sections that compete with playback state

## Motion and Feedback

Motion should be subtle and functional.

- use restrained hover and focus responses
- highlight active playback and current lyric line clearly
- avoid animated decoration unrelated to product state

## Copy Direction

Text should sound operational and product-specific.

- concise
- factual
- low on slogans
- high on context

Prefer labels like `Queue`, `Now Playing`, `Guild`, `Elapsed`, and `Next Up` over broad feature language.

## Implementation Order

1. rebuild the home page as a product entry instead of a landing template
2. refine the shared app shell, navigation, spacing, and panel system
3. redesign the dashboard around player, queue, and lyrics hierarchy
4. adapt admin views to the same visual system
5. keep docs in the same system with a quieter reading layout

## Decision Filter

When evaluating a new frontend change, use this question:

`Does this make Wavox feel more like a real-time operator console for music playback, or more like a generic app template?`

If the answer trends toward the template side, the change is likely wrong.
