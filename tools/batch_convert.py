#!/usr/bin/env python3
"""shot2pdf batch CLI: photos -> quad detection (Otsu bright-region, Canny fallback)
-> perspective warp -> resize long edge -> JPEG q~0.35 -> single PDF.

Usage: python3 batch_convert.py OUT_DIR IMG1 [IMG2 ...]
Requires: opencv-python-headless, numpy, pillow
"""
import cv2, numpy as np, sys, os

def order_pts(pts):
    pts = np.array(pts, dtype="float32")
    s = pts.sum(axis=1); d = np.diff(pts, axis=1)
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)],
                     pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")

def detect_quad(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Primary: Otsu bright region (dark room / bright screen or paper)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cand = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.08 * w * h:
            continue
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4:
            cand.append(("otsu", approx.reshape(-1, 2)))
    if cand:
        return max(cand, key=lambda t: cv2.contourArea(cv2.convexHull(t[1])))
    # Fallback: Canny + dilate + external
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.dilate(cv2.Canny(blur, 50, 150), np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cand = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.08 * w * h:
            continue
        approx = cv2.approxPolyDP(c, 0.03 * cv2.arcLength(c, True), True)
        if len(approx) == 4:
            cand.append(("canny", approx.reshape(-1, 2)))
    if cand:
        return max(cand, key=lambda t: cv2.contourArea(cv2.convexHull(t[1])))
    return None

def process(path, outdir, long_edge=1000, quality=35):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    name = os.path.basename(path).rsplit(".", 1)[0]
    det = detect_quad(img)
    if det is None:
        print(f"{name}: DETECT FAIL (kept as plain resize)")
        warp = img
        method = "no-quad"
    else:
        method, src = det
        quad = order_pts(src)
        tl, tr, br, bl = quad
        tw = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
        thh = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
        M = cv2.getPerspectiveTransform(quad, np.array([[0, 0], [tw - 1, 0], [tw - 1, thh - 1], [0, thh - 1]], dtype="float32"))
        warp = cv2.warpPerspective(img, M, (tw, thh))
    scale = long_edge / max(warp.shape[:2])
    if scale < 1:
        warp = cv2.resize(warp, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    jpg_path = os.path.join(outdir, f"{name}_fixed.jpg")
    cv2.imwrite(jpg_path, warp, [cv2.IMWRITE_JPEG_QUALITY, quality])
    print(f"{name}: OK via {method}, -> {warp.shape[1]}x{warp.shape[0]}")
    return jpg_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    jpgs = [p for p in (process(f, outdir) for f in sys.argv[2:]) if p]
    if jpgs:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in sorted(jpgs)]
        pdf = os.path.join(outdir, "output.pdf")
        ims[0].save(pdf, save_all=True, append_images=ims[1:])
        print("PDF:", pdf, os.path.getsize(pdf), "bytes,", len(ims), "pages")
