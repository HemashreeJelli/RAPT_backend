# 🚀 RAPT: Resume Analysis & Placement Tracker

RAPT is a sophisticated AI-powered recruitment platform designed to bridge the gap between job descriptions and candidate resumes. By utilizing **semantic search** and **high-dimensional vector embeddings**, RAPT ensures that recruiters find the best talent based on actual skill relevance rather than just keyword matching.

## 🏗️ Backend Architecture

The backend is built as a distributed system to handle heavy AI processing while maintaining high availability.

### 1. API Orchestration (FastAPI)

The central command center is built with **FastAPI** (Python) and hosted on **Render**.

* **Role-Based Access Control (RBAC):** Restricts sensitive actions, such as job creation, specifically to verified recruiters.
* **Service Coordination:** Manages the flow of data between the primary database and serverless AI functions.
* **Request Validation:** Uses Pydantic to ensure all incoming data (resumes and jobs) is structured correctly before processing.

### 2. Semantic Engine (Supabase Edge Functions)

To optimize resources, RAPT offloads intensive AI math to the **Edge**.

* **GTE-Small Model:** Uses a lightweight but powerful transformer model to turn text into math.
* **Self-Attention Math:** The engine analyzes the context of words (e.g., distinguishing "Python" the language from "Python" the snake) to ensure accuracy.
* **384-Dimensional Vectors:** Every job and resume is converted into a list of 384 unique numbers representing its "meaning".

### 3. Vector Database (PostgreSQL + pgvector)

Data is stored securely in **Supabase** using **PostgreSQL**.

* **Semantic Matching:** Instead of simple word searches, the database calculates **Cosine Similarity** to find the mathematical distance between a candidate's skills and a job's requirements.
* **Hybrid Storage:** Manages both relational data (user profiles, company info) and unstructured vector data in a single unified system.
