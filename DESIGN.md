# DESIGN.md - OmniDownloader Pro

## 1. Design Direction: Minimalist Pro / Utility Tool
- **Inspiration**: High-performance download workstation tools (Transmission, qBittorrent, aria2 webui) reimagined with a modern, clean, dark-mode desktop aesthetic.
- **Identity & Mood**: Pure functional efficiency, quiet confidence, dense information layout, zero decorative fluff.
- **Tone**: Focused, utilitarian, deterministic, and precise.

## 2. Antislop Dials
- **ENERGY: 2 / 5** (Disciplined, low visual noise, deliberate high-contrast action triggers).
- **RHYTHM: 3 / 5** (Structured tabular alignment, dense monospace metric columns, clear status borders).
- **MOTION: 1 / 5** (Micro-transitions 150ms-200ms only on direct hover/active/progress updates; no gratuitous bouncing, floating blobs, or unnecessary parallax).

## 3. Palette & Typography
- **Background**: Slate-950 (`#090d16` / `#0b0f19`) — deep neutral without saturated neon tint.
- **Surfaces & Cards**: Slate-900 / Slate-850 (`#111827` / `#1e293b`) with crisp `1px border-slate-800`.
- **Text**:
  - Primary: Slate-100 (`#f1f5f9`)
  - Secondary/Labels: Slate-400 (`#94a3b8`)
  - Muted: Slate-500 (`#64748b`)
- **Accents (Functional Only)**:
  - Brand/Active: Indigo-500 (`#6366f1`)
  - Downloading/Speed: Cyan-400 (`#38bdf8`)
  - Success/Complete: Emerald-400 (`#34d399`)
  - Warning/Caution: Amber-400 (`#fbbf24`)
  - Error/Cancel: Rose-500 (`#f43f5e`)
- **Typography**:
  - Headings & Labels: `Outfit`, system sans-serif (clean geometric sans).
  - Metrics, URLs, Paths, Speeds: `JetBrains Mono` (tabular numbers for perfect alignment).

## 4. Layout & Information Density
- **Header**: Minimalist toolbar with live aggregate speed (`0.0 MB/s`), active/queued count, and target path indicator.
- **Input Switcher**: Segmented toggle between **Single Link** and **Batch List (Multi-line)**.
- **Batch Area**: High-density textarea with live link detector parsing supported protocols in real time before queuing.
- **Task List**: Dense task cards/table rows with inline progress bar, numeric percentages, speed, ETA, and direct action buttons (Cancel, Retry, Show in Explorer).
- **Queue Controls**: "Clear Finished", "Cancel All Active", and quick target directory switch.
