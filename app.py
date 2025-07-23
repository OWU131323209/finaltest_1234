import streamlit as st
from datetime import datetime, timedelta
import requests
from geopy.geocoders import Nominatim
import google.generativeai as genai

st.set_page_config(page_title="天気＋スケジュール＋服装提案アプリ", layout="centered")
st.title("🌦️ 天気＋スケジュール＋服装提案アプリ")

# サイドバー入力
st.sidebar.header("🔧 設定")
city = st.sidebar.text_input("📍都市を入力してください（例：Tokyo）", value="Tokyo")
date_option = st.sidebar.selectbox("📅 日付を選んでください", ["今日", "明日"])

target_date = datetime.today()
if date_option == "明日":
    target_date += timedelta(days=1)

# --- ここから追加・変更する部分 ---

# ユーザーの予定や気分を入力するセクションを追加
st.sidebar.subheader("今日の予定や気分")
user_mood_or_plan = st.sidebar.text_area(
    "今日の予定や気分を教えてください（例：大学に行くのでラフな格好で、推し活なので気合いを入れたい、など）",
    value=""
)

# --- 追加・変更ここまで ---

if st.sidebar.button("✅ 情報取得を開始"):
    geolocator = Nominatim(user_agent="weather-app")
    # geolocator.geocode() は、都市が見つからない場合にNoneを返す可能性があります。
    # そのため、try-exceptブロックでエラーハンドリングを強化します。
    try:
        location = geolocator.geocode(city)
    except Exception as e:
        st.error(f"都市の検索中にエラーが発生しました: {e}")
        location = None # エラーが発生した場合はlocationをNoneに設定

    if location:
        lat, lon = location.latitude, location.longitude

        st.write(f"都市: **{city}**（緯度: {lat}, 経度: {lon}）")
        st.write(f"日付: **{target_date.strftime('%Y-%m-%d')}**")

        # st.secretsからAPIキーを読み込みます
        # OPENWEATHER_API_KEYがsecrets.tomlに設定されていることを確認してください
        weather_api_key = st.secrets.get("OPENWEATHER_API_KEY")
        if not weather_api_key:
            st.error("OpenWeatherMap APIキーが設定されていません。`.streamlit/secrets.toml`を確認してください。")
            st.stop() # APIキーがない場合は処理を停止

        # 今日 or 明日の天気を取得（簡易に現在の天気のみ対応）
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=metric&lang=ja"
        response = requests.get(weather_url)

        if response.status_code == 200:
            data = response.json()
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]

            st.success(f"現在の天気：**{weather}**")
            st.success(f"現在の気温：**{temp}°C**")

            # Gemini 服装アドバイス
            # GEMINI_API_KEYがsecrets.tomlに設定されていることを確認してください
            gemini_key = st.secrets.get("GEMINI_API_KEY")
            if not gemini_key:
                st.error("Gemini APIキーが設定されていません。`.streamlit/secrets.toml`を確認してください。")
                st.stop() # APIキーがない場合は処理を停止

            genai.configure(api_key=gemini_key)

            # --- プロンプトの変更点 ---
            # ユーザーの予定や気分をプロンプトに含めます
            prompt = f"""
            今日の天気は「{weather}」、気温は約{temp}度です。
            ユーザーは「{user_mood_or_plan}」と述べています。
            この条件でおすすめの服装（女性向け）をわかりやすく、季節感も踏まえてアドバイスしてください。
            ユーザーの意向を最大限に尊重し、具体的なアイテム名やコーディネート例を挙げて提案してください。
            """
            # --- プロンプトの変更点ここまで ---

            try:
                model = genai.GenerativeModel("gemini-1.5-flash-latest")
                gemini_response = model.generate_content(prompt)

                st.subheader("👕 今日の服装アドバイス（Geminiより）")
                st.write(gemini_response.text)
            except Exception as e:
                st.error(f"Geminiからのアドバイス取得中にエラーが発生しました: {e}")
                st.info("APIキーが正しいか、またはAPIの利用制限に達していないか確認してください。")
        else:
            st.error(f"天気データの取得に失敗しました。ステータスコード: {response.status_code}")
            st.error(f"エラー詳細: {response.text}")
    else:
        st.error("都市名が見つかりませんでした。正しい都市名を入力してください。")

