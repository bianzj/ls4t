# LS4T workspace hierarchy implementation plan

Goal: LS4T is 地表温度反演与归一化工作台, with two workspaces and seven explicit tools.
Architecture: common navigation and landing page; existing component/angle editor retained at stable URLs, independent surface LST endpoint; small time/space adapters reuse existing algorithms. Normalization batch accepts independent configuration files and returns per-job status. Existing raster task queue remains the full-chain retrieval workspace (unzip, conversion, LST, component stages).
Tech stack: Python HTTP server, NumPy, existing normalization modules, vanilla HTML/CSS/JS.
Spec: user's 2026-10-26 hierarchy; implement directly without confirmation.

Design: retain research interface palette (#edf2f5, #ffffff, #203743, #126477, #cfdae0), Chinese YaHei body and Bahnschrift LS4T wordmark. Left-aligned two-column home directories, two-level navigation on every tool, compact forms and auditable tables. Avoid introducing a sequential workflow across independent tools.

- [x] Add tested standalone surface, time, space and independent batch adapters. Time uses supplied diurnal amplitude/peak in local solar time; space uses explicit target row/column and weights. Examples clearly marked controlled, unlike archived AHI/SLSTR angle sample.
- [x] Add home and shared workspace navigation with all seven routes. Preserve old API URLs and batch page.
- [x] Extend observation editor with surface-only mode, add time/space forms and normalization batch file import. Keep independent drafts in session storage across page navigation.
- [x] Verify scientific contracts, regression tests, all routes and desktop/mobile browser interactions; review final changes.

Verification: 57 targeted tests passed. Browser exercised surface, components, time, angle, space and independent normalization batch computations, restored results across navigation, preserved blank/incomplete drafts without stale results, and verified surface URL with trailing slash. Existing full-chain task page loads prior tasks without executing production. Mobile width 390 has document scrollWidth 390. Review findings (cloud rejection, batch exception isolation, trailing-slash mode) fixed and rechecked.

Review focus: direct URL reload, browser history and active nav; incomplete drafts; no stale exports after edits; malformed/mixed batch items; empty target cells remain missing rather than zero.
No commits or unrelated working-tree changes. Existing canonical C:/work/ls4t is the user's active working copy.
