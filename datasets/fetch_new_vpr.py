#!/usr/bin/env python3
"""Fetch and standardise new sequential VPR datasets (resumable: every finished step is skipped on re-run).
Output layout (one folder per Kaggle dataset, uploaded to nhatlong1103):
  <OUT>/brisbane-event-vpr-frames/<traversal>/frames/<traversal>_<k:05d>.jpg  (1 frame/s, 640 px wide)
                                   <traversal>/frames.csv  name,t_video_s,t_utc,lat,lon,east_m,north_m,speed_mps
  <OUT>/qut-day-night-lateral/GardensPointWalking/..., SouthBankBicycle/...   (original zips unpacked)
Sources (licences kept in each folder's SOURCE.md):
  Brisbane-Event-VPR, Fischer & Milford RA-L 2020, zenodo.org/record/4302805, CC BY-NC-SA 4.0 (consumer-camera mp4 + nmea)
  Day-and-night-with-lateral-pose-change (Gardens Point Walking, SouthBank Bicycle), QUT, zenodo.org/records/4590133, CC BY 4.0
Usage: fetch_new_vpr.py <OUT> [--fps 1] [--width 640]"""
import os, sys, json, subprocess, zipfile, csv, math, datetime, urllib.request

OUT = sys.argv[1]
FPS = float(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 1.0
WID = int(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else 640
DL = os.path.join(OUT, "_downloads"); os.makedirs(DL, exist_ok=True)
BRIS = ["20200421_170039-sunset1", "20200422_172431-sunset2", "20200424_151015-daytime",
        "20200427_181204-night", "20200428_091154-morning", "20200429_061912-sunrise"]


def fetch(rec, key):
    dst = os.path.join(DL, key)
    if os.path.exists(dst) and not os.path.exists(dst + ".part"):
        return dst
    url = f"https://zenodo.org/api/records/{rec}/files/{key}/content"
    open(dst + ".part", "w").close()
    subprocess.run(["curl", "-sS", "-L", "--retry", "5", "-C", "-", "-o", dst, url], check=True)
    os.remove(dst + ".part"); print("downloaded", key, os.path.getsize(dst) // 2**20, "MB", flush=True)
    return dst


def nmea_fixes(path):
    """$GPRMC (time, date, lat, lon, speed). Returns list of (utc datetime, lat, lon, speed m/s)."""
    out = []
    for ln in open(path, errors="ignore"):
        p = ln.strip().split(",")
        if not p[0].endswith("RMC") or len(p) < 10 or p[2] != "A":
            continue
        try:
            t = datetime.datetime.strptime(p[9] + p[1].split(".")[0], "%d%m%y%H%M%S").replace(tzinfo=datetime.timezone.utc)
            t += datetime.timedelta(seconds=float("0." + p[1].split(".")[1]) if "." in p[1] else 0)
            lat = float(p[3][:2]) + float(p[3][2:]) / 60 * 1; lat = -lat if p[4] == "S" else lat
            lon = float(p[5][:3]) + float(p[5][3:]) / 60; lon = -lon if p[6] == "W" else lon
            out.append((t, lat, lon, float(p[7] or 0) * 0.514444))
        except Exception:
            continue
    return out


def to_local_m(lat, lon, lat0, lon0):
    R = 6378137.0
    return (math.radians(lon - lon0) * R * math.cos(math.radians(lat0)), math.radians(lat - lat0) * R)


def brisbane():
    root = os.path.join(OUT, "brisbane-event-vpr-frames"); os.makedirs(root, exist_ok=True)
    og = os.path.join(root, "origin.json")             # persisted: a resumed run must keep the SAME local frame
    ref = tuple(json.load(open(og))["local_origin_latlon"]) if os.path.exists(og) else None
    for tr in BRIS:
        d = os.path.join(root, tr.split("-")[1]); fr = os.path.join(d, "frames"); done = os.path.join(d, "frames.csv")
        if os.path.exists(done):
            continue
        mp4 = fetch(4302805, tr + "_concat.mp4"); nm = fetch(4302805, tr + "_concat.nmea")
        os.makedirs(fr, exist_ok=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                             "default=nw=1:nk=1", mp4], text=True))
        name = tr.split("-")[1]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-vf", f"fps={FPS},scale={WID}:-2",
                        "-q:v", "3", os.path.join(fr, f"{name}_%05d.jpg")], check=True)
        fixes = nmea_fixes(nm)
        if not fixes:
            raise RuntimeError("no RMC fixes in " + nm)
        # video and nmea are recorded by the same camera and synchronised (dataset README): video t=0 <-> first fix
        t0 = fixes[0][0]; ts = [(f[0] - t0).total_seconds() for f in fixes]
        if ref is None:
            ref = (fixes[0][1], fixes[0][2]); json.dump({"local_origin_latlon": ref}, open(og, "w"))
        imgs = sorted(os.listdir(fr)); rows = []
        for k, im in enumerate(imgs):
            tv = k / FPS                                   # ffmpeg fps filter: output frame k has pts k/FPS
            j = min(range(len(ts)), key=lambda i: abs(ts[i] - tv))
            if abs(ts[j] - tv) > 2.0:
                continue                                   # no GPS within 2 s -> frame kept but unlabeled
            lat, lon, sp = fixes[j][1], fixes[j][2], fixes[j][3]
            e, n = to_local_m(lat, lon, *ref)
            rows.append([im, f"{tv:.2f}", (t0 + datetime.timedelta(seconds=tv)).isoformat(), f"{lat:.7f}", f"{lon:.7f}",
                         f"{e:.2f}", f"{n:.2f}", f"{sp:.2f}"])
        with open(done + ".tmp", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["name", "t_video_s", "t_utc", "lat", "lon", "east_m", "north_m", "speed_mps"]); w.writerows(rows)
        os.replace(done + ".tmp", done)
        print(f"{name}: video {dur:.0f}s, {len(imgs)} frames, {len(rows)} with GPS, {len(fixes)} fixes", flush=True)
        os.remove(mp4)                                     # keep disk small; nmea kept
    open(os.path.join(root, "SOURCE.md"), "w").write(
        "# Brisbane-Event-VPR (consumer-camera frames)\nFischer & Milford, 'Event-Based Visual Place Recognition With "
        "Ensembles of Temporal Windows', IEEE RA-L 2020. Source: https://zenodo.org/record/4302805 (CC BY-NC-SA 4.0).\n"
        f"Frames extracted from *_concat.mp4 at {FPS} fps, width {WID}px; GPS from *_concat.nmea ($GPRMC), nearest fix "
        "(<=2 s). east/north in metres relative to the first fix of the first traversal (equirectangular).\n"
        "Six traversals of the same ~8 km route: sunset1, sunset2, daytime, night, morning, sunrise.\n")


def qut():
    root = os.path.join(OUT, "qut-day-night-lateral"); os.makedirs(root, exist_ok=True)
    for key, probe in (("GardensPointWalking.zip", "day_left"), ("SouthBankBicycle.zip", "frames1")):
        if os.path.isdir(os.path.join(root, probe)) or os.path.isdir(os.path.join(root, key[:-4], probe)):
            continue
        z = fetch(4590133, key)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(root)
        print("unpacked", key, flush=True)
    open(os.path.join(root, "SOURCE.md"), "w").write(
        "# Day and Night with Lateral Pose Change (QUT)\nGardens Point Walking (day_left, day_right, night_right; frame i of "
        "each traversal shows place i) and SouthBank Bicycle. Glover et al. / Suenderhauf et al.; source "
        "https://zenodo.org/records/4590133 (CC BY 4.0).\n")


def rebuild_csv():
    """Recompute every Brisbane frames.csv from the kept .nmea files (no video download): used after the 28/11 fix
    of the frame-time convention (k/FPS instead of (k+0.5)/FPS)."""
    root = os.path.join(OUT, "brisbane-event-vpr-frames"); ref = tuple(json.load(open(os.path.join(root, "origin.json")))["local_origin_latlon"])
    for tr in BRIS:
        name = tr.split("-")[1]; d = os.path.join(root, name); nm = os.path.join(DL, tr + "_concat.nmea")
        fixes = nmea_fixes(nm); t0 = fixes[0][0]; ts = [(f[0] - t0).total_seconds() for f in fixes]; rows = []
        for k, im in enumerate(sorted(os.listdir(os.path.join(d, "frames")))):
            tv = k / FPS; j = min(range(len(ts)), key=lambda i: abs(ts[i] - tv))
            if abs(ts[j] - tv) > 2.0: continue
            lat, lon, sp = fixes[j][1], fixes[j][2], fixes[j][3]; e, n = to_local_m(lat, lon, *ref)
            rows.append([im, f"{tv:.2f}", (t0 + datetime.timedelta(seconds=tv)).isoformat(), f"{lat:.7f}", f"{lon:.7f}", f"{e:.2f}", f"{n:.2f}", f"{sp:.2f}"])
        with open(os.path.join(d, "frames.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["name", "t_video_s", "t_utc", "lat", "lon", "east_m", "north_m", "speed_mps"]); w.writerows(rows)
        print("rebuilt", name, len(rows), flush=True)


if __name__ == "__main__":
    if "--rebuild-csv" in sys.argv: rebuild_csv(); sys.exit(0)
    qut(); brisbane(); print("FETCH_DONE", flush=True)
