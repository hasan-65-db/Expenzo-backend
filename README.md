# Expenzo Backend 🚀

Expenzo is a high-performance, production-ready REST API built with **Django REST Framework (DRF)** to track personal expenses and budgets. Moving away from monolithic design constraints, this system utilizes a fully dockerized, distributed architecture incorporating asynchronous task queues and memory-optimized caching to handle scale efficiently.



## 🛠️ System Architecture & Stack

The backend is decomposed into decoupled, containerized layers managed entirely via Docker Compose:

* **Application Server**: Django REST Framework (DRF) serving the REST endpoints.
* **Database**: PostgreSQL for robust, relational transactional storage.
* **In-Memory Cache**: Redis serving as a high-speed cache store and message broker.
* **Task Worker**: Celery executing asynchronous worker threads to offload heavy operations.



## ✨ Key Features

### 🚀 Advanced Granular Caching (Redis)
Instead of hammering PostgreSQL with repetitive list queries, transaction fetch requests are fully cached using Redis. 
* **Dynamic Cache Keys**: Cache keys are generated dynamically using a unique MD5 hash of the incoming request's query parameters (e.g., categories, prices, dates).
* **Intelligent Cache Invalidation**: The moment a user updates, deletes, or inserts an expense record, the system detects the mutation and instantly evicts all query-hashed cache entries tied to that specific user using pattern matching.

### 📬 Asynchronous Threshold Alerts (Celery + Redis)
To keep the main request-response cycle fast, business logic computations—such as checking budget caps—are decoupled into async workflows.
* **80% Budget Breach Monitor**: On every expense entry, an aggregated lookup calculates total spending. If spending crosses **80%** of the user's defined monthly limit, a Celery worker intercepts the task and fires off an alert email using an isolated worker queue without delaying the client's HTTP response.

### 🎛️ Dynamic Data Pipeline & Security
* **Custom Filtering**: Implements `django-filters` allowing precise user queries across dates, item amounts (`gte`, `lte`), types, and fuzzy text searches.
* **State Isolation**: Uses distinct data models and serializers to ensure user write payloads (`TransactionCreateSerializer`) and read representations (`TransactionResponseSerializer`) remain isolated.
* **Robust Row-Level Security**: Built-in object ownership verification overrides DRF generic handlers, explicitly raising authorization exceptions if a user attempts to alter resources they do not own.



## 🏗️ Local Installation & Setup

Ensure you have **Docker** and **Docker Compose** installed on your system.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/hasan-65-db/Expenzo-backend.git](https://github.com/hasan-65-db/Expenzo-backend.git)
   cd Expenzo-backend