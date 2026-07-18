---
name: Datapolis Editorial System
colors:
  surface: '#effcff'
  surface-dim: '#cfdcdf'
  surface-bright: '#effcff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#e9f6f9'
  surface-container: '#e3f0f3'
  surface-container-high: '#ddeaee'
  surface-container-highest: '#d8e5e8'
  on-surface: '#121d20'
  on-surface-variant: '#3f4948'
  inverse-surface: '#263235'
  inverse-on-surface: '#e6f3f6'
  outline: '#6f7978'
  outline-variant: '#bfc8c7'
  surface-tint: '#276867'
  primary: '#226362'
  on-primary: '#ffffff'
  primary-container: '#3e7c7b'
  on-primary-container: '#dffffe'
  inverse-primary: '#93d2d0'
  secondary: '#2d666d'
  on-secondary: '#ffffff'
  secondary-container: '#b3ecf4'
  on-secondary-container: '#346d73'
  tertiary: '#764f58'
  on-tertiary: '#ffffff'
  tertiary-container: '#916770'
  on-tertiary-container: '#fff7f7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#afeeec'
  primary-fixed-dim: '#93d2d0'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#024f4f'
  secondary-fixed: '#b3ecf4'
  secondary-fixed-dim: '#98d0d7'
  on-secondary-fixed: '#001f23'
  on-secondary-fixed-variant: '#0d4e55'
  tertiary-fixed: '#ffd9e0'
  tertiary-fixed-dim: '#ecb9c4'
  on-tertiary-fixed: '#2f121a'
  on-tertiary-fixed-variant: '#613c45'
  background: '#effcff'
  on-background: '#121d20'
  surface-variant: '#d8e5e8'
typography:
  display-lg:
    fontFamily: Libre Caslon Text
    fontSize: 48px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Libre Caslon Text
    fontSize: 36px
    fontWeight: '400'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Libre Caslon Text
    fontSize: 32px
    fontWeight: '400'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Libre Caslon Text
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.1em
  label-sm:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  container-max: 1120px
  gutter: 32px
---

## Brand & Style

The design system is built for a project-focused editorial experience, emphasizing clarity, sophistication, and a calm, professional atmosphere. It targets an audience that values deep work, architectural precision, and curated content. 

The aesthetic is a blend of **Modern Minimalism** and **Editorial Elegance**. It utilizes generous whitespace to allow data and imagery to breathe, creating a gallery-like experience. The emotional response should be one of quiet confidence—where "soft" does not mean "weak," but rather a refined absence of digital friction. Transitions are subtle, and the visual weight is distributed to favor content over container.

## Colors

The color palette is anchored by a deep teal primary shade that suggests stability and professional depth. The secondary and neutral tones provide a soft, low-contrast environment that reduces eye strain and reinforces the "soft" editorial feel.

- **Primary (#3E7C7B):** Used for key actions, active states, and structural accents.
- **Secondary (#7FB7BE):** Employed for supportive visual elements and subtle highlights.
- **Neutral (#B7C4C7, #E6E8E6, #FFFFFF):** These form the foundation of the layout. #E6E8E6 is the primary surface color for secondary sections, while white remains the canvas for core content.
- **Accent (#D8A7B1):** Reserved for delicate callouts, special tags, or "warm" interaction points to break the cool-toned palette.

## Typography

This design system utilizes a high-contrast typographic pairing to achieve an editorial feel. **Libre Caslon Text** provides an authoritative, literary voice for headings, while **Manrope** offers a balanced, modern, and highly legible experience for body text and data.

Vertical rhythm is maintained by a strict 1.5x or 1.6x line-height for body copy to ensure readability in long-form project descriptions. Labels use increased letter-spacing and uppercase styling to differentiate categorical information from narrative text.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for desktop to maintain a classic editorial column. The content is centered within a 1120px container.

- **Desktop:** 12-column grid with 32px gutters. Hero sections and large imagery may break the grid to go full-bleed for dramatic effect.
- **Mobile:** Single column with 20px side margins.
- **Vertical Rhythm:** A "generous but purposeful" approach means utilizing the `xl` (80px) spacing between major sections (e.g., between the Hero and the Project Description) and `lg` (48px) for internal section groupings.

## Elevation & Depth

This design system avoids heavy drop shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**. Depth is communicated through subtle shifts in background color rather than physical projection.

- **Surface Levels:** The base page is white. Secondary information panels or cards use the neutral `#E6E8E6` background.
- **Outlines:** Use 1px borders in `#B7C4C7` with a low opacity (30-50%) for input fields and card boundaries to keep the interface feeling "light."
- **Focus:** Interactive elements use a soft, primary-colored glow (5-10% opacity) rather than a hard shadow when hovered or focused.

## Shapes

The shape language is **Soft**. Sharp corners are avoided to maintain the approachable and elegant tone, but high roundedness (pills) is avoided to keep the system feeling professional and structured. 

Small components like buttons and tags use a 4px (0.25rem) radius. Larger containers like cards or image frames use 8px (0.5rem) to provide a gentle, modern frame for content.

## Components

- **Buttons:** Primary buttons are solid `#3E7C7B` with white text. Secondary buttons use a `#3E7C7B` outline with 1px width. Text is always centered and uses the `label-sm` weight.
- **Chips/Tags:** Used for project categories. These use a light fill of `#7FB7BE` at 15% opacity with text in the primary color. 
- **Lists:** Data lists in the project detail page should be borderless, using `md` spacing between items and a subtle `#B7C4C7` horizontal rule.
- **Input Fields:** Minimalist design. Only a bottom border of 1px in `#B7C4C7` that transitions to the primary color on focus.
- **Cards:** No shadows. Cards use a background of `#E6E8E6` and an 8px corner radius.
- **Project Stats:** A specific component for "Datapolis" details—large `headline-sm` numbers paired with `label-caps` descriptions, arranged in a horizontal row with generous gutters.