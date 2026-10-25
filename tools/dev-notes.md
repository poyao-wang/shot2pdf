# shot2pdf local dev notes

- Pi5 PoC server: `cd ~/projects/shot2pdf && python3 -m http.server 8000`（LAN: 192.168.8.138:8000 / Tailscale: 100.126.4.16:8000）；注意 gateway 重啟會帶走它，重開用 Hermes 背景程序追蹤
- **線上版**：GitHub Pages https://poyao-wang.github.io/shot2pdf/shot2pdf.html — push main 自動部署（30–60 秒）
- 改版流程：修改 → `node --check`（抽出 inline script）→ 瀏覽器實測（灌照片跑真按鈕）→ bump `#verTag` badge → commit+push；測試照片放 `.testphotos/` 用後即刪
- CLI 測試 venv：`/home/pi/poc/venv`（opencv-python-headless 5.0.0、numpy、pillow）
- 測資：`/mnt/data/0_Inbox/20261025T1050_slideToPdfTesting/`（IMG_5465–5467）＋ Pi5 `/home/pi/poc/slides2pdf/samples/IMG_sample1/2.jpg`
- 版本史：v0.2.0 badge → v0.2.1 jsPDF mediaBox → v0.3.x 縮圖/邊柄 → v0.4.x 旋轉/ZIP/角度鎖定 → v0.5.x radio 化（px/品質 preset+custom）、拉柄放大隨邊旋轉、全部重設；**v0.5.8 = 第一個部署版**
