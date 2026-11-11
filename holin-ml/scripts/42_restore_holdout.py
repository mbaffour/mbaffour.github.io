"""Build the restore-127 test sets for the v2 endolysin regression.

Background. The subsample test showed the v1 -> v2 loss is composition, not count. Part of that
composition change turned out to be a construction artifact: scripts/27 forms the gold holdout by
drawing 20% of homology CLUSTERS at random (seed 0). v2 was re-clustered over a larger set, the
cluster ids changed, the same seed drew different clusters, and v2's draw landed on larger ones
(631 positives held out, 23%, against 192 / 13% for v1). It swept 127 curated positives (60 pool,
51 UniProt-validated, 16 reviewed) that v1 had trained on into v2's holdout. They are still in the v2
file -- flagged in_gold_holdout, never trained on.

Arms written here, all derived from the v2 file so every record keeps v2's cluster id (no mixing of
cluster-id namespaces between v1 and v2, which would corrupt the family-removal protocol):

  restore127        v2 with exactly those 127 curated records returned to training
  ctrl127_s{0,1,2}  v2 with 127 randomly chosen held-out PFAM-MINED records returned instead --
                    same count, different kind, so restore127 vs ctrl separates "curated" from
                    "127 more records"

Valid for the LOGO benchmark (scripts/40), which never scores the gold holdout and removes homologs of
each query itself. NOT valid for anything shipped: these sets put gold-holdout clusters into training,
which would contaminate scripts/28's frozen-holdout evaluation.

Records are addressed by position in the v2 file, never by id: ids are not unique there.

Usage: python3 scripts/42_restore_holdout.py
"""
import json
from pathlib import Path
import numpy as np

B = Path(__file__).resolve().parent.parent
CUR = {"pool", "validated", "reviewed"}


def main():
    v1 = json.load(open(B / "data/processed/endolysin_positives_v1.json"))
    v2 = json.load(open(B / "data/processed/endolysin_positives.json"))
    v1_train = {r["sequence"] for r in v1 if not r["in_gold_holdout"]}
    v2_train = {r["sequence"] for r in v2 if not r["in_gold_holdout"]}

    # Records are addressed by POSITION, not id: pool records reuse the genome accession as their id
    # (105 ids cover 265 records in v2), so flipping by id silently drags along unrelated records.
    target = [i for i, r in enumerate(v2) if r["in_gold_holdout"] and r["sequence"] in v1_train
              and r["sequence"] not in v2_train and r["tier"] in CUR]
    assert len(target) == 127, len(target)

    def write(name, flip_ix, note):
        flip_ix = set(flip_ix); assert len(flip_ix) == 127
        out = []
        for i, r in enumerate(v2):
            r = dict(r)
            if i in flip_ix:
                r["in_gold_holdout"] = False; r["restored"] = note
            out.append(r)
        p = B / f"data/processed/endolysin_positives_{name}.json"
        p.write_text(json.dumps(out, indent=1))
        n = sum(not r["in_gold_holdout"] for r in out)
        assert n == sum(not r["in_gold_holdout"] for r in v2) + 127, n
        cur = sum((not r["in_gold_holdout"]) and r["tier"] in CUR for r in out)
        print(f"{p.name}: {n} training positives, curated share {cur / n:.3f}")

    write("v2_restore127", target, "curated_from_v1")
    pool = [i for i, r in enumerate(v2) if r["in_gold_holdout"] and r["tier"] == "pfam"
            and r["sequence"] not in v1_train]
    print(f"held-out pfam-mined candidates for the control: {len(pool)}")
    for seed in (0, 1, 2):
        ix = np.random.default_rng(seed).choice(len(pool), size=127, replace=False)
        write(f"v2_ctrl127_s{seed}", [pool[i] for i in ix], "pfam_control")


if __name__ == "__main__":
    main()
