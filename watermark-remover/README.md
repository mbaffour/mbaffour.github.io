# Watermark Remover

A browser port of the deterministic layers of
[guillaumemeyer/watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover).
It finds the characters and metadata that mark a file as machine-made or trace it back to you,
removes them, and reports exactly what it did — with no server, no upload, no build step and no
dependencies.

**Live:** <https://mbaffour.github.io/watermark-remover/>
**Tests:** <https://mbaffour.github.io/watermark-remover/tests.html> · or `node tests.node.js`

---

## Why a browser version

The upstream project is Python plus an HTTP service. That is the right shape for a pipeline and the
wrong shape for the common case, which is one person with one file who does not want to install
anything and — this is the point — does not want to hand the file to a service in order to have its
identifying data removed. A privacy tool that uploads your document to strip its metadata has an
awkward hole in the middle of it.

Everything here runs in the tab. The page works offline after first load.

## The three layers, and which two are here

The upstream design separates what can be verified from what cannot, and this port keeps that split.

| Layer | What it is | Here? |
|---|---|---|
| **A — deterministic** | Invisible Unicode, tag characters, variation selectors, bidi controls, exotic spaces, homoglyphs | Yes |
| **B — statistical** | Token-sampling watermarks, removed by model-driven rewriting | **No** |
| **File cleaners** | EXIF, XMP, IPTC, C2PA, PNG text chunks, PDF properties, Office/EPUB properties | Yes |

Layer B is absent on purpose. A statistical watermark is a property of which words a model chose
across a whole passage, so removing one means rewriting a substantial fraction of the text sentence
by sentence — which costs you your voice, and needs a language model. In a browser that is either a
multi-gigabyte download or an API call, and the API call breaks the one promise this tool makes. So
the tool does the layers it can do honestly and says so in the UI rather than implying more.

## What it removes

**Text (Layer A)**

- Invisible and zero-width characters — ZWSP, word joiner, soft hyphen, BOM, Hangul and Khmer fillers, interlinear annotation marks
- Unicode tag characters (U+E0000–E007F) — a complete invisible ASCII alphabet, and the usual smuggling carrier
- Variation selectors (U+FE00–FE0F, U+E0100–E01EF) — 256 codepoints, one per byte value
- Zero-width binary payloads, decoded under the common bit mappings
- Bidirectional controls, including the overrides behind Trojan Source
- Homoglyphs — Cyrillic and Greek lookalikes, folded **only** inside words that mix scripts
- Exotic spaces normalised to U+0020
- Optional: NFKC folding of styled letterforms, typographic normalisation, whitespace tidy

Any hidden payload found is **decoded and shown to you** before it is removed.

**Files**

| Format | What comes out |
|---|---|
| PNG | tEXt/zTXt/iTXt (where Stable Diffusion writes your prompt), eXIf, tIME, caBX (C2PA), data appended past IEND |
| JPEG | EXIF, XMP and extended XMP, IPTC/Photoshop blocks, JUMBF/C2PA in APP2 and APP11, comments, data past EOI |
| WebP | EXIF and XMP chunks, C2PA, with the VP8X flag bits corrected to match |
| GIF | Comment extensions and application extensions, keeping the NETSCAPE loop block |
| SVG | `<metadata>`, comments, `<desc>`, editor attributes, plus the text pass |
| PDF | Info dictionary strings, XMP packets, trailer `/ID` |
| DOCX / PPTX / XLSX | core.xml, app.xml, custom.xml, per-entry ZIP timestamps, invisible characters in the body |
| EPUB | Packaging timestamps and contributor, ZIP timestamps, invisible characters — title and author kept |
| ODT | meta.xml, ZIP timestamps, invisible characters |
| TXT / MD / HTML / CSV / JSON / … | The full text pass |

## Two design decisions worth knowing

**Images are operated on, not re-encoded.** The container is parsed, the metadata chunks are
dropped, and every remaining byte is copied through untouched. Your pixels come out bit-identical.
The usual "draw it to a canvas and export" approach silently recompresses the image, flattens
transparency and loses the colour profile. (A canvas re-encode is still offered as an explicit,
clearly labelled fallback.)

**PDF edits preserve file length.** A PDF's cross-reference table records the byte offset of every
object, so deleting bytes breaks the file. Every edit here overwrites in place with the same number
of bytes: string contents become spaces, hex digits become zeroes, XMP packet bodies become
whitespace. The xref stays valid and the document still opens. Verified in the test suite, and on a
real 279 KB PDF: 607 xref entries, 0 broken after cleaning.

## What it cannot do

Stated here as plainly as in the UI, because a remover that claims everything is not useful:

- **Pixel-domain watermarks.** SynthID and its relatives live in the image content, not the
  metadata. Stripping EXIF does nothing to them, and re-encoding does not reliably help — they are
  built to survive it. Verify with a detector rather than trusting any remover.
- **Statistical text watermarks.** See Layer B above.
- **Metadata inside compressed PDF object streams.** A byte-level pass cannot read them. The report
  says so when it detects them instead of claiming a clean file.
- **Encrypted PDFs.** Detected and refused rather than corrupted. Decrypt first (`qpdf --decrypt`).
- **TIFF.** The format addresses its image data through the same IFD tables that hold EXIF, so there
  is no chunk that can be safely dropped.

## Findings are classified, not just listed

The vocabulary comes from upstream, because it is the genuinely useful part:

- `confirmed` — it was present and it is now gone; checkable by hand
- `probable` — present and removed, but the character or field has legitimate uses too
- `informational` — changed, or worth knowing, but not a mark on its own
- `likely false positive` — found, understood, deliberately kept (a joiner inside a family emoji, a title inside an EPUB)

## Verifying the output

Do not take the report's word for it:

```sh
exiftool -a -G1 cleaned.jpg          # everything still in an image
c2patool cleaned.jpg                 # content credentials
qpdf --qdf --object-streams=disable cleaned.pdf out.pdf   # make PDF structure greppable
unzip -l cleaned.docx                # entry list and timestamps
```

If a check disagrees with the report, the check is right.

## Layout

```
watermark-remover/
├── index.html              the app
├── tests.html              the suite, in a browser
├── tests.node.js           the same suite, headless
├── sw.js                   offline cache
└── assets/
    ├── app.css
    └── js/
        ├── bytes.js        CRC32 and byte helpers
        ├── unicode.js      Layer A — the text engine
        ├── images.js       PNG / JPEG / WebP / GIF chunk surgery
        ├── pdf.js          length-preserving PDF metadata blanking
        ├── containers.js   ZIP documents and SVG
        ├── app.js          UI wiring only
        └── tests.js        assertions, shared by both runners
```

No framework, no bundler, no `node_modules`. Open `index.html` and it works.

## Responsible use

For content you own or are authorised to process — taking GPS coordinates out of a photo before you
post it, taking your name off a document before it circulates, removing a tracking string someone
pasted into text they sent you. Passing off machine-written work as your own, defeating attribution
you agreed to, or impersonating someone is not what it is for, and removing a marker does not change
what the content is.

## Credit

The three-layer model, the honest-reporting stance and the finding vocabulary are from
[guillaumemeyer/watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover).
This is an independent browser implementation of those ideas, not a fork of that code.
