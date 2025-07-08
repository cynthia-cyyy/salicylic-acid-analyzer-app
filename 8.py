import streamlit as st
import numpy as np
import cv2
import matplotlib.pyplot as plt
from collections import Counter

# ---------- 水楊酸換算公式 ----------
def gray_to_concentration(gray):
    return -(gray - 182.56) / 3660.7

# ---------- Streamlit 介面 ----------
st.set_page_config(page_title="水楊酸濃度分析", layout="centered")
st.title("🧪 水楊酸濃度分析工具")
st.markdown("請上傳一張圖片，系統將自動分析區域的灰階值並預估濃度")

uploaded_file = st.file_uploader("請選擇圖片檔案", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if image is None:
        st.error("❌ 圖片讀取失敗")
        st.stop()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ---------- 分格處理 ----------
    block_size = 16
    h, w = gray.shape
    concentrations = []
    block_info = []

    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = gray[y:y+block_size, x:x+block_size]
            avg_gray = np.mean(block)
            conc = gray_to_concentration(avg_gray)

            if 0 <= conc <= 1:
                rounded_conc = round(conc, 3)
                concentrations.append(rounded_conc)
                block_info.append((x, y, rounded_conc))

    if not concentrations:
        st.warning("⚠️ 沒有偵測到有效的濃度區塊")
        st.stop()

    # ---------- 找出眾數與預估區間 ----------
    counter = Counter(concentrations)
    mode_conc, count = counter.most_common(1)[0]
    max_conc = max(concentrations)

    st.markdown(f"📊 **最常見濃度：** `{mode_conc:.2%}`（出現 {count} 次）")
    st.markdown(f"📏 **預估濃度區間：** `{mode_conc:.2%} ~ {max_conc:.2%}`")

    # ---------- 標記格子 ----------
    tolerance = 0.001  # ±0.1%
    image_marked = image.copy()
    for x, y, conc in block_info:
        if abs(conc - mode_conc) <= tolerance:
            cv2.rectangle(image_marked, (x, y), (x + block_size, y + block_size), (0, 255, 0), 2)

    image_rgb = cv2.cvtColor(image_marked, cv2.COLOR_BGR2RGB)
    st.image(image_rgb, caption="綠框為最常見濃度的區域", use_column_width=True)

    # ---------- 畫濃度直方圖 ----------
    fig, ax = plt.subplots()
    ax.hist(concentrations, bins=30, color='skyblue', edgecolor='black')
    ax.axvline(mode_conc, color='orange', linestyle='--', label=f"Mode: {mode_conc:.2%}")
    ax.set_xlabel("Salicylic Acid Concentration (%)")
    ax.set_ylabel("Block Count")
    ax.set_title("Concentration Distribution")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)
    st.pyplot(fig)
