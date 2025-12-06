# Contributing to read-me-a-book

First off, thank you for considering contributing to this project! It's people like you that make Open Source tools great.

## 🛠️ Development Setup

We use **Docker** to simplify the development environment. You don't need to install Python or Node.js locally if you don't want to.

### Prerequisites
* Docker & Docker Compose
* Git

### Steps to Contribute

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone [https://github.com/YOUR-USERNAME/read-me-a-book.git](https://github.com/YOUR-USERNAME/read-me-a-book.git)
    cd read-me-a-book
    ```
3.  **Spin up the environment**:
    ```bash
    docker-compose up --build
    ```
    * Backend API will be available at: `http://localhost:8000/docs`
    * Frontend will be available at: `http://localhost:5173`

### 🧪 Code Quality & Testing

Please ensure your code follows the project standards:
* **Python**: We follow PEP8. Type hinting is highly encouraged.
* **Frontend**: SvelteKit components should be clean and modular.
* **Security**: Avoid hardcoded secrets. If you introduce new dependencies, please check for known vulnerabilities.

### Submitting a Pull Request (PR)

1.  Create a new branch for your feature/fix: `git checkout -b feature/amazing-feature`.
2.  Commit your changes using clear, descriptive messages (e.g., `feat: add new TTS engine support`).
3.  Push to your fork and submit a **Pull Request** to the `develop` branch.
4.  Describe your changes in detail in the PR description.

## 🐛 Bug Reports

If you find a bug, please create an Issue using the provided template, including:
* Steps to reproduce
* Expected vs. Actual behavior
* Environment details (OS, Docker version)