import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # 인구 변화 데이터셋 소개
        st.markdown("""
            ---
            **인구 변화 데이터셋 소개**  
            - 출처: [통계청 공개자료 등 기반 (사용자 제공)]  
            - 설명: 국내 지역별 인구, 출생아 수, 사망자 수의 연도별 변화 데이터를 담고 있음  
            - 주요 변수:
              - `연도`: 측정 연도  
              - `지역`: 전국 및 각 광역시/도  
              - `인구`: 해당 연도의 인구 수  
              - `출생아수(명)`: 출생아 수  
              - `사망자수(명)`: 사망자 수  
            - 활용 목적: 연도별 인구 변화 시각화 및 분석, 지역별 인구 증감 비교  
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("Population Trends Analysis")
        self.upload_file()

    def upload_file(self):
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.replace('-', 0, inplace=True)
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)
            self.df = df
            self.translate_dict = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            self.build_tabs()

    def build_tabs(self):
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Basic Stats", "Yearly Trend", "Region-wise Analysis",
            "Change Ranking", "Stacked Area", "Bonus UI"])

        with tab1:
            self.basic_stats()

        with tab2:
            self.yearly_trend()

        with tab3:
            self.region_analysis()

        with tab4:
            self.change_ranking()

        with tab5:
            self.stacked_area()

        with tab6:
            st.success("탭 기반 EDA UI가 완성되었습니다. 각 탭에서 다양한 분석 결과를 확인하세요.")

    def basic_stats(self):
        st.subheader("기초 통계 및 데이터 구조")

        # '세종' 지역 데이터 전처리
        df = self.df.copy()
        sejong_mask = df['지역'] == '세종'
        df.loc[sejong_mask] = df.loc[sejong_mask].replace('-', 0)

        # 숫자형 컬럼 변환
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 결측치 제거 또는 0으로 대체 (선택)
        df.fillna(0, inplace=True)

        # 결과 출력
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        st.text(info_str)

        st.dataframe(df.describe())


    def yearly_population_trend(self):
        st.subheader("Nationwide Population Trend with 2035 Forecast")
    
        df = self.df.copy()
        nat = df[df["지역"] == "전국"]
        nat["연도"] = pd.to_numeric(nat["연도"], errors="coerce")
        nat["인구"] = pd.to_numeric(nat["인구"], errors="coerce")
        nat = nat.dropna(subset=["연도", "인구"]).sort_values("연도")

        # 최근 3년 평균 순변화량 계산
        recent = nat.tail(3)
        avg_diff = (recent["출생아수(명)"] - recent["사망자수(명)"]).mean()
        predicted_2035 = nat["인구"].iloc[-1] + avg_diff * (2035 - nat["연도"].iloc[-1])

        # 그래프
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=nat, x="연도", y="인구", marker="o", ax=ax)
        ax.scatter(2035, predicted_2035, color="red")
        ax.text(2035, predicted_2035, f"{int(predicted_2035):,}", color="red", va="bottom")
        ax.set_title("Nationwide Population Trend")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population")
        st.pyplot(fig)


    def region_analysis(self):
        df = self.df.copy()
        st.subheader("Regional 5-Year Change Analysis")

        # 전국 제외
        region_df = df[df['지역'] != '전국']

        # 최근 연도 및 5년 전 연도
        last_year = region_df['연도'].max()
        past_year = last_year - 5

        # 최근, 과거 인구 정보
        recent = region_df[region_df['연도'] == last_year]
        past = region_df[region_df['연도'] == past_year]

        # 병합 및 변화량 계산
        merged = pd.merge(
            recent[['지역', '인구']],
            past[['지역', '인구']],
            on='지역',
            suffixes=('_recent', '_past')
            )

        merged['diff'] = (merged['인구_recent'] - merged['인구_past']) / 1000  # 천 명 단위
        merged['rate'] = (merged['diff'] / (merged['인구_past'] / 1000)) * 100  # 백분율

        # 지역명 영문으로 변환 및 정렬
        merged['지역'] = merged['지역'].map(self.translate_dict)
        merged.sort_values(by='diff', ascending=False, inplace=True)

        # 변화량 막대 그래프
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=merged, y='지역', x='diff', ax=ax1, palette='Blues_d')
        for i, val in enumerate(merged['diff']):
            ax1.text(val, i, f"{val:,.0f}", va='center')
        ax1.set_title("Population Change (Last 5 Years)")
        ax1.set_xlabel("Change (thousands)")
        ax1.set_ylabel("")

        st.pyplot(fig1)

        # 변화율 막대 그래프
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=merged, y='지역', x='rate', ax=ax2, palette='coolwarm')
        for i, val in enumerate(merged['rate']):
            ax2.text(val, i, f"{val:.1f}%", va='center')
        ax2.set_title("Population Change Rate (Last 5 Years)")
        ax2.set_xlabel("Rate (%)")
        ax2.set_ylabel("")

        st.pyplot(fig2)

        # 해설 추가
        st.markdown("""
        **Interpretation:**  
        - Regions with higher positive bars are experiencing population growth, potentially due to urbanization or policy support.  
        - Regions with negative change or high decline rates may be affected by aging, low birth rates, or population outflow.
        """)

    def change_and_growth_ranking(self):
        st.subheader("Top Population Change & Growth Rate")

        df = self.df.copy()
        df.columns = df.columns.str.strip()
        required_cols = {'지역', '연도', '인구'}
        if not required_cols.issubset(df.columns):
            st.error("필수 컬럼(지역, 연도, 인구)이 누락되었습니다.")
            return

        df = df[df["지역"] != "전국"]
        df["연도"] = pd.to_numeric(df["연도"], errors="coerce")
        df["인구"] = pd.to_numeric(df["인구"], errors="coerce")
        df = df.dropna(subset=["지역", "연도", "인구"])
        df = df.sort_values(["지역", "연도"])

        # 인구 증감 및 증감률 계산
        df["증감"] = df.groupby("지역")["인구"].diff()
        df["증감률"] = df["증감"] / df.groupby("지역")["인구"].shift(1) * 100

        # ▶ 상위 100 증감 순위 테이블
        st.markdown("### 🔹 Top 100 Population Increase (by count)")
        top_count = df.dropna(subset=["증감"]).sort_values(by="증감", ascending=False).head(100).copy()
        top_count["인구"] = top_count["인구"].apply(lambda x: f"{int(x):,}")
        top_count["증감_표시"] = top_count["증감"].apply(lambda x: f"{int(x):,}")

        styled_count = top_count[["연도", "지역", "인구", "증감", "증감_표시"]].style\
            .format({"인구": "{:,}", "증감": "{:,.0f}"})\
            .background_gradient(subset=["증감"], cmap="coolwarm", axis=0)

        st.dataframe(styled_count, use_container_width=True)

        # ▶ 상위 20 증감률 순위 테이블
        st.markdown("### 🔹 Top 20 Population Growth Rate (by %)")
        top_rate = df.dropna(subset=["증감률"]).sort_values(by="증감률", ascending=False).head(20).copy()
        top_rate["인구"] = top_rate["인구"].apply(lambda x: f"{int(x):,}")
        top_rate["증감"] = top_rate["증감"].apply(lambda x: f"{int(x):,}")
        top_rate["증감률"] = top_rate["증감률"].apply(lambda x: f"{x:.2f}%")

        st.dataframe(top_rate[["연도", "지역", "인구", "증감", "증감률"]], use_container_width=True)

    def population_overview_by_region(self):
        st.subheader("📊 Regional Population Overview")

        df = self.df.copy()
        df.columns = df.columns.str.strip()
        required_columns = {'지역', '연도', '인구'}

        if not required_columns.issubset(df.columns):
            st.error("필수 컬럼(지역, 연도, 인구)이 누락되었습니다.")
            return

        try:
            # '전국' 제외 및 정리
            df = df[df["지역"] != "전국"]
            df["연도"] = pd.to_numeric(df["연도"], errors="coerce")
            df["인구"] = pd.to_numeric(df["인구"], errors="coerce")
            df = df.dropna(subset=["연도", "인구", "지역"])
            df = df.sort_values("연도")

            # 영어 변환 사전 적용 (선택 사항)
            df["지역"] = df["지역"].apply(lambda x: self.translate_dict.get(x, x))

            # ▶ 1. 누적 영역 그래프용 피벗
            pivot_area = df.pivot(index="연도", columns="지역", values="인구").fillna(0)

            st.markdown("### 1. Stacked Area Chart of Population by Region")
            fig_area, ax_area = plt.subplots(figsize=(12, 6))
            pivot_area.plot.area(ax=ax_area, cmap="tab20", linewidth=0)
            ax_area.set_title("Stacked Area Chart of Population by Region")
            ax_area.set_xlabel("Year")
            ax_area.set_ylabel("Population")
            ax_area.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), title="Region")
            plt.tight_layout()
            st.pyplot(fig_area)

            # ▶ 2. 히트맵용 피벗
            pivot_heatmap = df.pivot(index="지역", columns="연도", values="인구").fillna(0)
            pivot_display = pivot_heatmap.applymap(lambda x: int(x))

            st.markdown("### 2. Population Heatmap by Region and Year")
            fig_heatmap, ax_heatmap = plt.subplots(figsize=(12, 8))
            sns.heatmap(pivot_heatmap, cmap="YlGnBu", linewidths=0.5, ax=ax_heatmap)
            ax_heatmap.set_title("Heatmap of Population by Region and Year")
            st.pyplot(fig_heatmap)

            # ▶ 3. 피벗 테이블 출력
            st.markdown("### 3. Raw Pivot Table")
            st.dataframe(pivot_display.style.format("{:,}"))

        except Exception as e:
            st.error(f"Error during visualization: {str(e)}")


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()