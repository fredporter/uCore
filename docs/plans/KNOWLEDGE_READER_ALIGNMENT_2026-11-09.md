# Knowledge and reading alignment

Implemented on 9 November 2026.

- Documentation tabs use Knowledge, uCode and Advanced. Advanced defaults off and is controlled by Show Advanced in Settings. Existing route IDs remain compatible.
- The global toolbar links directly to Knowledge. Basic Settings expose appearance, text size, profiles and Show Advanced. Engineering pages, configuration and administration are revealed with Advanced.
- Advanced also reveals dashboard engineering/admin cards, extension launches, Recipes navigation, server administration tabs and knowledge federation tools. Personal knowledge copies remain available in the basic view.
- Manual documents retain the right-side reading drawer and can expand to full-screen. Location, chapter count, previous/next, folder navigation and contents stay available. Escape exits full-screen without closing the document; returning to the library restores the opening control.
- Both knowledge and manual readers strip YAML frontmatter from prose and render properties as pills. Read-only parsing handles BOM, CRLF and block-list tags. Card layout is left aligned; prose follows the canonical 72ch measure, 1.7 line-height and serif fallback stack.
- The learning catalogue scans the learning library and uCode/Sonic manuals, excluding whole-vault scans and archived engineering reports. The local catalogue contains 18 guide entries rather than 143 mixed files.
- Tasks filters occupy a single 48px toolbar row, with horizontal overflow on narrow views.

Validation: production build and TypeScript checks pass; nine reader/preference tests and seven backend settings/catalogue tests pass. Static action audit reports 842 controls with no missing handlers. Live inspection confirmed the compact task toolbar, guide cards, reader drawer and metadata pills, with no browser console errors. Full-screen transitions and chapter navigation are covered by component tests; browser comment mode intercepted native button clicks during live inspection.

The normal staged-diff home-policy check cannot run because system git exits 69 under the pending Xcode licence. The same checker passed using --diff-stdin with the complete touched path-owning sources. No canonical knowledge files were edited and no commit was created.
