⚙️ Backend Architecture & Engineering
The RAPT backend is built with a focus on performance, modularity, and resource efficiency. It utilizes a distributed micro-services approach to handle intensive AI tasks without compromising the core API's responsiveness.

1. API Orchestration (FastAPI)
The central command center is built with FastAPI (Python) and hosted on Render. It handles:

JWT Authentication: Secure user sessions and Role-Based Access Control (RBAC) to distinguish between candidates and recruiters.

Request Validation: Strict data validation using Pydantic models to ensure data integrity before database insertion.

Service Coordination: Orchestrating the workflow between the primary database and serverless AI functions.

2. Semantic Engine (Supabase Edge Functions)
To solve the "Heavy Model" problem (memory constraints on free-tier hosting), RAPT offloads AI processing to the Edge.

GTE-Small Model: We utilize the GTE-small model (General Text Embeddings) to perform self-attention math on job descriptions and resumes.

High-Dimensional Mapping: Each text input is converted into a 384-dimensional vector, representing its semantic meaning in a mathematical space.

Serverless Efficiency: Written in TypeScript (Deno), these functions scale automatically and execute only when a new job or resume is uploaded.

3. Vector Database (PostgreSQL + pgvector)
Data is managed in Supabase, utilizing PostgreSQL with the pgvector extension.

Semantic Search: Instead of simple keyword matching, RAPT performs Cosine Similarity calculations to find the mathematical distance between vectors.

Complex Data Modeling: Handles relational data including profiles, job listings, companies, and nested JSON analysis results.

Why this setup?
Scalability: The Edge Function handles the "heavy lifting," keeping the FastAPI server lightweight and fast.

Cost-Effectiveness: By using GTE-small, we achieve high accuracy with a tiny memory footprint (~70MB), fitting perfectly into serverless environments.

Accuracy: Semantic search allows RAPT to find matches that traditional search would miss (e.g., matching "Backend Developer" with "Python Engineer").
