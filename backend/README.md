# Quickstart Llama Hackathon based on the Restack AI Example repo

[Everything you need for the Llama Impact Hackathon](https://docs.restack.io/community/hackathons/08-11-2024-llama-impact)

Restack AI - FastApi + TogetherAI with LlamaIndex Example

The AI workflow will search hacker news based on a query, crawl each project's website, and make summaries for the user.

## Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Docker (for running the Restack services)
- Active [Together AI](https://together.ai) account with API key


## Usage

1. Run Restack local engine with Docker:

   ```bash
   docker run -d --pull always --name studio -p 5233:5233 -p 6233:6233 -p 7233:7233 ghcr.io/restackio/engine:main
   ```

2. Open the Web UI to see the workflows:

   ```bash
   http://localhost:5233
   ```

3. Install dependencies using Poetry:

   ```bash
   poetry install
   ```

4. Set up your environment variables:

   Copy `.env.example` to `.env` and add your Together AI API key:

   ```bash
   cp .env.example .env
   # Edit .env and add your TOGETHER_API_KEY
   ```

5. Open poetry shell:

   ```bash
   poetry shell
   ```

It will display an interpreter path like
...caches/pypoetry/virtualenvs/get-started-ORuVhULK-py3.12

When you open a python file in VSCode or other IDEs like Cursor, you can select the interpreter path to use the poetry environment.

8. Run the services:

   ```bash
   poetry run services
   ```

   This will start the Restack service with the defined workflows and functions.

9. In a new terminal, run FastAPI app:

   ```bash
   poetry run app
   ```

10. In a new terminal, run the Streamlit frontend

   ```bash
   poetry run streamlit run frontend.py
   ```

10. You can test the API endpoint without the Streamlit UI with:

```bash
curl -X POST \
  http://localhost:8000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{"query": "AI", "count": 5}'
```

11. Install llama stack

```
llama stack build --template together
```

This will schedule the workflow and return the result.

12. Run llama stack
```
llama stack run /Users/ssoima/.llama/distributions/llamastack-together/together-run.yaml --port 5050

```
