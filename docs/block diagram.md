mermaid
graph TD
    A[User Interface<br>(User submits FAQ)] --> B[Django Backend (intelligent_faq)<br>- Receives user query];
    B --> C[Retrieve Relevant Context<br>- Embed query (MiniLM)<br>- Search FAISS index<br>- Get top relevant docs];
    C --> D[Construct Prompt<br>- System + context + query];
    D --> E[Call LLM API (Qwen)<br>- Generate precise answer];
    E --> F[Return Answer to Frontend];
    F --> G[User Interface<br>(Displays Answer)];