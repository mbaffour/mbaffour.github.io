"""Feature extraction shared by training and genome prediction.

1) Interpretable biophysical features (no external tools): length, Kyte-Doolittle hydropathy TM segments, terminal charges,
   amino-acid composition. TM segments here are a simple hydropathy heuristic (window 19, threshold 1.6; Kyte & Doolittle 1982),
   not a topology predictor; they are model inputs, not reported topology.
2) ESM-2 protein language-model embeddings (facebook/esm2_t12_35M_UR50D, mean over residues, 480-d), loaded from
   safetensors via HuggingFace transformers. Cached per sequence SHA-256.
"""
import hashlib
from pathlib import Path
import numpy as np

AA = "ACDEFGHIKLMNPQRSTVWY"
KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9,
      "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}
WIN, THR, MIN_TM = 19, 1.6, 15


def tm_segments(seq):
    h = np.array([KD.get(a, 0.0) for a in seq])
    if len(seq) < WIN: return []
    avg = np.convolve(h, np.ones(WIN) / WIN, mode="valid")  # avg[i] covers residues i..i+WIN-1
    cover = np.zeros(len(seq), bool)
    for i in np.where(avg >= THR)[0]: cover[i:i + WIN] = True
    segs, i = [], 0
    while i < len(seq):
        if cover[i]:
            j = i
            while j + 1 < len(seq) and cover[j + 1]: j += 1
            if j - i + 1 >= MIN_TM: segs.append((i, j))
            i = j + 1
        else: i += 1
    return segs


def charge(s):
    return sum(a in "KR" for a in s) - sum(a in "DE" for a in s)


HAND_NAMES = (["length", "log_length", "n_tm", "tm_fraction", "first_tm_start_frac", "last_tm_end_to_cterm", "max_window_hydropathy",
               "cterm20_K+R", "cterm20_D+E", "cterm20_net_charge", "cterm30_net_charge", "nterm20_net_charge", "net_charge_per_res",
               "frac_charged", "frac_hydrophobic", "frac_G+P"] + [f"aac_{a}" for a in AA])


def handcrafted(seq):
    L = len(seq); segs = tm_segments(seq)
    h = np.array([KD.get(a, 0.0) for a in seq]); mw = np.convolve(h, np.ones(min(WIN, L)) / min(WIN, L), mode="valid").max()
    c20, c30, n20 = seq[-20:], seq[-30:], seq[:20]
    f = [L, np.log(L), len(segs), sum(b - a + 1 for a, b in segs) / L, (segs[0][0] / L) if segs else 1.0, (L - 1 - segs[-1][1]) if segs else L, mw,
         sum(a in "KR" for a in c20), sum(a in "DE" for a in c20), charge(c20), charge(c30), charge(n20), charge(seq) / L,
         sum(a in "KRDEH" for a in seq) / L, sum(a in "AVILMFWY" for a in seq) / L, sum(a in "GP" for a in seq) / L]
    f += [seq.count(a) / L for a in AA]
    return np.array(f, dtype=float)


def sha(seq): return hashlib.sha256(seq.encode()).hexdigest()


class ESM:
    MODEL = "facebook/esm2_t12_35M_UR50D"
    MAXLEN = 1022

    def __init__(self, cache_dir):
        import torch
        from transformers import AutoTokenizer, EsmModel
        torch.set_num_threads(4)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(self.MODEL)
        self.model = EsmModel.from_pretrained(self.MODEL, use_safetensors=True, add_pooling_layer=False).eval()
        self.cache = Path(cache_dir); self.cache.mkdir(parents=True, exist_ok=True)

    def embed(self, seqs, batch_tokens=12000):
        """mean-pooled last-layer embeddings; sequences longer than MAXLEN are embedded in windows and averaged by length."""
        out = [None] * len(seqs); todo = []
        for i, s in enumerate(seqs):
            p = self.cache / f"{sha(s)}.npy"
            if p.exists(): out[i] = np.load(p)
            else: todo.append(i)
        todo.sort(key=lambda i: len(seqs[i]))
        b, n = [], 0
        def run(batch):
            chunks = []
            for i in batch:
                s = seqs[i]
                for k in range(0, len(s), self.MAXLEN): chunks.append((i, s[k:k + self.MAXLEN]))
            enc = self.tok([c for _, c in chunks], return_tensors="pt", padding=True)
            with self.torch.no_grad(): hs = self.model(**enc).last_hidden_state
            m = enc["attention_mask"].clone(); m[:, 0] = 0  # drop <cls>
            for r in range(m.shape[0]): m[r, int(enc["attention_mask"][r].sum()) - 1] = 0  # drop <eos>
            vec = (hs * m[..., None]).sum(1).numpy(); cnt = m.sum(1).numpy()
            agg = {}
            for (i, _), v, c in zip(chunks, vec, cnt):
                a = agg.setdefault(i, [np.zeros_like(v), 0]); a[0] += v; a[1] += c
            for i, (v, c) in agg.items():
                e = (v / c).astype(np.float32); out[i] = e; np.save(self.cache / f"{sha(seqs[i])}.npy", e)
        for i in todo:
            L = min(len(seqs[i]), self.MAXLEN) + 2
            if b and (len(b) + 1) * L > batch_tokens: run(b); b = []
            b.append(i)
        if b: run(b)
        return np.stack(out)


# ---------------------------------------------------------------------------------------------------------------
# TM-anchored local features.
#
# Why these exist. Mean-pooled embeddings and whole-protein composition describe a 218-aa protein as a whole, so a
# 30-residue membrane anchor is averaged into ~190 residues of soluble domain. That is exactly how the model loses
# T4 holin T and T5 C1 (both ~218 aa, single N-terminal TM at 24-54 and 16-47, long C-terminal tail): under
# leave-one-genome-out both score 0.0000.
#
# Generic sliding-window features do not fix it either. "C-terminal charge of the window" is meaningless when the
# window ends mid-protein -- for T4 t it flips from +2 to -3 purely because the window stops at residue 100.
#
# So these features describe the parts a holin is actually made of: the anchor TM segment, the charge on each side
# of it (the positive-inside asymmetry), and the largest non-TM stretch treated as its own domain.
LOCAL_NAMES = ["n_tm", "anchor_tm_len", "anchor_tm_start_frac", "anchor_tm_hydropathy", "flank_N20_charge",
               "flank_C20_charge", "flank_charge_asymmetry", "soluble_len", "soluble_frac", "soluble_net_charge",
               "soluble_charge_per_res", "soluble_frac_hydrophobic", "anchor_in_n_terminal_third",
               "residues_before_first_tm", "residues_after_last_tm", "n_tm_in_first_100", "tm_residue_frac"]


def _charge(s): return sum((a in "KR") - (a in "DE") for a in s)


def local(seq, flank=40):
    """TM-anchored features, plus the sub-sequence (anchor TM +/- `flank`) to embed as the protein's membrane domain.

    Returns (vector, window_sequence). With no TM segment the vector is zeroed apart from the length-derived
    entries and the window is the N-terminal 2*flank residues, so the caller never has to special-case it.
    """
    L = len(seq)
    segs = tm_segments(seq)
    if not segs:
        v = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, float(L), 1.0, float(_charge(seq)), _charge(seq) / max(L, 1),
             sum(a in "AVILMFWC" for a in seq) / max(L, 1), 0.0, float(L), 0.0, 0.0, 0.0]
        return v, seq[:2 * flank]
    a_s, a_e = max(segs, key=lambda s: s[1] - s[0])          # longest segment is the anchor
    tm = seq[a_s - 1:a_e]
    before, after = seq[max(0, a_s - 1 - 20):a_s - 1], seq[a_e:a_e + 20]
    # the largest stretch of the protein that is not in any TM segment: the soluble domain
    cuts, prev = [], 0
    for s, e in sorted(segs):
        if s - 1 > prev: cuts.append((prev, s - 1))
        prev = e
    if prev < L: cuts.append((prev, L))
    sol = max(cuts, key=lambda c: c[1] - c[0]) if cuts else (0, 0)
    sseq = seq[sol[0]:sol[1]]
    tm_res = sum(e - s + 1 for s, e in segs)
    v = [float(len(segs)), float(a_e - a_s + 1), (a_s - 1) / max(L, 1),
         float(np.mean([KD.get(c, 0.0) for c in tm])) if tm else 0.0,
         float(_charge(before)), float(_charge(after)), float(_charge(after) - _charge(before)),
         float(len(sseq)), len(sseq) / max(L, 1), float(_charge(sseq)), _charge(sseq) / max(len(sseq), 1),
         sum(a in "AVILMFWC" for a in sseq) / max(len(sseq), 1),
         1.0 if (a_s - 1) < L / 3 else 0.0, float(sorted(segs)[0][0] - 1), float(L - sorted(segs)[-1][1]),
         float(sum(1 for s, e in segs if s <= 100)), tm_res / max(L, 1)]
    w0, w1 = max(0, a_s - 1 - flank), min(L, a_e + flank)
    return v, seq[w0:w1]
