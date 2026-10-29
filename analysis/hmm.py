"""Discrete HMM / Bayes filter over map images for sequence-based localization (place level).

State j = map image j (position m_pos[j]). Observation at time t = similarity vector s_t (query t vs every map image).
  transition  p(j | i, u_t) = (1-eps) * K(m_pos[j] - m_pos[i] - u_t) / Z_i + eps / N     (u_t = odometry, or 0)
  emission    p(s_t | j)   ∝ exp(s_tj / T)
Forward filter b_t ∝ e_t ⊙ (P_t^T b_{t-1}); estimate = argmax b_t. Transition applied through a sparse
neighbour list (map items within `radius` of each other), so cost is O(N * avg_neighbours) per step.
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree


def neighbours(m_pos, radius):
    """sparse pairs (i, j) with ||m_pos[i]-m_pos[j]|| <= radius, and the displacement m_pos[j]-m_pos[i]"""
    tr = cKDTree(m_pos); pairs = tr.query_pairs(radius, output_type="ndarray")
    n = len(m_pos); ii = np.r_[pairs[:, 0], pairs[:, 1], np.arange(n)]; jj = np.r_[pairs[:, 1], pairs[:, 0], np.arange(n)]
    return ii, jj, m_pos[jj] - m_pos[ii]


class TopoHMM:
    def __init__(self, m_pos, sigma=3.0, radius=None, eps=1e-3, odo=False, speed=1.0):
        """sigma: transition std (m); odo=False: random-walk kernel centred on `speed`-free zero displacement
        (|d| <= radius), odo=True: kernel centred on the odometry displacement (vector, map frame)."""
        self.m_pos = np.asarray(m_pos, float); self.n = len(self.m_pos)
        self.sigma, self.eps, self.odo = sigma, eps, odo
        self.radius = radius or (4 * sigma + 3 * speed)
        self.ii, self.jj, self.D = neighbours(self.m_pos, self.radius)

    def P(self, u=None):
        """row-stochastic sparse transition (without the eps-uniform part) for displacement u"""
        d = self.D if u is None else self.D - u[None, :]
        w = np.exp(-0.5 * (d ** 2).sum(1) / self.sigma ** 2)
        P = csr_matrix((w, (self.ii, self.jj)), shape=(self.n, self.n))
        z = np.asarray(P.sum(1)).ravel(); z[z == 0] = 1
        return csr_matrix((w / z[self.ii], (self.ii, self.jj)), shape=(self.n, self.n))

    def filter(self, S, T=0.02, U=None, reset=None):
        """S: (L, N) similarities of one query sequence. U: (L, dim) odometry displacement from t-1 to t (row 0 unused).
        Returns (argmax states (L,), max posterior (L,), posterior entropy (L,))."""
        L = len(S); b = np.full(self.n, 1.0 / self.n); est = np.empty(L, int); pmax = np.empty(L); P0 = None if self.odo else self.P()
        for t in range(L):
            if t > 0:
                P = self.P(U[t]) if self.odo else P0
                b = (1 - self.eps) * (P.T @ b) + self.eps / self.n
            z = (S[t] - S[t].max()) / T; e = np.exp(z)
            b = b * e; b /= b.sum()
            est[t] = b.argmax(); pmax[t] = b[est[t]]
        return est, pmax
