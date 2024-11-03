# HealMate Backend

---

## Overview  
The backend of HealMate is designed to provide robust and efficient API endpoints that support the frontend application and AI virtual therapist functionalities. It leverages modern technologies to handle real-time communication, data validation, AI integrations, and ensures smooth operation of the platform. With future plans to add audio capabilities, the backend is structured to accommodate enhancements without significant refactoring.

---

## Story and Motivation  
Our motivation for the backend was to build a system capable of handling complex AI interactions while providing real-time support to users. We aimed to create an infrastructure that is scalable, efficient, and secure. By using FastAPI and integrating AI models through LangChain, we strived to deliver intelligent and empathetic responses that simulate a real therapeutic experience. Recognizing the importance of future-proofing, we designed our architecture to be extensible, allowing for the integration of audio responses. Automating our deployment process with Terraform and GitHub Actions was a key step in ensuring that we could iterate quickly and deploy confidently.

---

## Tech Stack  
- **FastAPI**  
- **Uvicorn**  
- **Pydantic**  
- **pyhumps**  
- **python-multipart**  
- **WebSockets**  
- **LangChain** (community, OpenAI, Fireworks integrations)  
- **LangGraph**  
- **Wikipedia API**  
- **Tavily Python**  
- **Docker and DockerHub**  
- **Terraform**  
- **GitHub Actions**  
- **PocketBase**

---

## Features  
- **AI-Powered Virtual Therapist**: Uses LangChain and external knowledge bases to provide advanced therapeutic conversations.
- **Real-Time Communication**: Implements WebSockets for interactive, real-time interactions.
- **Data Validation and Serialization**: Utilizes Pydantic for robust data validation.
- **File Upload Support**: Handles file uploads via python-multipart.
- **Automated Deployment**: Infrastructure as code with Terraform, and CI/CD pipelines with GitHub Actions.
- **Containerization**: Dockerized application for consistent and portable deployment.
- **Scalable Infrastructure**: Deployed on Vercel for reliable performance and scalability.

---

## Installation  

1. **Clone the Repository**  

    ```bash
    git clone https://github.com/yourusername/healmate-backend.git
    cd healmate-backend
    ```

2. **Create a Virtual Environment**  

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**  

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Application**  

    ```bash
    uvicorn app.main:app --reload
    ```
