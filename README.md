# 🏗️ Backend Architecture

The backend is engineered as a distributed system designed to handle intensive AI processing while maintaining high availability and low latency.

## 1. API Orchestration (FastAPI)

The central command center is built with **FastAPI (Python)** and hosted on **Render**. It acts as the primary gateway for all client interactions.

* **Role-Based Access Control (RBAC):** Implements strict security protocols to restrict sensitive actions, such as job creation and candidate sourcing, exclusively to verified recruiter accounts.
* **Service Coordination:** Orchestrates the data flow between the primary relational database and specialized serverless AI functions.
* **Request Validation:** Leverages **Pydantic** for rigorous schema enforcement, ensuring all incoming payloads (resumes and job descriptions) are sanitized and structured correctly before downstream processing.

---

## 2. Semantic Engine (Supabase Edge Functions)

To optimize resource allocation and minimize cold starts, RAPT offloads computationally heavy AI tasks to the network edge.

* **GTE-Small Model:** Utilizes a high-performance, lightweight transformer model to perform text-to-vector embeddings.
* **Self-Attention Mechanism:** The engine analyzes contextual relationships within the text—for instance, accurately distinguishing "Python" the programming language from "Python" the biological entity.
* **384-Dimensional Vectors:** Every document is transformed into a high-dimensional vector space, represented by 384 unique numerical coordinates that capture the "latent meaning" of the content.

---

## 3. Vector Database (PostgreSQL + pgvector)

Persistent storage and similarity searches are handled within **Supabase** using the **PostgreSQL** ecosystem.

* **Semantic Matching:** Moving beyond legacy keyword searches, the system utilizes **Cosine Similarity** math to calculate the distance between vectors. This identifies the best candidates based on the "closeness" of their skills to a job's specific requirements.
* **Hybrid Storage Architecture:** A unified system that manages both structured relational data (user profiles, company metadata) and unstructured vector data, allowing for complex, multi-attribute queries in a single database call.
