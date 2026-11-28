"""Non-HMM baselines on a similarity matrix S (T,M)."""
import numpy as np


def single_image_post(S, tau):
    z = S.astype(np.float64) / tau; z -= z.max(1, keepdims=True); p = np.exp(z)
    return p / p.sum(1, keepdims=True)


def seqslam_causal(S, L=10, vels=(0.5, 0.75, 1.0, 1.25, 1.5), enhance=10, reset_mask=None):
    """Causal SeqSLAM (Milford & Wyeth 2012, adapted to similarities, vectorised):
    score(t,j) = max_v mean_{k<min(L, t-start+1)} S~[t-k, round(j - v*k)], S~ optionally locally contrast-
    enhanced along the map axis (window 2*enhance+1). Returns (T,M) scores."""
    T, M = S.shape
    Se = S.astype(np.float32).copy()
    if enhance:
        from scipy.ndimage import uniform_filter1d
        mu = uniform_filter1d(Se, size=2 * enhance + 1, axis=1, mode="nearest")
        sq = uniform_filter1d(Se ** 2, size=2 * enhance + 1, axis=1, mode="nearest")
        Se = (Se - mu) / np.sqrt(np.maximum(sq - mu ** 2, 1e-8))
    start = np.zeros(T, int)
    if reset_mask is not None:
        cur = 0
        for t in range(T):
            if reset_mask[t]: cur = t
            start[t] = cur
    age = np.arange(T) - start                      # frames since sequence start
    best = np.full((T, M), -np.inf, np.float32)
    for v in vels:
        acc = np.zeros((T, M), np.float32); cnt = np.zeros((T, M), np.float32)
        for k in range(L):
            sh = int(round(v * k))
            if sh >= M: break
            valid_t = age >= k                       # row t-k belongs to the same sequence
            src = np.zeros((T, M), np.float32)
            src[k:, sh:] = Se[:T - k, :M - sh] if k > 0 else Se[:, :M - sh]
            m = np.zeros((T, M), np.float32); m[k:, sh:] = 1.0
            m[~valid_t] = 0.0
            acc += src * m; cnt += m
        sc = acc / np.maximum(cnt, 1)
        sc[cnt == 0] = -np.inf
        best = np.maximum(best, sc)
    return best


def seqslam_centred(S, L=10, vels=(0.5, 0.75, 1.0, 1.25, 1.5), enhance=0, reset_mask=None):
    """Centred (offline) SeqSLAM / SeqMatch as in OpenSeqSLAM and the SeqNet code (A34): the trajectory is centred on
    query t, using frames t-h..t+h (h = L//2) of the SAME sequence (truncated at sequence boundaries):
    score(t,j) = max_v mean_{o=-h..h} S~[t+o, round(j + v*o)]. Uses h FUTURE frames (not causal). Returns (T,M)."""
    T, M = S.shape; h = L // 2
    Se = S.astype(np.float32).copy()
    if enhance:
        from scipy.ndimage import uniform_filter1d
        mu = uniform_filter1d(Se, size=2 * enhance + 1, axis=1, mode="nearest")
        sq = uniform_filter1d(Se ** 2, size=2 * enhance + 1, axis=1, mode="nearest")
        Se = (Se - mu) / np.sqrt(np.maximum(sq - mu ** 2, 1e-8))
    sid = np.zeros(T, int)
    if reset_mask is not None:
        sid = np.cumsum(reset_mask.astype(int))
    best = np.full((T, M), -np.inf, np.float32)
    for v in vels:
        acc = np.zeros((T, M), np.float32); cnt = np.zeros((T, M), np.float32)
        for o in range(-h, h + 1):
            sh = int(round(v * o))
            if abs(sh) >= M or abs(o) >= T: continue
            src = np.zeros((T, M), np.float32); m = np.zeros((T, M), np.float32)
            ts, te = max(0, -o), min(T, T - o)                    # rows t with t+o inside [0, T)
            js, je = max(0, -sh), min(M, M - sh)                  # cols j with j+sh inside [0, M)
            if ts >= te or js >= je: continue
            src[ts:te, js:je] = Se[ts + o:te + o, js + sh:je + sh]; m[ts:te, js:je] = 1.0
            same = np.zeros(T, bool); same[ts:te] = sid[ts:te] == sid[ts + o:te + o]
            m[~same] = 0.0
            acc += src * m; cnt += m
        sc = acc / np.maximum(cnt, 1); sc[cnt == 0] = -np.inf
        best = np.maximum(best, sc)
    return best
