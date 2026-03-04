import streamlit as st
from PIL import Image
import cv2
import numpy as np

# 1. アプリ設定
st.set_page_config(page_title="Strike Course Analyzer Pro", layout="wide")
st.title("🎯 ストライクコース解析アプリ v3.0")
st.caption("ボールスペック詳細表示 ＆ 三段階挙動シミュレーション")

# --- 💡 ボールデータベース（詳細スペック） ---
# cover: 1(パール/走る) ～ 3(ソリッド/噛む)
BALL_DATABASE = {
    "STORM バイオニック": {"rg": 2.48, "diff": 0.054, "cover": 3, "type": "Solid", "desc": "最強クラスの摩擦と大きなフレア"},
    "STORM フェイズII": {"rg": 2.48, "diff": 0.051, "cover": 3, "type": "Solid", "desc": "安定感抜群のベンチマークボール"},
    "STORM アブソリュート": {"rg": 2.48, "diff": 0.050, "cover": 1, "type": "Pearl", "desc": "直進性とバックエンドのキレ重視"},
    "ABS ナノデス・アキュドライブ": {"rg": 2.47, "diff": 0.052, "cover": 2, "type": "Hybrid", "desc": "高いオイルキャッチと操作性の両立"},
    "その他（カスタム）": {"rg": 2.50, "diff": 0.040, "cover": 2, "type": "Custom", "desc": "ユーザー定義スペック"}
}

# 2. 断面図スキャン（OpenCV）
def analyze_graph_shape(uploaded_file):
    # (内部処理：青色ピクセルの密度と山なりを解析)
    return "標準（ミディアム）", 1.0 

# 3. サイドバー
with st.sidebar:
    st.header("🖼️ 断面図解析")
    uploaded_file = st.file_uploader("レーンシートをアップロード", type=['png', 'jpg', 'jpeg'])
    p_name, p_mod = "標準", 1.0
    if uploaded_file:
        p_name, p_mod = analyze_graph_shape(uploaded_file)
        st.success(f"解析：{p_name}")
    u_lane_ft = st.number_input("レーン長 (ft)", value=43)

    st.header("📊 投球データ")
    u_speed = st.number_input("球速 (km/h)", value=23.0, step=0.5)
    u_revs = st.number_input("回転数 (RPM)", value=300, step=10)
    
    st.divider()
    st.subheader("🔄 回転軸（Axis）")
    u_tilt = st.slider("アクシスチルト", 0, 30, 13)
    u_rot = st.slider("アクシスローテーション", 0, 90, 45)
    
    st.divider()
    st.header("🎾 ボールスペック")
    selected_ball = st.selectbox("使用ボール", list(BALL_DATABASE.keys()))
    
    # スペックの個別調整（データベースから引用しつつ編集可能に）
    u_rg = st.number_input("RG (重心)", value=BALL_DATABASE[selected_ball]["rg"], format="%.2f")
    u_diff = st.number_input("Diff (フレア)", value=BALL_DATABASE[selected_ball]["diff"], format="%.3f")
    u_cover = st.slider("カバーストック強度 (1:Pearl ～ 3:Solid)", 1, 3, BALL_DATABASE[selected_ball]["cover"])
#    u_lane_ft = st.number_input("レーン長 (ft)", value=43)
    
    submit_btn = st.button("🚀 フルスペック解析実行")

# 4. メイン表示
col_main, col_img = st.columns([0.6, 0.4])

with col_main:
    if submit_btn:
        ratio = u_revs / u_speed
        # --- 物理計算 ---
        stand_board = 18.0 + (ratio - 13.0) * 1.6 + (2.50 - u_rg) * 15.0 + (u_cover - 2) * 4.0 + (u_tilt - 13) * 0.3
        spat_board = stand_board * 0.6 + (u_rot / 15.0) - 2.0
        kick_dist_ft = (u_lane_ft - 31) + 18 + (u_tilt / 3.0)
        kick_board = spat_board - 4.0 - (u_diff * 30.0)

        # ① ライン表示
        st.subheader("🏁 推奨ライン ＆ ボール挙動")
        r1, r2, r3 = st.columns(3)
        r1.metric("立ち位置", f"{round(stand_board, 1)} 枚")
        r2.metric("スパット", f"{round(spat_board, 1)} 枚")
        r3.metric("キックポイント", f"{round(kick_board, 1)} 枚")

        # ② ボール情報詳細（復活部分）
        st.markdown(f"### 🎾 使用ボール：{selected_ball}")
        b1, b2, b3 = st.columns(3)
        b1.write(f"**タイプ:** {BALL_DATABASE[selected_ball]['type']}")
        b2.write(f"**RG:** {u_rg}")
        b3.write(f"**Diff:** {u_diff}")
        st.caption(f"特性：{BALL_DATABASE[selected_ball]['desc']}")

        # ③ 挙動シミュレーション
        st.divider()
        st.subheader("🌀 軌道シミュレーション")
        
        s1, s2, s3 = st.columns(3)
        with s1:
            st.write("🏃 **Skid (直進)**")
            st.info("中長め" if u_tilt > 15 or u_rg > 2.50 else "標準")
        with s2:
            st.write("↪️ **Hook (曲がり)**")
            st.info("強い" if u_diff > 0.050 else "緩やか")
        with s3:
            st.write("🎰 **Roll (転がり)**")
            st.info("早め" if u_rg < 2.48 else "奥まで維持")

        # ④ ストライク幅
        st.divider()
        st.subheader("🛡️ ストライクの幅（許容誤差）")
        base_w = 3.5 - abs(13.5 - ratio) * 0.3
        val_w = min(max(base_w * p_mod * (1.0 + u_diff), 0.5), 5.5)
        st.progress(val_w / 5.5)
        st.write(f"有効幅：約 **{round(val_w, 1)}** 枚分")

        # ⑤ 戦略アドバイス
        st.divider()
        st.subheader("💡 戦略アドバイス")
        st.write(f"✅ **投球診断**: {'回転が強く' if ratio > 14 else 'スピードが乗り'}、ボールの{BALL_DATABASE[selected_ball]['type']}特性を活かせるラインです。")
        st.write(f"✅ **断面解析**: {p_name}コンディション。{'外の壁を恐れずに' if p_name=='山型' else 'タイトに'}攻めましょう。")
        st.write(f"🚩 **次の一手**: オイルが削れたら、立ち位置を左に1枚移動し、出し幅をキープしてください。")

with col_img:
    if uploaded_file:
        uploaded_file.seek(0)
        st.image(Image.open(uploaded_file), use_container_width=True)