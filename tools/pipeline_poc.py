#!/usr/bin/env python3
"""Full PoC pipeline: detect slide quad -> perspective warp -> resize 1000px -> JPEG q0.3487 -> PDF.
Detector = Otsu bright-quad (primary) + Canny/dilate fallback, area+quad checks."""
import cv2, numpy as np, sys, os

def order_pts(pts):
    pts = np.array(pts, dtype="float32")
    s = pts.sum(axis=1); d = np.diff(pts, axis=1)
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)],
                     pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")

def detect_quad(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Primary: Otsu bright region
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cand = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.08 * w * h:  # slide occupies 40-60% typically
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

def process(path, outdir):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    det = detect_quad(img)
    name = os.path.basename(path).rsplit(".", 1)[0]
    if det is None:
        print(f"{name}: DETECT FAIL"); return None
    method, src = det
    quad = order_pts(src)
    # warp to rect: width = max of top/bottom edge lengths, height = left/right
    tl, tr, br, bl = quad
    tw = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    thh = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    M = cv2.getPerspectiveTransform(quad, np.array([[0,0],[tw-1,0],[tw-1,thh-1],[0,thh-1]], dtype="float32"))
    warp = cv2.warpPerspective(img, M, (tw, thh))
    # resize long edge 1000 (only shrink)
    scale = 1000 / max(warp.shape[:2])
    if scale < 1:
        warp = cv2.resize(warp, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    # JPEG q0.3487 to mirror the Mac shortcut convention
    jpg_path = os.path.join(outdir, f"{name}_fixed.jpg")
    cv2.imwrite(jpg_path, warp, [cv2.IMWRITE_JPEG_QUALITY, 34])
    print(f"{name}: OK via {method}, warp {tw}x{thh} -> {warp.shape[1]}x{warp.shape[0]}")
    return jpg_path

if __name__ == "__main__":
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    jpgs = [p for p in (process(f, outdir) for f in sys.argv[2:]) if p]
    if len(jpgs) >= 2:
        # build PDF from the fixed jpgs (Pillow)
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in sorted(jpgs)]
        pdf = os.path.join(outdir, "slides_poc.pdf")
        ims[0].save(pdf, save_all=True, append_images=ims[1:])
        print("PDF:", pdf, os.path.getsize(pdf), "bytes")
