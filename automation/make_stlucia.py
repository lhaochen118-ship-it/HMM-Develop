"""St Lucia Multiple Times of Day (Glover et al. ICRA 2010; Hugging Face mirror medwa126/UQStLuciaMultipleToD, 10 traversals of one
suburban route in Brisbane, 08:45-15:45 on two days two weeks apart, 640 x 480 roof webcam, 15 fps, GPS) -> frames + metadata in
the layout of the other dumps (Entry 36).
Positions: fGPS.txt gives one GPS fix per video frame, held constant between 1 Hz fixes; the position at every frame is the
linear interpolation (in frame index) between the frames where the fix changes, converted to a local metric ENU frame shared by
all traversals (equirectangular at the first fix of the first traversal; < 0.1 % scale error over a 3 km area). Frames are kept
every SPACING metres of interpolated path (default 5 m, the GPS subsampling of SafeVPR'26), the stationary start / end removed.
Output: <out>/img/<trav>/<frame>.jpg (resized to 480 x 360), <out>/meta/stlucia_<trav>.npz (names = frame indices, C (n, 2), t = frame
time in s at 15 fps). Usage: make_stlucia.py <raw_dir> <out_dir> [--spacing 5]"""
import sys, os
import numpy as np

R_EARTH = 6371000.0


def positions(fgps, lat0=None, lon0=None):
    g = np.loadtxt(fgps, delimiter=","); lat, lon = -g[:, 0], g[:, 1]          # file stores |latitude| (southern hemisphere)
    lat0 = lat[0] if lat0 is None else lat0; lon0 = lon[0] if lon0 is None else lon0
    x = R_EARTH * np.cos(np.deg2rad(lat0)) * np.deg2rad(lon - lon0); y = R_EARTH * np.deg2rad(lat - lat0)
    P = np.c_[x, y]; ch = np.r_[0, np.flatnonzero(np.any(np.diff(P, axis=0) != 0, axis=1)) + 1]   # frames where the fix changes
    fi = np.arange(len(P)); Pi = np.c_[np.interp(fi, ch, P[ch, 0]), np.interp(fi, ch, P[ch, 1])]
    return Pi, ch, lat0, lon0


def main():
    raw, out = sys.argv[1], sys.argv[2]
    sp = float(sys.argv[sys.argv.index("--spacing") + 1]) if "--spacing" in sys.argv else 5.0
    import cv2
    travs = sorted(d for d in os.listdir(raw) if os.path.isdir(os.path.join(raw, d)))
    os.makedirs(os.path.join(out, "meta"), exist_ok=True); lat0 = lon0 = None
    for tr in travs:
        P, ch, lat0, lon0 = positions(os.path.join(raw, tr, "fGPS.txt"), lat0, lon0)
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        lo, hi = ch[1] if len(ch) > 1 else 0, ch[-1]                          # drop the stationary start / end
        keep, last = [], -np.inf
        for f in range(lo, hi + 1):
            if d[f] - last >= sp: keep.append(f); last = d[f]
        keep = np.array(keep); kset = set(keep.tolist())
        od = os.path.join(out, "img", tr); os.makedirs(od, exist_ok=True)
        cap = cv2.VideoCapture(os.path.join(raw, tr, "webcam_video.avi")); f = 0; n_ok = 0
        while True:
            ok, im = cap.read()
            if not ok: break
            if f in kset:
                cv2.imwrite(os.path.join(od, f"{f:06d}.jpg"), cv2.resize(im, (480, 360), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92]); n_ok += 1
            f += 1
        keep = keep[keep < f]
        np.savez(os.path.join(out, "meta", f"stlucia_{tr}.npz"), names=np.array([f"{k:06d}" for k in keep]), C=P[keep].astype(np.float64),
                 t=keep / 15.0, lat0=lat0, lon0=lon0)
        print(f"{tr}: {len(keep)} frames every {sp} m, path {d[hi] - d[lo]:.0f} m, video frames {f}, written {n_ok}", flush=True)


if __name__ == "__main__":
    main()
