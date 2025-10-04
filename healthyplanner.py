import streamlit as st
# Pastikan library yang diperlukan sudah terinstal: pip install streamlit langchain-google-genai langgraph langchain-core
from langchain_google_genai import ChatGoogleGenerativeAI  # Untuk interaksi dengan Google Gemini via LangChain
from langgraph.prebuilt import create_react_agent  # Untuk membuat agen ReAct
from langchain_core.messages import HumanMessage, AIMessage  # Untuk format pesan
from langchain_core.tools import tool 
from typing import Dict, Any, List

# 1. Konfigurasi Dasar Aplikasi
st.set_page_config(page_title="Your Personal Health Planner - Journal Based", page_icon="🏋🏽🔥💪🏼")
st.title(" Healthy Planner Chatbot 🏋🏽🔥💪🏼")
st.write("Plan your health goals with Journal-backed insights.")

# Create a sidebar section for app settings
with st.sidebar:
    st.subheader("Settings")

    google_api_key = st.text_input("Google AI API Key", type="password")
    reset_button = st.button("Reset Conversation", help="Clear all messages and start fresh")
        # KETERANGAN API KEY 
    st.markdown(
        """
        **Belum punya google AI API Key?**
        1. Dapatkan kunci Anda di [Google AI Studio] GRATIS dengan klik tautan berikut(https://aistudio.google.com/api-keys)
        2. Pastikan Anda mengaktifkan layanan **Gemini API**.
        3. klik tombol "Get API Key"
        4. Create API Key
        5. Berikan nama key
        6. pilih project atau buat project baru
        7. klik "Create Key"
        8. Copy API Key & Paste ke kolom "Google AI API Key
        9. lalu tekan tombol enter di keyboard 
        10. Selamat Mencoba!
        """
    )
    


# Definisi Tools
# 1 BMI Calculator Tool
@tool
def calculate_bmi(weight: float, height: float) -> Dict[str, Any]:
    """
    Menghitung BMI (Body Mass Index) dan mengembalikan interpretasi kategorinya.
    """
    try:
        # Menghitung BMI: berat (kg) / (tinggi (m))^2. Tinggi dikonversi dari cm ke m.
        bmi = round(weight / ((height / 100) ** 2), 2)
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal"
        elif 25 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"
        return {"bmi": bmi, "category": category}
    except Exception as e:
        return {"error": str(e)}

# 2 Research Retriever Tool
@tool
def retrieve_research(query: str) -> List[str]:
    """
    Memberi instruksi kepada model untuk melakukan pencarian Google secara mandiri.
    Gunakan ini untuk mendapatkan rekomendasi yang didukung jurnal (journal-backed) dan real-time.
    """
    return [f"LLM Search Instruction: Cari data ilmiah terbaru di Google untuk '{query}' dan pastikan semua rekomendasi didukung oleh jurnal atau penelitian. Hasil harus singkat dan langsung."]

# 3 Plan Generator Tool
@tool
def plan_generator_tool(user_data: Dict[str, Any]) -> str:
    """
    Membuat rencana kesehatan terperinci
    berdasarkan data pengguna. Integrasi dengan hasil pencarian journal atau research terkait untuk memastikan rencana berbasis bukti.
    """
    # Di sini, agen akan menggunakan alat ini untuk membuat prompt yang akan dikirim ke LLM
    # untuk menghasilkan rencana.
    goal = user_data.get("goal", "goal tidak spesifik")
    timeframe = user_data.get("timeframe", "waktu tidak spesifik")
    return f"Instruksi LLM: Buat rencana yang terperinci untuk mencapai tujuan '{goal}' dalam '{timeframe}', dengan mempertimbangkan data pengguna. Gunakan retrieve_research untuk memastikan semua rekomendasi didukung secara ilmiah."



# Inisialisasi LLM dan Agen
# Check if the user has provided an API key.
if not google_api_key:
    st.info("Please add your Google AI API key in the sidebar to start chatting.", icon="🗝️")
    st.stop()

# Inisialisasi LLM sekali saat kunci berubah atau belum ada
if ("llm" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        # Inisialisasi LLM
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.3
        )
        # Simpan kunci untuk perbandingan di masa mendatang
        st.session_state._last_key = google_api_key
        # Kosongkan histori jika kunci berubah
        st.session_state.pop("messages", None)
        # Hapus agen lama agar dibuat ulang
        st.session_state.pop("agent", None) 
    except Exception as e:
        st.error(f"Invalid API Key or configuration error: {e}")
        st.stop()

# 4. Chat History Management
# Inisialisasi histori pesan
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle the reset button click.
if reset_button:
    st.session_state.pop("agent", None)
    st.session_state.pop("messages", None)
    st.session_state.pop("user_data", None) # Hapus data pengguna juga
    st.rerun()

# 5. Step 1: Collect user data once
if "user_data" not in st.session_state: 
    with st.form("user_form"):
        st.subheader("🧍‍♂️ Tell us about yourself")
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=70)
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
        age = st.number_input("Age", min_value=10, max_value=100, value=25)
        gender = st.selectbox("Gender (optional)", ["Prefer not to say", "Male", "Female"])
        goal = st.text_input("What is your main health goal? (e.g. lose 5 kg, gain muscle without gym, improve my sleep, etc)")
        timeframe = st.slider("Target duration to reach your goal? (in month)")
        personal_situation = st.text_input("tell us your other personal situation that block you from living healthy. e.g. student, 9-5 employee, lack of money to buy good food, bad habit, etc")
        #st.text_input("Target duration to reach your goal? (e.g. 3 months, 6 weeks, etc)")

        submitted = st.form_submit_button("Start Planning!")
        if submitted:
            # 1. Simpan data pengguna
            st.session_state["user_data"] = {
                "weight": weight,
                "height": height,
                "age": age,
                "gender": gender,
                "goal": goal,
                "timeframe": timeframe
            }
            
            # 2. Inisialisasi agen
            st.session_state.agent = create_react_agent(
                model=st.session_state.llm,
                tools=[calculate_bmi, retrieve_research, plan_generator_tool    ],
                prompt="""You are a expert, friendly healthy planner assistant. 
                Your primary function is to help users achieve their health goals. 
                Use the tools available to calculate BMI, evaluate goals, retrieve journal-backed research, and generate detailed plans. 
                Respond concisely and clearly."""
            )
            
            # 3. Prompt setelah tekan tombol start planning
            initial_query = """Immediately use the Goal Evaluator and Plan Generator tools to analyze the user data. 
                Output the result ONLY in a compact Markdown report format, covering 4 main sections: 
                **1. Profile & BMI Summary, 2. Goal Evaluation & Timeframe Advice, 3.Proven & Detailed Action Plan based on the specified timeframe, goal and personal_situation that user can follow daily**.
                4. give daily progress tracking to comparing progress overtime
                Use bullet points/lists for information density. 
                Provide brief references to the scientific journals used."""
            
            # Persiapkan pesan untuk pemanggilan agen
            initial_messages = [
                HumanMessage(content=f"USER QUERY: {initial_query}\n\nUSER PROFILE (for context/tools): {st.session_state['user_data']}")
            ]

            # Tambahkan pesan pengguna pemicu ke histori chat
            st.session_state.messages.append({"role": "user", "content": initial_query})

            with st.spinner("⏳ Sedang menghasilkan rencana kesehatan yang dipersonalisasi..."):
                try:
                    initial_response = st.session_state.agent.invoke({"messages": initial_messages})
                    
                    # Ekstrak jawaban
                    generated_plan = initial_response.get("messages", [AIMessage(content="Maaf, rencana tidak dapat dihasilkan.")])[-1].content
                    
                    # Tambahkan respons agen ke histori chat
                    st.session_state.messages.append({"role": "assistant", "content": generated_plan})
                    
                    st.success("🎉 Rencana Awal Berhasil Dibuat! Lihat di bawah untuk detailnya. Anda dapat bertanya lebih lanjut.")

                except Exception as e:
                    st.error(f"Gagal menghasilkan rencana awal: {e}")
                    
            # st.rerun() untuk me-refresh dan menampilkan histori chat (rencana) yang baru ditambahkan
            st.rerun()

# 6. Display Past Messages

# Loop melalui setiap pesan yang tersimpan di session state.
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. Handle User Input and Agent Communication

# If untuk memastikan agen sudah diinisialisasi sebelum mengizinkan chat
if "agent" in st.session_state:
    prompt = st.chat_input("Type your message here...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Tambahkan data pengguna ke prompt agen
            user_info = st.session_state.get("user_data", {})
            user_prompt_with_data = f"USER QUERY: {prompt}\n\nUSER PROFILE (for context/tools): {user_info}"

            # Konversi histori pesan ke format yang diharapkan oleh agen
            messages = []
            # Mulai histori dengan pesan sistem untuk memberikan konteks
            messages.append(HumanMessage(content=user_prompt_with_data))

            # Batas 5 pesan terakhir untuk menghemat token, tambahkan yang lainnya sebagai System/Context
            for msg in st.session_state.messages[-5:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            # Kirim prompt pengguna ke agen
            with st.spinner("Thinking..."):
                response = st.session_state.agent.invoke({"messages": messages})
            
            # Ekstrak jawaban dari respons (LangGraph/ReAct biasanya mengembalikan AIMessage terakhir)
            answer = response.get("messages", [AIMessage(content="I'm sorry, I couldn't generate a response.")])[-1].content


        except Exception as e:
            # Menangani error
            answer = f"An error occurred during agent execution: {e}"

        # Tampilkan respons asisten.
        with st.chat_message("assistant"):
            st.markdown(answer)
        # Tambahkan respons asisten ke histori.
        st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    # Tampilkan pesan jika agen belum siap (menunggu data pengguna)
    if "user_data" in st.session_state:
        st.info("Asisten Anda sedang dimuat. Silakan tunggu sebentar.")
    else:
        st.info("Isi formulir 'Tell us about yourself' untuk memulai perencanaan kesehatan pribadi Anda.")


