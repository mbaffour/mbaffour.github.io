/* Source of truth for the #poetry section on index.html.

   The poems go up on Instagram first. They are typeset here as real text
   rather than embedded as post cards, because a poem living inside an image
   is invisible to search and unreadable to a screen reader — and the type on
   this site is nicer than Instagram's.

   TO ADD A POEM
     1. copy the text into `lines` — one string per line of verse,
        and an empty string "" wherever a stanza break goes
     2. `url` is the Instagram permalink: the ⋯ menu on the post → "Copy link"
     3. `iso` sorts the list (newest first) and feeds <time datetime>;
        `date` is what a reader actually sees

   Everything except `lines` is optional. A poem with no `url` simply renders
   without the "Read on Instagram" link.

   INSTAGRAM_HANDLE drives the follow link at the foot of the section. Left as
   null, every Instagram link on the page disappears rather than 404ing, so a
   half-filled-in file never ships a broken link. */
const INSTAGRAM_HANDLE = null;   // e.g. 'mbaffour' — no leading @

const poems = [
    /* Template — copy this, fill it in, delete the comment markers.
    {
        title: "Harmattan",
        date: "March 2026", iso: "2026-03-14",
        tags: ["Ghana"],
        lines: [
            "The dust comes down from the Sahara",
            "and everything softens at the edges,",
            "",
            "even the arguments."
        ],
        note: "Written on a plane back to Accra.",
        url: "https://www.instagram.com/p/XXXXXXXXXXX/"
    },
    */
];
