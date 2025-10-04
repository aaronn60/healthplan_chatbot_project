# healthplan_chatbot_project
this is chatbot made to accomodate health planning according to valid research.
This is a chatbot designed to help users create personalized health plans based on validated research and evidence-based guidelines.
It leverages Large Language Models (LLM) and google search to access insights from credible health journals, ensuring that every recommendation is grounded in reliable data.The chatbot is deployed through Streamlit, making it interactive and easy to use directly from the browser.
**
Input Feature:**
1. User Data Input
Weight
Height
Age
Gender (optional)
Fitness or health goals (example: lose weight, gain muscle, improve sleep, etc.)
Desired time frame to achieve the goal: (example: 1 month, 2 month, 1 year, etc.)
other situation

3. Smart Questioning System
Asks clarifying questions to better understand user goals and current habits
Collects lifestyle info (e.g., diet pattern, activity level, sleep duration, medical history if relevant)
Validates feasibility of goals using data-driven logic

**Output Feature:**
1. Personalized Health Plan Generation
Suggests actionable steps (nutrition, exercise, rest)
Provides rationale based on research-backed insights retrieved via RAG

2, Research Integration
Uses Gemini API to fetch credible health studies and datasets
Summarizes findings into user-friendly explanations

3. Progress Tracking (Planned)
Future version will support saving user inputs and comparing progress over time

** Tech Stack**
1. Frontend & Interface: Streamlit
2. Backend Core: Python
3. Language Model: LLM
4. Retrieval Engine: google search
5. Data Source: google search connection to health research databases and journals

**Version Control:**
1. Git + GitHub

**Future Improvements
**
1. Add user auth to more secure and personalized
2. Integrate personal visualization dashboard for progress tracking.
