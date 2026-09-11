# Frozen synthetic scans

These two images supply the OCR pages in the public retrieval corpus.
Their SHA-256 hashes are frozen in `../corpus.json` and checked during generation.

Both use a white 1500-by-180 RGB canvas and ReportLab 4.4.10's bundled Vera font.
The original rendering used Pillow 12.3.0 on macOS, black text at `(30, 60)`, and font size 34.
`invoices.png` reads: "Scanned evidence: invoices are payable within 45 days."
`signatures.png` reads: "Scanned mixed-page evidence: two signatures are required."

Pillow's native font renderer produced different pixels in Linux CI.
The corpus therefore embeds these frozen pixels instead of rasterizing fonts during generation.
Changing either image requires a corpus revision and another real-engine retrieval gate.
The three primary PDFs and all four expected PDF hashes remain unchanged by this correction.
