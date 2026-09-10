# Repository checks

`check-repository.mjs` checks allowed Markdown locations, local link targets, JSON/YAML syntax, and the canonical Claude instruction import.
It exports `checkRepository(root)` so regression tests can exercise isolated fixture trees.
The CLI prints each failure and exits with status 1, or prints a success count and exits with status 0.

Markdown parsing follows Markdown-it's default CommonMark-compatible rules with HTML enabled.
The check follows normal Markdown links and images, including reference-style links.
It checks embedded HTML image sources for existence.
It deliberately does not fetch remote links or validate heading fragments.

Ignored build, dependency, scratch, and artifact directories are excluded from traversal.
The check rejects symlinks encountered in the checked tree.
That prevents a local link or configuration file from silently reading outside the checkout.
