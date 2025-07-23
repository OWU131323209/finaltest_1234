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

if st.sidebar.button("✅ 情報取得を開始"):
    geolocator = Nominatim(user_agent="weather-app")
    location = geolocator.geocode(city)

    if location:
        lat, lon = location.latitude, location.longitude

        st.write(f"都市: **{city}**（緯度: {lat}, 経度: {lon}）")
        st.write(f"日付: **{target_date.strftime('%Y-%m-%d')}**")

        weather_api_key = st.secrets["OPENWEATHER_API_KEY"]

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
            gemini_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=gemini_key)

            prompt = f"""
            今日の天気は「{weather}」、気温は約{temp}度です。
            この条件でおすすめの服装（女性向け）をわかりやすく、季節感も踏まえてアドバイスしてください。
            """

            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            gemini_response = model.generate_content(prompt)

            st.subheader("👕 今日の服装アドバイス（Geminiより）")
            st.write(gemini_response.text)
        else:
            st.error("天気データの取得に失敗しました。")
    else:
        st.error("都市名が見つかりませんでした。")
