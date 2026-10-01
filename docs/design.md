# Design Guidelines — GridLens UI

## Color Palette

GridLens uses an **Obsidian Premium**-inspired color palette for a professional, sophisticated aesthetic.

### Background & Surface
- **Primary Background**: `slate-50` to `slate-100` (light gradients)
- **Card Background**: `white` with `border-slate-200` borders
- **Subtle Overlay**: `slate-200`, `slate-300`
- **Text on Light**: `slate-900`, `slate-800`, `slate-700`, `slate-600`

### Accent Colors
- **Primary Action**: `violet-600` (hover: `violet-700`)
- **Demand/Electric**: `violet-500` (left borders on metrics)
- **Generation/Output**: `emerald-500` (progress bars, renewable indicators)
- **Renewable Percentage**: `emerald-600` (text)

### Semantic Colors
- **Success/Renewable**: `emerald-*` (wind, solar, hydro)
- **Error/Alert**: `red-600`, `red-50`, `red-200`
- **Loading/Neutral**: `violet-500` (spinners)

### Typography Colors
- **Headings**: `text-slate-900` (dark, professional)
- **Body Text**: `text-slate-700`, `text-slate-600` (readable, muted)
- **Labels**: `text-slate-600`, `text-slate-500` (subtle, supporting)
- **Disabled**: `text-slate-500`, `bg-slate-100` (grayed out)

## Component Styling

### Buttons
```tsx
// Primary (Active)
bg-violet-600 text-white hover:bg-violet-700

// Secondary (Inactive)
bg-slate-200 text-slate-800 hover:bg-slate-300

// Disabled
bg-slate-100 text-slate-400 cursor-not-allowed
```

### Form Elements
```tsx
// Border
border-slate-300

// Focus Ring
focus:ring-2 focus:ring-violet-500

// Disabled
disabled:bg-slate-100 disabled:cursor-not-allowed
```

### Cards & Containers
```tsx
// Standard Card
bg-white rounded-lg shadow-sm border border-slate-200

// No Heavy Shadows
shadow-sm (not shadow)
```

### Spinners & Loaders
```tsx
// Spinner
border-4 border-violet-500 border-t-transparent

// Loading Text
text-slate-500
```

### Metric Cards
```tsx
// Demand (Left Border)
border-l-4 border-violet-500

// Generation (Left Border)
border-l-4 border-emerald-500
```

## Design Principles

### 1. Minimalism
- Use whitespace effectively
- Avoid unnecessary visual clutter
- Let data speak for itself

### 2. Professionalism
- Muted color palette (no bright primary blue)
- Consistent typography hierarchy
- Subtle shadows instead of bold contrasts

### 3. Sophistication
- Inspired by Obsidian Premium aesthetic
- Elegant use of slate grays and violet accents
- Refined typography with proper line heights

### 4. Accessibility
- High contrast ratios (slate-900 on white)
- Clear focus indicators (violet rings)
- Readable font sizes and spacing

### 5. Consistency
- All accent colors use `violet-*` (not blue)
- All backgrounds use `slate-*` (not gray)
- All renewable indicators use `emerald-*` (not green)
- All shadows use `shadow-sm` (not `shadow`)

## Migration from "AI Slop"

### Before (Generic AI Starter)
- Bright blue (`blue-500`, `blue-50`)
- Green gradients (`green-50`)
- Heavy shadows (`shadow`)
- Generic gray text (`gray-*`)

### After (Obsidian Premium)
- Muted violet (`violet-600`)
- Slate backgrounds (`slate-50`, `slate-100`)
- Subtle shadows (`shadow-sm`)
- Professional slate text (`slate-900`, `slate-600`)

## File Updates

All major UI components have been updated:
- ✅ `DashboardPage.tsx` — Background, text colors, metric cards
- ✅ `ComparisonPage.tsx` — Background, buttons, tables
- ✅ `HistoryPage.tsx` — Background
- ✅ `CountrySelector.tsx` — Focus ring, disabled states
- ✅ `ElectricityCard.tsx` — Spinner, text, renewable bar color
- ✅ `GenerationChart.tsx` — (Future: color-coded generation types)

## Future Enhancements

1. **Chart Colors**: Update Recharts bar/line colors to use violet/emerald palette
2. **Dark Mode**: Optional dark mode using slate-900 backgrounds with lighter text
3. **Animations**: Smooth transitions on focus/hover (already in place)
4. **Typography**: Consider adjusting font weights and letter spacing for ultra-polish
