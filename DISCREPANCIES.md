# Factual discrepancies — for your review

Generated during the site audit. **Nothing in this list has been changed.** Each item is a
place where the site, the HTML CV, and the résumé PDF disagree with each other, or where a
claim has drifted out of date. You're the only one who can say which version is correct, so
they're all left as-is pending your call.

Ordered by how much damage each one could do if a PI or recruiter checks.

---

## 1. Your CV does not list your published paper — 🔴 highest severity

The homepage headlines the *Serwaa* genome announcement as **"★ Latest · Published"**
(`index.html:4749-4757`), citing:

> Debrah MA, Awuah MB, Koh A, Ramsey J. *Complete genome sequence of Escherichia Siphophage
> Serwaa.* Microbiology Resource Announcements, 2026. doi:10.1128/mra.01222-25

But `cv-resume/Michael_Baffour_Awuah_CV.html:699-713` — the entire Publications section —
lists **only the bioRxiv preprint**. Neither PDF contains the string "Serwaa" (verified by
decompressing the PDF content streams).

**Consequence:** anyone who reads the homepage claim and then downloads your CV to verify it
finds a candidate with zero peer-reviewed publications. This is the single most likely thing
on the site to cost you credibility.

**Also missing from the site's citation** (`index.html:4749-4757`): article number `e01222-25`
(your own blog knows it — `blog/serwaa-first-paper.html:421`), volume, and PMID.
The preprint entry (`index.html:4760-4770`) omits the PMID/PMCID that the CV has
(`CV.html:709`: PMID 41292803; PMCID PMC12642591).

---

## 2. "Seven novel phages" vs. three — 🔴

Three different numbers for the same body of work:

| Source | Claim |
|---|---|
| `cv-resume/…CV.html:572` | "Isolated, purified, and characterized **seven** novel *E. coli* 4s-infecting bacteriophages" |
| `cv-resume/…CV.html:580` | "genomes of **seven** novel phages" |
| `index.html:3695` (hero stat), `:3762` (About pill) | "**3** Novel Phages" |
| `blog/serwaa-first-paper.html:412` | "I initially thought I had discovered **seven** novel phages, but after further work I realized that only **three** of them were truly unique." |

Your own blog states the seven figure was an error. The CV still asserts it as fact, twice.

---

## 3. A poster is presented as an invited talk — 🔴

`index.html:4505-4507`, in a card headed **"Invited Lectures & Talks"**:

> Delivered department lectures and conference talks on phage N4 lysis inhibition — including
> *"Bacteriophage are prolific bacterial predators"* and *"The Viral Death Race."*

- **"The Viral Death Race"** is a **poster**, not a talk. It's `kind: "poster"` in
  `publications[]` (`index.html:4801-4805`) and tagged `Poster` in the CV (`CV.html:722`).
- **"Bacteriophage are prolific bacterial predators"** appears nowhere in `publications[]`
  or the CV. It exists only as a gallery *filename*: `gallery/gallery-prolific-predators.jpg`.

Billing a poster as an invited lecture is exactly the kind of thing a PI verifies.

---

## 4. Résumé PDF publishes your home address — 🔴 (acted on, see note)

`cv-resume/Michael-Baffour-Awuah-Resume.pdf` carries a home street address in Bryan, TX, on a
public, Google-indexed GitHub Pages site, linked from the About section (`index.html:3777`).

**Action taken:** the file has been removed and unlinked, per your instruction.

**Important caveat:** removing it from the current commit does **not** remove it from git
history — anyone can still retrieve it from an earlier commit, and search engines or the
Wayback Machine may already hold a copy. Purging history requires a `git filter-repo` rewrite
and a force push, which rewrites every commit hash. That's your call; say the word and I'll do
it.

To restore the résumé: re-export without the address and I'll re-link it.

---

## 5. Two different phone numbers

| Source | Number |
|---|---|
| `cv-resume/Michael_Baffour_Awuah_CV.html:502` | (979) 326-6958 |
| `Michael-Baffour-Awuah-Resume.pdf` header | (979) 326-6965 |

One of these does not reach you.

---

## 6. "4th Year PhD" is a year out of date

`index.html:3693` (hero stat) and `:3761` (About pill) both say **4th year**. Your CV records
a start of **Aug 2022** (`CV.html:532`). As of Aug 2026 that is the start of year **5**.

It's in the hero, so it's the first hard fact a visitor reads.

---

## 7. Two different dissertation titles

| Source | Title |
|---|---|
| `cv-resume/…CV.html:537` | "Delaying the Inevitable – Lysis Inhibition in Bacteriophage N4" |
| Résumé PDF | "Bacteriophage N4 Lysis Inhibition – Investigating genetic regulation of controlled cell lysis" |

---

## 8. Four conflicting date ranges between the CV and the résumé

| Item | CV HTML | Résumé PDF |
|---|---|---|
| B.Sc. | Aug 2016 – **Jun** 2020 (`CV.html:544`) | Aug 2016 – **July** 2020 |
| WACCBIP internship | **Jun** – Jul 2022 (`CV.html:590`) | **May** – July 2022 |
| Undergraduate researcher | Jan 2018 – **Jun 2020** (`CV.html:634`) | Jan 2018 – **Aug 2020** |
| Noguchi internship | **Jun – Jul** 2019 (`CV.html:646`) | **July – Aug** 2019 |

---

## 9. A preprint filed under "Peer-Reviewed Publications"

- The résumé PDF lists the bioRxiv preprint under a heading reading **"Peer-Reviewed
  Publications."** A preprint is by definition not peer-reviewed.
- `index.html:4145` has the same problem more subtly: *"Peer-reviewed work, a first-author
  preprint on N4 lysis, and selected talks"* under a section label reading
  "Peer-Reviewed Work · Talks · Posters."

---

## 10. Mentee count told two ways

- `index.html:4514`: "**Four** undergraduates have worked with me during my PhD."
- Résumé PDF: "mentorship of **10+** undergraduate researchers."

Both are defensible (4 at TAMU + 6 at UCC), but a reader holding both documents sees inflation.
Worth stating the split explicitly in one place.

The same card makes three time-sensitive claims with no as-of date: *"Two continue with me in
the Ramsey Lab today; one is now in a biology PhD program; one is applying to medical school."*

---

## 11. Talks card dated 2024–2025, but no 2025 talk exists

`index.html:4504` labels the Invited Lectures card **"2024–2025."** All three oral
presentations in `publications[]` (`index.html:4772-4795`) and in the CV (`CV.html:723-727`)
are **2024**. The only 2025 item anywhere is a poster.

Separately, the résumé PDF claims presentations at "Molecular Genetics of Bacteria & Phages
Meeting (2023, **2025**)" and "Texas ASM Branch Meeting (2023, 2024, **2025**)" — neither
2025 entry exists in the CV or in `publications[]`.

---

## 12. "My first paper" vs. second authorship

`index.html:3873`:

> This is how **I** isolated and characterized *Serwaa*, the novel phage behind **my first
> paper**, named after my grandmother.

The citation (`index.html:4751`) is `Debrah MA, Awuah MB, Koh A, Ramsey J` — you're second
author. Your blog is scrupulously fair about this, crediting Michael Debrah with "genome
annotation, manuscript preparation, and navigating the publication process"
(`blog/serwaa-first-paper.html:434`) and Annie Koh with much of the bench work (`:428`).
The homepage sentence is the only place that isn't.

---

## 13. Darwin Day marked "Annual"

`index.html:4519` dates the Darwin Day outreach card **"Annual."** The CV records exactly one
instance (`CV.html:855`, "Feb 2024").

---

## 14. TailFiber advertises a receptor it doesn't have

`index.html:4243-4249` lists the game's receptors as "LPS, OmpC, LamB, Type IV pili,
**Flagella**." The shipped fiber selector (`index.html:4277-4281`) is "LPS, OmpC, LamB, Pili,
**NfrA**."

Flagella is promised and absent. NfrA — N4's actual receptor, and the most scientifically
interesting one in there — is present and unadvertised.

---

## 15. Skills claim carried forward from an older document

`CV.html:876` has a skill pill reading "BSL2 Culture (**5+ yrs**)", and the résumé says "5+
years of hands-on wet-lab experience." The CV's own history (UCC from 2018 → present) supports
roughly **8**. You're underselling by three years.

---

## 16. Inconsistent AI-authorship disclosure across blog posts

Six posts credit Claude explicitly and gracefully — `plaque-toolkit.html:777,780,880`,
`cellmorphr.html:713`, `hmm-homologue-finder.html`, `cfu-plot-studio.html`,
`genomics-kitchen.html`. Four do not — `gibson-assembly-calculator.html`,
`hmm-discovery-app.html`, `lifexp.html`, `number-tug.html`.

Not a factual error, but a reader who notices the asymmetry may read it as selective. Worth
making consistent in one direction or the other.

---

## Summary of what needs your decision

| # | Question only you can answer |
|---|---|
| 1 | Add the Serwaa paper to the CV (HTML + re-exported PDF)? |
| 2 | Is it three novel phages or seven? |
| 3 | Reword the "Invited Lectures & Talks" card to match the record? |
| 5 | Which phone number is current? |
| 6 | Update to 5th year — and add an expected defense date? |
| 7 | Which dissertation title is the real one? |
| 8 | Which set of dates is correct? |
| 9 | Reclassify the preprint out from under "Peer-Reviewed"? |
| 10 | State the mentee count as "4 at TAMU, 10+ overall"? |
| 11 | Correct the talks card to 2024, and drop the 2025 résumé entries? |
| 12 | Soften "my first paper" to credit co-authorship? |
| 13 | Darwin Day: annual or 2024? |
| 14 | Fix the TailFiber blurb to say NfrA, not Flagella? |
| 15 | Update "5+ yrs" to reflect ~8? |
| 16 | Disclose AI assistance on all posts, or none? |
