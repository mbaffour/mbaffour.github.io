/* Starting XI — the "Off the pitch" widget.
   Eleven things I actually rely on, arranged 4-3-3. Click a shirt to read the
   scouting report. Built the same way as the rest of the site: no framework, no
   network, and it degrades to a plain list if this file never loads. */
(function () {
    "use strict";

    var SQUAD = [
        { n: 1,  pos: "GK",  x: 50, y: 90, name: "Controls & replicates",
          role: "Goalkeeper",
          note: "Nothing else on this list matters if the blank is wrong. Boring, unglamorous, and the reason any of the rest is publishable." },
        { n: 2,  pos: "RB",  x: 18, y: 72, name: "Molecular cloning",
          role: "Right back",
          note: "Gibson, restriction, site-directed mutagenesis. If I want to know what a gene does, this is how I take it away and see what breaks." },
        { n: 4,  pos: "CB",  x: 38, y: 76, name: "Phage isolation",
          role: "Centre back",
          note: "Sewage, plaque picks, and patience. Three novel phages so far — one of them named after my grandmother." },
        { n: 5,  pos: "CB",  x: 62, y: 76, name: "Genome assembly & annotation",
          role: "Centre back",
          note: "A phage genome is only useful once you know where the genes are and which ones nobody has seen before." },
        { n: 3,  pos: "LB",  x: 82, y: 72, name: "CRISPR engineering",
          role: "Left back",
          note: "Targeted knockouts in the phage and the host. The cleanest way to turn a correlation into a cause." },
        { n: 6,  pos: "CM",  x: 28, y: 50, name: "Experimental design",
          role: "Holding midfield",
          note: "Sits deepest, touches everything. Most failed experiments were lost here, days before anyone pipetted anything." },
        { n: 8,  pos: "CM",  x: 50, y: 46, name: "RNA-seq & DESeq2",
          role: "Central midfield",
          note: "Which genes the phage turns on, when, and by how much. The transcriptome is where lysis timing stops being a guess." },
        { n: 10, pos: "CM",  x: 72, y: 50, name: "R & Python pipelines",
          role: "Attacking midfield",
          note: "The connective tissue. Turns a folder of plate-reader CSVs into a figure I trust, the same way every time." },
        { n: 7,  pos: "RW",  x: 20, y: 24, name: "Tool building",
          role: "Right wing",
          note: "Sixteen-odd open tools, all browser-first and privacy-first. Each one started as something that annoyed me twice." },
        { n: 9,  pos: "ST",  x: 50, y: 16, name: "Lysis inhibition in N4",
          role: "Centre forward",
          note: "The thesis. How one phage decides not to kill its host yet, and what it builds with the extra time — up to ~3,000 particles per cell." },
        { n: 11, pos: "LW",  x: 80, y: 24, name: "Teaching & mentoring",
          role: "Left wing",
          note: "Nine courses, two universities, ten undergraduates at the bench. Explaining it is how I find out whether I understand it." }
    ];

    var root = document.getElementById('pitchWidget');
    if (!root) return;

    var pitch = root.querySelector('.pitch-svg');
    var panel = root.querySelector('.pitch-detail');
    var fallback = root.querySelector('.pitch-fallback');
    if (!pitch || !panel) return;

    // The plain list is the no-JS view; once we're here we can replace it.
    if (fallback) fallback.hidden = true;
    root.classList.add('is-live');

    var NS = 'http://www.w3.org/2000/svg';
    var selected = null;

    function show(p) {
        selected = p.n;
        panel.innerHTML =
            '<span class="pd-role">' + p.role + ' &middot; #' + p.n + '</span>' +
            '<h4 class="pd-name">' + p.name + '</h4>' +
            '<p class="pd-note">' + p.note + '</p>';
        Array.prototype.forEach.call(pitch.querySelectorAll('.shirt'), function (g) {
            var on = g.getAttribute('data-n') === String(p.n);
            g.classList.toggle('on', on);
            g.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
    }

    SQUAD.forEach(function (p) {
        var g = document.createElementNS(NS, 'g');
        g.setAttribute('class', 'shirt');
        g.setAttribute('data-n', String(p.n));
        g.setAttribute('tabindex', '0');
        g.setAttribute('role', 'button');
        g.setAttribute('aria-pressed', 'false');
        // The accessible name carries the content, so a screen reader gets the
        // squad without having to interpret a drawing.
        g.setAttribute('aria-label', p.role + ', number ' + p.n + ': ' + p.name);

        // Invisible, larger hit area. The visible disc is ~32 px across on a
        // phone, under the 44 px touch-target minimum; widening the disc itself
        // would crowd the formation, so the target and the drawing are separate.
        var hit = document.createElementNS(NS, 'circle');
        hit.setAttribute('cx', p.x); hit.setAttribute('cy', p.y); hit.setAttribute('r', '8');
        hit.setAttribute('class', 'shirt-hit');

        var c = document.createElementNS(NS, 'circle');
        c.setAttribute('cx', p.x); c.setAttribute('cy', p.y); c.setAttribute('r', '5.4');
        c.setAttribute('class', 'shirt-disc');

        var t = document.createElementNS(NS, 'text');
        t.setAttribute('x', p.x); t.setAttribute('y', p.y);
        t.setAttribute('class', 'shirt-num');
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('dominant-baseline', 'central');
        t.textContent = String(p.n);

        var l = document.createElementNS(NS, 'text');
        l.setAttribute('x', p.x); l.setAttribute('y', p.y + 9.6);
        l.setAttribute('class', 'shirt-pos');
        l.setAttribute('text-anchor', 'middle');
        l.textContent = p.pos;

        g.appendChild(hit); g.appendChild(c); g.appendChild(t); g.appendChild(l);
        g.addEventListener('click', function () { show(p); });
        g.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(p); }
        });
        pitch.appendChild(g);
    });

    show(SQUAD[9]);   // kick off on the centre forward — the thesis
})();
