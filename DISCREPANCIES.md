# Factual discrepancies — resolution record

Round 1 found sixteen conflicts across the site, the HTML CV and the résumé PDF, and
changed none of them. Round 2 put **every one** of them to you and applied your rulings.
This file is now the record of what was decided, not a to-do list.

Several of your rulings overrode what the repo evidence suggested — those are marked, so
the reasoning is recoverable later.

---

## Resolved

| # | Conflict | Ruling and what changed |
|---|---|---|
| 1 | **CV omitted the published paper.** The homepage headlined *Serwaa* as "★ Latest · Published" while `CV.html` Publications listed only the preprint — a recruiter downloading the CV saw zero publications. | **Fixed.** The full citation now leads the CV's Publications section, with article number `e01222-25`. |
| 2 | **"Seven novel phages"** in the CV vs. "3" on the site vs. your blog saying the seven figure was wrong. | **Your ruling: three throughout.** Both CV bullets now read three. *(Evidence suggested "seven isolated, three novel"; you chose three.)* |
| 3 | **"The Viral Death Race"** cited under "Invited Lectures & Talks" but recorded everywhere as a poster. | **Your ruling: poster only, no talk entry.** Removed from the talks card. |
| 4 | **"Bacteriophage are prolific bacterial predators"** cited as a talk title; it appears nowhere in your records. | **Your ruling: it's a slide title** from the Bio & Chem Sciences Symposium talk already listed. Removed as a separate title; no duplicate entry added. |
| 5 | **Talks card dated 2024–2025** with no 2025 talk in any record. | **Fixed.** Card now dated 2024 and describes your three real oral presentations: Bio & Chem Sciences Symposium, Texas ASM Branch Meeting, BIOGSA. |
| 6 | **"4th Year PhD"** with an Aug 2022 start. | **Fixed** to 5th, in the hero and the About pill. |
| 7 | **Mentee count**: four on the recognition card, ten in the Teaching section. | **Your ruling: four during the PhD, ten overall.** The card now states both. |
| 8 | **"My first paper"** on a second-author paper. | **Your clarification:** you isolated the phage before Annie Koh joined, and she then worked on it too. The card keeps the isolation claim and credits her. |
| 9 | **Darwin Day "Annual"** vs. one CV instance. | **Your ruling: annual is right, 2024 and 2025.** The CV now records both years; the card keeps "Annual". |
| 10 | **TailFiber advertised a Flagella receptor** the game doesn't have, and omitted NfrA — N4's actual receptor — which it does. | **Fixed** to NfrA. |
| 11 | **"BSL2 Culture (5+ yrs)"** where your history supports about eight. | **Your ruling: 8+ yrs.** You were underselling by three years. |
| 12 | **Serwaa citation missing its article number; preprint missing PMID.** | **Fixed.** `e01222-25` and PMID 41292803 / PMCID PMC12642591 now render under each citation. |
| 13 | **Inconsistent AI-authorship disclosure** — six posts credit Claude, four don't. | **Your ruling: leave the current mix.** Deliberate, recorded here so it doesn't get "fixed" by someone later. |

## Mooted by removing the résumé PDF

These four existed only *between* the CV and a résumé that is no longer published. They
need no action now, but they are **constraints for whenever you re-export it** — the
re-exported résumé must agree with the CV on all four:

- **Two phone numbers** — CV says (979) 326-6958; the résumé said (979) 326-6965.
- **Two dissertation titles** — CV: "Delaying the Inevitable – Lysis Inhibition in
  Bacteriophage N4"; the résumé had a different one.
- **Four conflicting date ranges** — B.Sc., WACCBIP internship, undergraduate researcher,
  and Noguchi internship each differed by a month or more.
- **A preprint filed under "Peer-Reviewed Publications."** A preprint is by definition not
  peer-reviewed. (The site's equivalent problem was fixed in round 1 when Publications was
  split from Talks & Posters.)

---

## Still open — needs you

### 1. The home address (highest priority)

The résumé PDF is deleted and unlinked, but it was served from a live public URL, so the
real exposure is caches — which deleting the file does **not** clear. Do these in order:

- [ ] **Google Search Console → Removals → New request** for
      `https://mbaffour.github.io/cv-resume/Michael-Baffour-Awuah-Resume.pdf`.
      The URL already returns 404, which is what makes the removal permanent rather than
      the temporary 6-month kind.
- [ ] **Wayback Machine** — check `https://web.archive.org/web/*/mbaffour.github.io/*` for
      a snapshot of the PDF; if one exists, email `info@archive.org` from an address on the
      domain requesting exclusion.
- [ ] **Optional, after the PR merges:** purge it from git history with
      `git filter-repo --invert-paths --path cv-resume/Michael-Baffour-Awuah-Resume.pdf`
      followed by a force-push. Cheap here — one contributor, no forks — but it is the
      smaller half of the fix, and GitHub can keep the unreachable object fetchable by SHA
      until its garbage collection runs. Permanently purging that needs a note to GitHub
      Support. **Ask before running this**: force-pushing rewritten history isn't reversible.
- [ ] Re-export the résumé without the address and I'll re-link it.

### 2. Smaller things I left alone

- **Posters carry no author lists.** The seven poster entries in `assets/js/main.js` have a
  title, venue and year but no `authors` field, unlike your talks and papers. More visible
  now that they have their own section.
- **"Annual" on the Darwin Day card.** You ruled to keep it, and the record is 2024 and
  2025. Since February 2026 has passed, "Annual" reads as ongoing where **"2024–2025"**
  would be exact. Your call — say the word and I'll change it.
- **Time-sensitive mentee outcomes have no as-of date.** "One is applying to medical
  school" will go stale quietly.
