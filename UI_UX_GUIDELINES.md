# UI/UX Guidelines - UI UX Pro Max Integration

This project leverages the **[UI UX Pro Max](https://uupm.cc)** library to ensure professional design intelligence, consistency, and a high-quality user experience across the application.

## 🚀 How to Update the UI/UX

Whenever you need to update the UI/UX of this project, follow these steps:

### 1. Initialize the Skill
The library is installed as a Cursor Skill in:
`.cursor/skills/ui-ux-pro-max/SKILL.md`

Always refer to this skill before starting any design work to leverage its reasoning engine and style guidelines.

### 2. Design System Generation
Use the internal reasoning engine to analyze project requirements and generate a complete, tailored design system.

Example prompt to Cursor:
> "Analyze the current project and use UI UX Pro Max to generate a design system for a [Market/Fintech/SaaS] application."

### 3. Apply Professional Styles
The library provides 67 UI styles (Minimalism, Glassmorphism, Bento Grid, etc.) and 96 color palettes. Choose the one that best fits the brand identity.

### 4. Stack-Specific Implementation
Follow the guidelines for the project's stack:
- **Frontend**: React + Tailwind CSS + Lucide Icons
- **Mobile**: Android (Jetpack Compose)

### 5. Pre-Delivery Checklist
Before finishing a UI task, verify:
- [ ] No emojis as icons (use SVG: Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Text contrast (4.5:1 minimum)
- [ ] Responsive design (Mobile first)

---

## 📚 Library Reference

### Key Features
- **Design System Generator**: AI-powered reasoning engine for tailored systems.
- **100 Industry-Specific Rules**: Specialized guidelines for SaaS, Finance, Healthcare, etc.
- **67 UI Styles**: From Glassmorphism to Bento Box Grids.
- **Master + Overrides Pattern**: Persist design choices in `design-system/MASTER.md`.

For full documentation, visit [uupm.cc](https://uupm.cc).
