import streamlit as st
import random
import joblib
import os
import base64
import time
import csv
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional

# ========== KONFIGURASI ==========
st.set_page_config(page_title="Game Pemilahan Sampah", layout="centered")

@dataclass
class GameState:
    score: int = 0
    correct: int = 0
    wrong: int = 0
    times: List[float] = None

    def __post_init__(self):
        if self.times is None:
            self.times = []

    def add_answer(self, is_correct: bool, response_time: float, points: int = 10):
        if is_correct:
            self.correct += 1
            self.score += points
        else:
            self.wrong += 1
        self.times.append(response_time)

    @property
    def total_questions(self) -> int:
        return self.correct + self.wrong

    @property
    def accuracy(self) -> float:
        return self.correct / self.total_questions if self.total_questions > 0 else 0

# ========== DATA & UTILITAS ==========
@st.cache_data
def load_image_dataset():
    fallback_data = {
        'nama': ['Daun', 'Kulit Pisang', 'Botol Plastik', 'Kaleng', 'Sisa Makanan'],
        'file': ['daun.jpeg', 'kulit_pisang.jpeg', 'botol_plastik.jpeg', 'p.png', 'sisa_makanan.jpeg'],
        'kategori': ['Organik', 'Organik', 'Anorganik', 'Anorganik', 'Organik']
    }
    try:
        df = pd.read_csv('di.csv', delimiter=',')
        df['kategori'] = df['kategori'].str.capitalize()
    except FileNotFoundError:
        df = pd.DataFrame(fallback_data)
    
    df['file_path'] = df['file'].apply(lambda x: os.path.join('images', x))
    return df

QUIZ_DATA = [
    {"question": "Sampah organik berasal dari makhluk hidup. Manakah contoh sampah organik?",
     "options": ["Botol plastik", "Kulit buah pisang", "Kaleng minuman", "Kantong plastik"],
     "answer": 1, "explanation": "Kulit buah pisang berasal dari tumbuhan sehingga termasuk sampah organik."},
    
    {"question": "Apa yang sebaiknya dilakukan sebelum membuang sampah?",
     "options": ["Dipilah berdasarkan jenisnya", "Dibakar semua", "Ditimbun di tanah", "Dibuang ke sungai"],
     "answer": 0, "explanation": "Memilah sampah memudahkan proses daur ulang dan pengelolaan."},
    
    {"question": "Sampah anorganik tidak mudah terurai. Contohnya adalah:",
     "options": ["Daun kering", "Kulit jeruk", "Botol plastik", "Nasi sisa"],
     "answer": 2, "explanation": "Botol plastik terbuat dari bahan kimia yang tidak mudah terurai."},
    
    {"question": "Mengapa kita harus memilah sampah organik dan anorganik?",
     "options": ["Supaya terlihat rapi", "Untuk memudahkan daur ulang", "Karena warnanya berbeda", "Tidak ada alasan"],
     "answer": 1, "explanation": "Pemilahan sampah memudahkan daur ulang dan mengurangi pencemaran."},
    
    {"question": "Sampah organik seperti sisa sayuran dapat diolah menjadi:",
     "options": ["Tas plastik", "Kompos", "Botol kaca", "Kaleng"],
     "answer": 1, "explanation": "Sampah organik dapat diolah menjadi kompos sebagai pupuk alami."}
]

def init_session():
    defaults = {
        'page': 'home', 'game_state': GameState(), 'quiz_state': GameState(),
        'current_question': None, 'question_start': time.time(), 'used_images': [],
        'quiz_index': 0, 'feedback': None, 'show_explanation': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def play_sound(sound_file: str):
    try:
        if os.path.exists(sound_file):
            with open(sound_file, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                st.markdown(f'<audio autoplay style="display:none;"><source src="data:audio/mp3;base64,{data}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except:
        pass

def get_random_image(df: pd.DataFrame) -> Optional[Dict]:
    available = df[~df['file'].isin(st.session_state.used_images)]
    if available.empty:
        return None
    row = available.sample(1).iloc[0]
    st.session_state.used_images.append(row['file'])
    return {'image': row['file_path'], 'category': row['kategori'], 'name': row['nama']}

def show_stats(state: GameState):
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Skor", state.score)
    with col2: st.metric("Benar", state.correct)
    with col3: st.metric("Salah", state.wrong)
    
    if state.total_questions > 0:
        accuracy = int(state.accuracy * 100)
        st.progress(state.accuracy, text=f"Akurasi: {accuracy}%")

def show_feedback():
    if st.session_state.feedback:
        if st.session_state.feedback == "benar":
            st.success("✅ Jawaban Benar!")
        else:
            st.error("❌ Jawaban Salah!")
        
        if st.session_state.show_explanation and hasattr(st.session_state, 'current_explanation'):
            st.info(f"💡 {st.session_state.current_explanation}")
        
        # Clear feedback
        st.session_state.feedback = None
        st.session_state.show_explanation = False
        time.sleep(0.5)
        st.rerun()

# ========== HALAMAN ==========
def home_page():
    st.markdown("# 🌱 Game Edukasi Pemilahan Sampah")
    st.markdown("Belajar membuang sampah dengan benar!")
    
    if os.path.exists("tampilan/tampilan.png"):
        st.image("tampilan/tampilan.png", use_container_width=True)
    
    with st.expander("📖 Cara Bermain"):
        st.markdown("""
        **Game Pemilahan:**
        - Lihat gambar sampah dan pilih kategori yang tepat
        - 🟢 ORGANIK: dari makhluk hidup (daun, kulit buah)
        - 🔴 ANORGANIK: buatan manusia (plastik, kaleng)
        
        **Mini Quiz:**
        - Jawab 5 pertanyaan tentang sampah
        - Baca penjelasan untuk belajar lebih dalam
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 Game Pemilahan", use_container_width=True):
            st.session_state.page = 'game'
            st.session_state.game_state = GameState()
            st.session_state.used_images = []
            st.rerun()
    
    with col2:
        if st.button("🧠 Mini Quiz", use_container_width=True):
            st.session_state.page = 'quiz'
            st.session_state.quiz_state = GameState()
            st.session_state.quiz_index = 0
            st.rerun()

def game_page(image_df):
    st.markdown("# 🎮 Game Pemilahan Sampah")
    
    game_state = st.session_state.game_state
    show_feedback()
    
    # Progress
    progress = min(game_state.total_questions / 10, 1.0)
    st.progress(progress, text=f"Progres: {game_state.total_questions}/10")
    
    # Cek game selesai
    if game_state.total_questions >= 10:
        st.markdown("## 🎉 Game Selesai!")
        show_stats(game_state)
        
        if game_state.score >= 80:
            st.balloons()
            st.success("🌟 AMAZING! Master Pemilah Sampah!")
        elif game_state.score >= 60:
            st.success("🎉 GREAT JOB!")
        else:
            st.info("💪 KEEP TRYING!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎯 Quiz", use_container_width=True):
                st.session_state.page = 'quiz'
                st.session_state.quiz_state = GameState()
                st.rerun()
        with col2:
            if st.button("🔄 Main Lagi", use_container_width=True):
                st.session_state.game_state = GameState()
                st.session_state.used_images = []
                st.rerun()
        with col3:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()
        return
    
    # Ambil pertanyaan baru
    if not st.session_state.current_question:
        image_data = get_random_image(image_df)
        if not image_data:
            st.error("Semua gambar sudah digunakan!")
            return
        st.session_state.current_question = image_data
        st.session_state.question_start = time.time()
        st.rerun()
    
    # Tampilkan pertanyaan
    question = st.session_state.current_question
    
    if os.path.exists(question['image']):
        st.markdown("### 📸 Identifikasi Sampah:")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(question['image'], width=300, caption=question['name'])
        
        st.markdown(f"**Nama: {question['name']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 ORGANIK", use_container_width=True):
                handle_answer("Organik", question, game_state)
        with col2:
            if st.button("🔴 ANORGANIK", use_container_width=True):
                handle_answer("Anorganik", question, game_state)
    
    if st.button("🏠 Kembali"):
        st.session_state.page = 'home'
        st.rerun()

def handle_answer(user_answer, question, game_state):
    response_time = time.time() - st.session_state.question_start
    is_correct = question['category'] == user_answer
    game_state.add_answer(is_correct, response_time)
    
    st.session_state.feedback = "benar" if is_correct else "salah"
    play_sound(f"audio/{'benar' if is_correct else 'salah'}.mp3")
    st.session_state.current_question = None
    st.rerun()
#fungsi skor dan leaderboard    
def simpan_skor(nama: str, skor: int):
    with open('scores.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([nama, skor, time.strftime('%d-%m-%Y %H:%M')])
    
def tampilkan_leaderboard():
    st.subheader("🏆 Leaderboard Hari Ini")
    if not os.path.exists('scores.csv'):
        st.info("Belum ada data.")
        return

    df = pd.read_csv('scores.csv', names=["Nama", "Skor", "Waktu"])
    hari_ini = time.strftime('%d-%m-%Y')
    df = df[df['Waktu'].str.startswith(hari_ini)]
    df = df.sort_values(by='Skor', ascending=False).head(5)
    st.table(df)
def quiz_page():
    st.markdown("# 🧠 Mini Quiz Pemilahan Sampah")
    
    quiz_state = st.session_state.quiz_state
    quiz_index = st.session_state.quiz_index
    
    show_feedback()
    
    # Progress
    progress = min(quiz_index / len(QUIZ_DATA), 1.0)
    st.progress(progress, text=f"Quiz: {quiz_index}/{len(QUIZ_DATA)}")
    show_stats(quiz_state)
    
    # Cek quiz selesai
    if quiz_index >= len(QUIZ_DATA):
        st.markdown("## 🎉 Quiz Selesai!")
        show_stats(quiz_state)
        
        score_pct = (quiz_state.score / (len(QUIZ_DATA) * 20)) * 100
        if score_pct >= 80:
            st.balloons()
            st.success("🌟 EXCELLENT!")
        elif score_pct >= 60:
            st.success("🎉 GREAT!")
        else:
            st.info("💪 KEEP LEARNING!")
        
        #fakta menarik tentang sampah
        FAKTA = ["Tahukah kamu? Botol plastik membutuhkan waktu lebih dari 400 tahun untuk terurai.",
        "Sampah organik bisa dijadikan kompos untuk tanaman.",
        "Plastik bisa mencemari laut dan membahayakan hewan laut.",
        "Memilah sampah membantu menjaga lingkungan tetap bersih.",
        "Sampah anorganik bisa didaur ulang menjadi barang baru."]
        
        st.markdown("### 💡 Fakta Menarik:")
        st.info(random.choice(FAKTA))
        #video edukasi youtube
        st.markdown("## 🎥 Yuk Tonton Video Edukasi!")
        st.video("https://www.youtube.com/watch?v=-jo9aUYf0Nk")

        #input nama
        nama = st.text_input("🧒 Nama Kamu:")
        if st.button("📥 Simpan Skor"):
            if nama.strip():
                simpan_skor(nama.strip(), quiz_state.score)
                st.success("Skor berhasil disimpan!")
            else:
                st.warning("masukkan nama terlebih dahulu")
                    
        tampilkan_leaderboard()
                
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Ulangi", use_container_width=True):
                st.session_state.quiz_state = GameState()
                st.session_state.quiz_index = 0
                st.rerun()
        with col2:
            if st.button("🎮 Game", use_container_width=True):
                st.session_state.page = 'game'
                st.session_state.game_state = GameState()
                st.rerun()
        with col3:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()
        return

        
    # Tampilkan pertanyaan
    current_quiz = QUIZ_DATA[quiz_index]
    st.markdown(f"**Soal {quiz_index + 1}: {current_quiz['question']}**")
    
    selected = st.radio("Pilih jawaban:", current_quiz['options'], key=f"quiz_{quiz_index}", index=None)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("✅ Jawab", use_container_width=True, disabled=(selected is None)):
            response_time = time.time() - st.session_state.question_start
            is_correct = current_quiz['options'].index(selected) == current_quiz['answer']
            
            quiz_state.add_answer(is_correct, response_time, 20)
            
            st.session_state.feedback = "benar" if is_correct else "salah"
            st.session_state.show_explanation = True
            st.session_state.current_explanation = current_quiz['explanation']
            st.session_state.awaiting_next = True 
            play_sound(f"audio/{'benar' if is_correct else 'salah'}.mp3")
            st.session_state.quiz_index += 1
            
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()

    if st.session_state.get('awaiting_next', False):
        st.info(f"💡 Penjelasan: {st.session_state.current_explanation}")
        if st.button("➡️ Lanjut", use_container_width=True):
            st.session_state.quiz_index += 1
            st.session_state.awaiting_next = False
            st.session_state.current_explanation = ""
            st.session_state.question_start = time.time()
            st.rerun()

  
        

# ========== MAIN ==========
def main():
    init_session()
    image_df = load_image_dataset()
    
    # Sidebar
    with st.sidebar:
        st.markdown("# 📊 Dashboard")
        if st.session_state.game_state.total_questions > 0:
            st.markdown("### Game Stats")
            show_stats(st.session_state.game_state)
        
        if st.session_state.quiz_state.total_questions > 0:
            st.markdown("### Quiz Stats")
            show_stats(st.session_state.quiz_state)
        
        if st.button("🔄 Reset"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Router
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'game':
        game_page(image_df)
    elif st.session_state.page == 'quiz':
        quiz_page()

if __name__ == "__main__":
    main()
