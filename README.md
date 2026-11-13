# Python AI Learning

This repository contains practical work completed while learning Python backend and AI application development, from Python fundamentals through document chunking for retrieval-augmented generation (RAG).

## Prerequisites

Install the following:

- Python 3.12 or newer
- Docker Desktop, if Docker examples are required
- A Google Gemini API key, if running Day 3 or Day 4
- PowerShell on Windows

Check installations:

```powershell
python --version
pip --version
docker --version
docker compose version
```

## Python Virtual Environment Setup

From the project directory:

```powershell
cd C:\Varrnit\Python\python-ai-learning
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation, use the Python executable directly instead:

```powershell
.\.venv\Scripts\python.exe day1\practice.py
```

To leave the environment:

```powershell
deactivate
```

## What Was Learned

### Day 1: Python Functions and Pydantic

#### Decorators

`day1/decorator.py` demonstrates:

- Passing a function as an argument.
- Calling a function from another function.
- Creating a decorator.
- Using decorator syntax with `@my_decorator`.
- Running code before and after the decorated function.

#### Pydantic Models

`day1/pydanticPractice.py` and `day1/practice.py` demonstrate:

- Creating data models with `BaseModel`.
- Defining fields and constraints with `Field`.
- Validating JSON with `model_validate_json`.
- Automatic type conversion, such as converting `"25"` to `25`.
- Nested models for API responses.
- Lists of typed values.
- Custom validation with `field_validator`.
- Handling invalid data with `ValidationError`.
- Restricting values such as course difficulty to:
  `Beginner`, `Intermediate`, or `Advanced`.

Example:

```python
class Employee(BaseModel):
    name: str = Field(min_length=3)
    age: int = Field(gt=18, lt=60)
    salary: float = Field(gt=0)
    department: str
```

### Day 2: Async Python, HTTPX, FastAPI, and Docker

#### Synchronous and Asynchronous Code

`day2/asyncioaw.py` demonstrates:

- Normal blocking functions using `time.sleep`.
- Async functions using `async def`.
- Pausing without blocking with `await asyncio.sleep`.
- Starting an async program with `asyncio.run`.
- Running independent tasks concurrently with `asyncio.gather`.

Concurrency allows multiple waiting operations to progress together. For example, three two-second tasks can complete in approximately two seconds when run with `asyncio.gather`, rather than approximately six seconds sequentially.

#### HTTPX

`day2/httpxpr.py` demonstrates:

- Making a synchronous HTTP request with `httpx.get`.
- Making an asynchronous request with `httpx.AsyncClient`.
- Reusing one async client for multiple requests.
- Checking failures with `response.raise_for_status`.
- Fetching multiple users concurrently.

#### FastAPI

`day2/fastapi/main.py` provides:

- `GET /health`
- `POST /echo`

`day2/assisgnment_day2/assday2.py` additionally provides:

- `GET /health`
- `POST /echo`
- `GET /users/{user_id}`

FastAPI uses Pydantic request models to validate incoming JSON before the endpoint function runs.

#### Docker

The Day 2 Dockerfiles:

- Start from `python:3.12-slim`.
- Set `/app` as the working directory.
- Install dependencies from `requirements.txt`.
- Copy the application into the image.
- Expose port `8000`.
- Start the app with Uvicorn.

### Day 3: Gemini API, Chatbots, and Streaming

The files in `day3` demonstrate:

- Loading secrets from `.env` with `python-dotenv`.
- Creating a Google Gemini client with `google-genai`.
- Sending a normal request with `generate_content`.
- Receiving output incrementally with `generate_content_stream`.
- Maintaining conversation history.
- Adding user and model messages with `types.Content`.
- Using a system instruction to define the assistant's behavior.
- Setting generation options such as temperature and maximum output tokens.
- Closing the client in a `finally` block.

The Gemini examples use:

```python
http_options=types.HttpOptions(
    api_version="v1beta",
    timeout=10_000,
    retry_options=types.HttpRetryOptions(attempts=1),
)
```

`v1beta` is required in these examples because they use `system_instruction`.

### Day 4: Structured Ticket Classification

`day4/ticket_classifier.py` combines Gemini with Pydantic.

The `TicketClassification` model defines the required output:

```python
class TicketClassification(BaseModel):
    category: Literal[
        "Billing", "Technical", "Account", "Shipping", "Other"
    ]
    priority: Literal["Low", "Medium", "High", "Urgent"]
    summary: str
```

The model is sent to Gemini as a JSON Schema:

```python
response_mime_type="application/json"
response_json_schema=TicketClassification.model_json_schema()
```

- `response_mime_type` requests JSON instead of normal text.
- `response_json_schema` describes the exact fields and allowed values.

The result is validated again in Python:

```python
TicketClassification.model_validate_json(response.text)
```

This gives both structured generation from Gemini and runtime validation with Pydantic.

`day4/test_tickets.py` tests the classifier with multiple billing, technical, and account tickets. `day4/results.txt` contains recorded test output.

### Day 5: Gemini Function Calling and Tool Use

`day5/main.py` demonstrates how to connect Gemini to local Python functions.

The application exposes two tools:

- `calculator` performs addition, subtraction, multiplication, and division.
- `mock_lookup` retrieves customer information from a local mock database.

The tool-calling flow is:

1. Send the user's question and tool declarations to Gemini.
2. Let Gemini decide whether a tool is needed.
3. Read the requested function name and arguments from `response.function_calls`.
4. Find and execute the corresponding Python function.
5. Send the function result back to Gemini.
6. Receive and print Gemini's final natural-language answer.

The `available_functions` dictionary maps model-requested tool names to actual Python functions:

```python
available_functions = {
    "calculator": calculator,
    "mock_lookup": mock_lookup,
}
```

This pattern keeps the model responsible for choosing a tool while Python remains responsible for executing the tool and controlling the data.

Example questions:

```text
What is 25 multiplied by 4?
Look up customer C101.
What is the status and plan of customer C103?
```

Run Day 5 with:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day5
.\.venv-google\Scripts\Activate.ps1
python .\main.py
```

Every tool-enabled question can require more than one Gemini request: one request to select the tool and another request to generate the final answer after the tool result is returned.

#### Day 5 Quota Note

Gemini free-tier projects have request limits. A `429 RESOURCE_EXHAUSTED` error means the configured project has exceeded its quota, not that the local Python tool function necessarily failed. Check the usage and reset time at:

- https://ai.dev/rate-limit
- https://aistudio.google.com/docs/rate-limits

Retrying repeatedly does not resolve a daily quota limit. Wait for the quota reset or use a project with available quota.

### Day 6: Multi-Tool Agent and API Rate Limiting

`day6/agent.py` builds on function calling with:

- Calculator operations: add, subtract, multiply, divide, modulo, power, and floor division.
- Customer lookup against a larger mock customer database.
- Text analysis for words, unique words, lines, digits, vowels, punctuation, and character counts.
- A `final_answer` tool that ends the agent loop.
- Scratchpad and file logging for agent steps and tool results.
- A maximum step limit to prevent unbounded agent loops.
- A rolling process-local Gemini request limiter.

The limiter defaults to four requests per minute and can be configured before starting the application:

```powershell
$env:GEMINI_REQUESTS_PER_MINUTE = "3"
python .\main.py
```

The limiter controls request frequency but does not increase Gemini's daily quota. A `429 RESOURCE_EXHAUSTED` response still requires waiting for the provider quota reset or using a project with available quota.

Run Day 6 with:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day6
python -m pip install -r requirements.txt
python .\main.py
```

`day6/agent_test.py` exercises arithmetic, customer comparisons, multi-tool tasks, text analysis, unknown customers, invalid arithmetic, unsupported requests, and failure handling.

### Day 8: PDF Text Extraction and Chunking

`day8/main.py` extracts text from the sample PDFs in `day8/day8_sample_pdfs` using `pypdf`, then compares three chunking strategies from `day8/chunking.py`:

- **Fixed-size:** slices text by character count, with configurable overlap.
- **Recursive:** tries paragraph, line, sentence-like, and word boundaries before falling back to character slices.
- **Heading-based:** splits documents at numbered headings matching the pattern used by the sample PDFs.

For each PDF and strategy, the program prints the number of chunks, average chunk size in characters, and up to two sample chunks (the first 200 characters of each sample). The average is computed over the complete chunks returned by that strategy.

Run it with the repository's virtual environment:

```powershell
cd C:\Varrnit\Python\python-ai-learning
.\.venv\Scripts\Activate.ps1
cd .\day8
python -m pip install -r requirements.txt
python .\main.py
```

Or, if you use another virtual environment, activate it first and then run:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day8
python -m pip install -r requirements.txt
python .\main.py
```

### Day 9: PDF Retrieval with Gemini Embeddings and PostgreSQL

Day 9 builds a small retrieval pipeline over PDF documents. It stores document
chunks and their Gemini embeddings in PostgreSQL with the `pgvector` extension,
then finds chunks nearest to a question using cosine distance.

#### How the files fit together

- `day9/embeddings.py` calls Gemini's `gemini-embedding-001` model. It creates
  768-dimensional vectors and uses `RETRIEVAL_DOCUMENT` for stored document
  text and `RETRIEVAL_QUERY` for user questions.
- `day9/db.py` opens a PostgreSQL connection using `DATABASE_URL` and registers
  pgvector's Psycopg adapter so vector values can be read and written.
- `day9/ingest.py` reads PDFs from `day9/day8_sample_pdfs`, extracts text page
  by page, and splits each page into 500-character chunks with 50 characters
  of overlap. It finds the nearest preceding numbered heading as the section,
  generates an embedding for each chunk, and inserts the chunk, metadata, and
  source details into `document_chunks`. Existing identical source/page/chunk
  rows are skipped.
- `day9/search.py` embeds a question, wraps the result as a pgvector `Vector`,
  and orders stored chunks by PostgreSQL's cosine-distance operator (`<=>`).
  It prints the three nearest results by default, including their source,
  page, section, distance, similarity, and text.
- `day9/test_db.py` checks that the database connection works by printing the
  current database name; it does not create or validate the vector table.
- `day9/docker-compose.yml` runs a local PostgreSQL 16 database with pgvector.

The end-to-end flow is:

1. Extract PDF text and split it into overlapping chunks.
2. Ask Gemini to turn each chunk into a numeric embedding.
3. Store the text, embedding, and source metadata in PostgreSQL.
4. Turn a question into an embedding using the query task type.
5. Rank stored embeddings by cosine distance and print the closest chunks.

#### Configure the database and Gemini

From PowerShell, start the local database:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day9
docker compose up -d
```

Create `day9/.env` with your own Gemini API key and local database URL:

```dotenv
GEMINI_API_KEY=replace_with_your_key
DATABASE_URL=postgresql://raguser:ragpassword@localhost:5432/ragdb
```

These database credentials are the development defaults in `docker-compose.yml`;
do not use them for a publicly accessible or production database. Keep `.env`
private and never commit API keys.

The compose file starts PostgreSQL but does not create the application table.
Connect to the database with a PostgreSQL client and run this setup once:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT NOT NULL,
    page INTEGER NOT NULL,
    section TEXT,
    UNIQUE (source, page, content)
);
```

The vector dimension must match `DIMENSIONS` in `day9/embeddings.py`. The
unique constraint supports the conflict handling used by the ingestion script.

#### Run SQL directly in the PostgreSQL terminal

Start the Day 9 database, then open an interactive `psql` session from
PowerShell:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day9
docker compose up -d
docker compose exec postgres psql -U raguser -d ragdb
```

When the prompt changes to `ragdb=#`, you are connected to the `ragdb`
database. You can enter SQL directly; finish each statement with a semicolon.
For example, to add a generated full-text-search column to the existing
`document_chunks` table:

```sql
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS content_tsv TSVECTOR
GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(content, ''))
) STORED;
```

Verify the table and column from the same `psql` session:

```sql
SELECT current_database();
SELECT to_regclass('public.document_chunks');

SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'document_chunks'
  AND column_name = 'content_tsv';
```

The first query should return `ragdb`, the second should return
`document_chunks`, and the last should list `content_tsv` after the `ALTER
TABLE` succeeds. Exit `psql` and return to PowerShell with:

```text
\q
```

The Day 11 Compose setup runs a separate PostgreSQL database and data volume.
Its host port is `5433`, but `docker compose exec postgres ...` connects inside
the Day 11 container. A table created in Day 9 is not automatically present in
Day 11. Run database changes in the Compose project that owns the table; create
and populate `document_chunks` in Day 11 first if you intend to alter that
database instead.

#### Install and run

The existing Day 3 Google environment can be reused. From the Day 9 directory:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day9
..\day3\.venv-google\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Verify database connectivity, then ingest the sample PDFs:

```powershell
python .\test_db.py
python .\ingest.py
```

Search the ingested chunks:

```powershell
python .\search.py
```

Edit the `question` in `search.py` to ask a different question. Each distinct
chunk requires a Gemini embedding request during ingestion; rerunning ingestion
skips chunks already present under the same source, page, and content.

### Day 10: PDF Question Answering with RAG and Citations

Day 10 builds on Day 9's PDF retrieval pipeline to generate answers grounded in
retrieved document passages. It embeds a question, searches PostgreSQL with
pgvector, sends the closest passages to Gemini as context, and validates that
the answer cites only chunks that were actually retrieved.

#### How the files fit together

- `day10/main.py` runs the command-line question-and-answer loop and prints the
  answer and citation metadata.
- `day10/rag.py` embeds a question, retrieves the nearest chunks, builds the
  prompt, calls Gemini, validates citation IDs, and prepares the response.
  The query embedding is wrapped in pgvector's `Vector` type before it is
  passed to PostgreSQL's cosine-distance operator (`<=>`).
- `day10/embeddings.py` creates 768-dimensional Gemini embeddings. Stored
  document chunks use `RETRIEVAL_DOCUMENT`; user questions use
  `RETRIEVAL_QUERY`.
- `day10/db.py` connects to PostgreSQL using `DATABASE_URL` and registers
  pgvector's Psycopg adapter.
- `day10/test_citations.py` checks valid citations, citations to unknown chunk
  IDs, and answers with no citation.
- `day10/requirements.txt` lists the Python dependencies.

Day 10 does not include a PDF ingestion script or a Docker Compose file. Use
Day 9's database setup and ingestion process to create and populate
`document_chunks` before asking questions. Both days must connect to the same
database, and its vector column must be `VECTOR(768)` to match the embedding
dimension.

#### Configure and run

Start and initialize PostgreSQL, then ingest the PDFs as described in the Day 9
instructions above. Create `day10/.env` with the same database URL used by Day
9 and your own Gemini API key:

```dotenv
GEMINI_API_KEY=replace_with_your_key
DATABASE_URL=postgresql://raguser:ragpassword@localhost:5432/ragdb
```

`GEMINI_MODEL` optionally selects the answer-generation model; it defaults to
`gemini-2.5-flash`. `GEMINI_EMBEDDING_MODEL` optionally selects the embedding
model; it defaults to `gemini-embedding-001`. Keep `.env` private and never
commit API keys.

From PowerShell:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day10
python -m pip install -r requirements.txt
python .\test_citations.py
python .\main.py
```

Ask a question at the prompt and type `exit` to quit. The app retrieves five
chunks by default; change `top_k` in `day10/main.py` to experiment with the
amount of context sent to Gemini.

Citation validation confirms that an answer has at least one citation and
that every cited chunk ID came from retrieval. It does not verify that a cited
chunk actually supports the answer's claims.

### Day 11: Compare Vector and Hybrid Retrieval

Day 11 compares vector-only retrieval with hybrid retrieval, which combines
vector similarity and PostgreSQL full-text search using reciprocal rank fusion.
It evaluates retrieval against manually reviewed chunk IDs; it does not call
the answer-generation model.

- `day11/search.py` provides vector search, keyword search, and hybrid search.
- `day11/evaluate.py` runs the ten-question test set, reports the top five
  chunk IDs and Recall@5 for vector and hybrid search, and averages recall over
  questions with relevant chunks. Questions with no relevant chunk are shown
  but excluded from the recall average.
- `day11/ground_truth.json` contains the manually reviewed relevant chunk IDs.
- `day11/db.py` and `day11/embeddings.py` provide the PostgreSQL and Gemini
  embedding helpers used by search.
- `day11/docker-compose.yml` runs a separate database on host port `5433`.

The current ground truth was checked against the 15 chunks in the populated
Day 9 database. Therefore, run the evaluator against Day 9's database unless
you have also ingested the same documents into Day 11. The Day 11 database
volume is separate and currently has no `document_chunks` table. Day 9 must
have the `content_tsv` generated column for keyword and hybrid search.

From PowerShell, install the Day 11 dependencies and run the evaluator against
the existing Day 9 database. The database URL override applies only to this
PowerShell session; the Day 11 `.env` still supplies the Gemini API key:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day11
python -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://raguser:ragpassword@localhost:5432/ragdb"
python .\evaluate.py
Remove-Item Env:DATABASE_URL
```

The URL uses the local development credentials in Day 9's Compose file; do not
use those credentials for a public or production database. Evaluation makes
one Gemini embedding request per question. If you ingest the corpus again or
use a different database, chunk IDs can change; inspect the new chunks and
update `ground_truth.json` before interpreting the metrics.

## Project Structure

```text
python-ai-learning/
├── day1/
│   ├── decorator.py
│   ├── practice.py
│   └── pydanticPractice.py
├── day2/
│   ├── asyncioaw.py
│   ├── httpxpr.py
│   ├── assisgnment_day2/
│   │   ├── Dockerfile
│   │   ├── assday2.py
│   │   └── requirements.txt
│   └── fastapi/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
├── day3/
│   ├── chatbot.py
│   ├── firstcall.py
│   └── streaming.py
├── day4/
│   ├── .env
│   ├── ticket_classifier.py
│   ├── test_tickets.py
│   └── results.txt
├── day5/
│   └── main.py
├── day6/
│   ├── agent.py
│   ├── agent_test.py
│   ├── main.py
│   ├── requirements.txt
│   └── tools.py
├── day8/
│   ├── chunking.py
│   ├── main.py
│   ├── requirements.txt
│   └── day8_sample_pdfs/
│       └── (sample PDF documents)
├── day9/
│   ├── db.py
│   ├── docker-compose.yml
│   ├── embeddings.py
│   ├── ingest.py
│   ├── requirements.txt
│   ├── search.py
│   ├── test_db.py
│   └── day8_sample_pdfs/
│       └── (sample PDF documents)
├── day10/
│   ├── db.py
│   ├── embeddings.py
│   ├── main.py
│   ├── rag.py
│   ├── requirements.txt
│   └── test_citations.py
├── day11/
│   ├── db.py
│   ├── docker-compose.yml
│   ├── embeddings.py
│   ├── evaluate.py
│   ├── ground_truth.json
│   ├── rag.py
│   ├── requirements.txt
│   └── search.py
└── README.md
```



## Install Python Libraries

### Day 1

```powershell
python -m pip install pydantic email-validator
```

`email-validator` is useful when using Pydantic's `EmailStr` type.

### Day 2

```powershell
python -m pip install fastapi "uvicorn[standard]" httpx
```

Or install the existing FastAPI project dependencies:

```powershell
cd day2\fastapi
python -m pip install -r requirements.txt
```

For the assignment project:

```powershell
cd ..\assisgnment_day2
python -m pip install -r requirements.txt
```

### Day 3, Day 4, Day 5, and Day 6

```powershell
python -m pip install google-genai python-dotenv pydantic
```

The `google-genai` package provides the Gemini client, and `python-dotenv` loads values from `.env`.

### Day 9

```powershell
cd C:\Varrnit\Python\python-ai-learning\day9
python -m pip install -r requirements.txt
```

## Gemini Environment Variables

Create a `.env` file in the directory from which the Gemini script is run. These examples use the `GEMINI_API_KEY` variable.

Example:

```dotenv
GEMINI_API_KEY=replace_with_your_key
```

Do not commit `.env` or expose the API key.

Run Gemini examples from their own directories:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day3
.\.venv-google\Scripts\Activate.ps1
python .\firstcall.py
```

For the Day 4 classifier:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day4
.\.venv-google\Scripts\Activate.ps1
python .\ticket_classifier.py
```

For the Day 5 tool-calling agent:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day5
.\.venv-google\Scripts\Activate.ps1
python .\main.py
```

For the Day 6 multi-tool agent:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day6
.\.venv-google\Scripts\Activate.ps1
python .\main.py
```

## Running the Python Examples

```powershell
cd C:\Varrnit\Python\python-ai-learning
.\.venv\Scripts\Activate.ps1

python .\day1\decorator.py
python .\day1\practice.py
python .\day1\pydanticPractice.py
python .\day2\asyncioaw.py
python .\day2\httpxpr.py
```

Run the ticket tests:

```powershell
cd day4
.\.venv-google\Scripts\Activate.ps1
python .\test_tickets.py
```

The test script calls the Gemini API, so it may be affected by API rate limits or temporary service errors.

## Running FastAPI Locally

### Main FastAPI App

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\fastapi
.\..\..\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

Open:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

Test the echo endpoint from another PowerShell window:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/echo `
  -ContentType "application/json" `
  -Body '{"message":"Hello","user":"Varrnit"}'
```

### Assignment FastAPI App

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\assisgnment_day2
.\..\..\.venv\Scripts\Activate.ps1
python -m uvicorn assday2:app --reload
```

The assignment app uses the same port and provides the additional `/users/{user_id}` endpoint.

Stop a running local server with `Ctrl+C`.

## Docker Commands

Make sure Docker Desktop is running before using these commands.

### Build and Run the Main FastAPI Image

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\fastapi
docker build -t python-ai-fastapi .
docker run --name python-ai-fastapi-container -p 8000:8000 python-ai-fastapi
```

Open http://localhost:8000/docs.

Run in detached mode:

```powershell
docker run -d --name python-ai-fastapi-container -p 8000:8000 python-ai-fastapi
```

View logs:

```powershell
docker logs -f python-ai-fastapi-container
```

Stop and remove the container:

```powershell
docker stop python-ai-fastapi-container
docker rm python-ai-fastapi-container
```

### Build and Run the Assignment Image

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\assisgnment_day2
docker build -t python-ai-assignment .
docker run --name python-ai-assignment-container -p 8000:8000 python-ai-assignment
```

### Useful Docker Commands

```powershell
docker image ls
docker container ls
docker container ls -a
docker inspect python-ai-fastapi-container
docker stop python-ai-fastapi-container
docker rm python-ai-fastapi-container
docker rmi python-ai-fastapi
docker system prune
```

Use `docker system prune` carefully because it removes unused Docker resources.

## Common Terminal Commands

```powershell
# Show the current directory
Get-Location

# List files, including hidden files
Get-ChildItem -Force

# Move to a directory
Set-Location C:\Varrnit\Python\python-ai-learning

# Create a directory
New-Item -ItemType Directory new-folder

# Create a virtual environment
python -m venv .venv

# Activate a Windows PowerShell virtual environment
.\.venv\Scripts\Activate.ps1

# Show the Python executable being used
Get-Command python

# Install a package
python -m pip install package-name

# Install all packages from a requirements file
python -m pip install -r requirements.txt

# Show installed packages
python -m pip list

# Run a Python file
python .\path\to\file.py

# Stop a running program
Ctrl+C
```

## Troubleshooting

### PowerShell Does Not Allow Activation

Use the environment's Python executable directly:

```powershell
.\.venv-google\Scripts\python.exe .\ticket_classifier.py
```

### Gemini `400 INVALID_ARGUMENT`

If the error says that developer instructions are not enabled for API version `v1`, configure the client with:

```python
types.HttpOptions(api_version="v1beta")
```

### Gemini `503 UNAVAILABLE`

The model may be temporarily busy. Wait and retry. This is a service availability problem rather than a Python validation problem.

### Gemini Rate Limits

The API may reject requests after too many calls. Reduce request frequency, wait for the retry window, and avoid repeatedly running the full ticket test set during development.

### Port 8000 Is Already in Use

Use another host port:

```powershell
python -m uvicorn main:app --reload --port 8001
```

Or map a different host port for Docker:

```powershell
docker run --name python-ai-fastapi-container -p 8001:8000 python-ai-fastapi
```

Then open http://localhost:8001/docs.

## Main Takeaways

1. Decorators wrap and extend function behavior.
2. Pydantic validates and structures Python data.
3. Asyncio allows concurrent waiting operations.
4. HTTPX makes synchronous and asynchronous HTTP requests.
5. FastAPI builds validated web APIs quickly.
6. Docker packages an application and its dependencies.
7. Gemini can generate normal, streamed, and structured responses.
8. A Pydantic JSON Schema can constrain an AI response.
9. Pydantic validation should still verify the response received from an AI model.
10. Gemini function calling lets an AI model request controlled local Python tools.
11. Embeddings and vector search can retrieve relevant PDF chunks for a question.
