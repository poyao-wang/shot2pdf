# shot2pdf

拍照圖片 → 四角校正 → PDF，批次一鍵完成。不限 slides：發票、文件、白板、任何「拍下來的平面東西」都適用。

## 線上版

**https://poyao-wang.github.io/shot2pdf/shot2pdf.html**（GitHub Pages，push main 自動部署）

也可以本機跑：單檔 web app，瀏覽器直接開 `shot2pdf.html`（或掛在任何靜態 server 上）。頁面標題下的 badge 顯示版本號，測試前先確認它。

## 用法

1. 拖入整批照片（JPEG/PNG/WebP，可一次整批）
2. 「✨ 自動偵測全部」— OpenCV.js 自動找投影/紙張四角
3. 沒抓好的點「四角」手動修正：拖角、拖邊（四邊角度鎖定，只變長度）、↻ 旋轉
4. 「產出 PDF」或「產出 ZIP（校正圖）」— 透視校正攤平 → resize → 壓縮 → 下載；自動檔名 `YYYYMMDDThhmmss`
5. 「♻️ 全部重設」清空重來（有確認步驟）

全程**本機處理**（照片不上傳）；唯一網路需求是首次載 OpenCV.js／jsPDF 的 CDN。

## 參數

- 尺寸基準：長邊／寬／高（radio 三選一，預設**寬**）
- px 值：1000／2000／500 或 custom（1–4000 整數，預設 1000）；只縮不放大
- 品質：25／35／50 或 custom（1–100 百分比整數，預設 35；沿用手機 shortcut 的 0.3487≈35 慣例）
- 輸入值即時檢查：超界/非整數紅框提示，匯出時一律夾回合法範圍（亂值不會炸）

## 架構筆記

- **OpenCV.js 全走 Web Worker**：10MB WASM 首次編譯會凍結主執行緒（Safari 直接 Page Unresponsive），所有 cv 工作在 worker message queue 排隊，ImageData transferable 往返
- **偵測主路線 Otsu 亮區分割**：暗教室亮幕／暗桌亮紙場景，亮度分割遠比 Canny 邊緣法穩；Canny+dilate 當 fallback
- 偵測在 900px 縮圖做、warp 在 1600px 做、輸出再縮目標長邊

## 踩過的坑（改 code 前先讀）

1. **`cv.findContours` 的輪廓容器必須是 `cv.MatVector`**——傳 `cv.Mat` 每張都丟例外（"Expected null or instance of MatVector"）。錯誤若被批次迴圈吞掉，UI 只會看到 0/N，毫無線索
2. **`decodeToCanvas` 的 `drawImage` 必須帶縮放尺寸**——只給位置不給尺寸，4032px 原圖會「原尺寸」畫進 900px 畫布＝只看到照片中央裁切，四角根本不在畫面內。症狀：偵測全滅＋編輯器圖片爆版，且完全沒有報錯
3. Safari 對快取很頑固——改版後測試要**完全關分頁再開**（或加 `?v=N`）
4. **`.setting input` 型 CSS 選擇器會連 radio 一起命中**——數字框寬度規則限用 `input[type="number"]`，radio 另給 15px 全域規則（踩過兩次：v0.4.6、v0.5.3）
5. `disabled` 的 input 收不到 pointer/focus——「點它自動啟用」模式要用半透明 class 代替 disabled
6. 邊拖柄「角度鎖定」用直線交點解：相鄰邊方向不變、沿原方向伸縮接軌；退化（平行）退回純平移
7. jsPDF 多頁尺寸不同時，每頁 `addPage([w,h], orientation)` 帶自己的尺寸，別用 deletePage/AddPage 空頁模式（mediaBox 會錯亂）
8. 瀏覽器版 opencv.js（docs.opencv.org/4.9.0）在 Node 用 eval 載會失敗；要離線跑偵測用 npm `@techstark/opencv-js`

## tools/

- `batch_convert.py` — Python/OpenCV 命令列版（同管線：Otsu 偵測 → warp → resize → JPEG → PDF），適合 SSH/批次場景；用法 `python3 tools/batch_convert.py OUT_DIR IMG1 IMG2 ...`（需 opencv-python-headless、pillow、numpy）

## 來源

從 life-os `slide-photo-automation` 研究升格而來（Notion Records_Main 2026-10-23）。歷史研究記錄在 life-os `3_resources/H_Digital-Management/slide-photo-automation/`。
