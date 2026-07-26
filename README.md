# Food Nutrition API

A RESTful API for importing, searching, and managing the Korean food nutrition
dataset published in `통합_식품영양성분DB_음식_20230715.xlsx`.

The application reads the source Excel workbook, maps and normalizes the
selected columns, and stores the data in PostgreSQL. It provides paginated
search and full CRUD operations through Django REST Framework.

## Features

- Excel-to-PostgreSQL import command
- Idempotent imports using PostgreSQL upserts on `food_cd`
- Missing-value and type normalization
- CRUD endpoints for food records
- Partial or exact, case-insensitive search
- Combined search criteria using AND semantics
- Page-number pagination with a configurable page size
- Consistent API error envelopes
- OpenAPI schema, Swagger UI, and ReDoc
- Docker-based local application and PostgreSQL setup
- Unit, database-backed API, import, and end-to-end integration tests

## Technology

- Python 3.14
- Django 6
- Django REST Framework
- PostgreSQL 17
- pandas and openpyxl
- drf-spectacular
- pytest and pytest-django
- uv
- Docker and Docker Compose

## Quick start with Docker

### 1. Configure the environment

Copy the example environment file:

```bash
cp .env.example .env
```

The included values are intended only for local development. Do not use the
example secret or database password in a production environment.

### 2. Build and start the application

```bash
docker compose up --build
```

Compose starts PostgreSQL, waits for its health check, runs Django migrations,
and starts the API at <http://localhost:8000>.

To run the services in the background:

```bash
docker compose up --build -d
```

### 3. Import the food dataset

Run the management command inside the web container:

```bash
docker compose exec web python manage.py load_food_data \
  /app/nutrition/static/통합_식품영양성분DB_음식_20230715.xlsx
```

The default database batch size is 1,000 rows. It can be changed for testing:

```bash
docker compose exec web python manage.py load_food_data \
  /app/nutrition/static/통합_식품영양성분DB_음식_20230715.xlsx \
  --batch-size 10
```

The command logs a summary containing the numbers read, created, updated,
rejected, and removed as in-file duplicates.

### 4. Verify imported data

Search for an actual row from the workbook:

```bash
curl -s \
  "http://localhost:8000/api/foods/?food_code=D000006&match=exact" \
  | python -m json.tool
```

The result should contain `꿩불고기`, made in `충주`, from research year 2019.

### 5. Stop the services

```bash
docker compose down
```

PostgreSQL data remains in the `postgres_data` Docker volume. To delete the
local database and start over, use the destructive command:

```bash
docker compose down -v
```

## Local development without a web container

Install dependencies with uv:

```bash
uv sync --locked
cp .env.example .env
```

Start only PostgreSQL:

```bash
docker compose up -d db
```

Apply migrations, import the workbook, and start Django:

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py load_food_data \
  "nutrition/static/통합_식품영양성분DB_음식_20230715.xlsx"
./.venv/bin/python manage.py runserver
```

## Data loading design

The import pipeline has three stages:

1. `load_food_excel()` reads only the required source columns and renames them
   to model field names.
2. `normalize_food_df()` converts missing values and types and rejects rows
   without required identity fields.
3. `bulk_create_food_objs()` writes the records with Django `bulk_create()` and
   PostgreSQL conflict updates.

The management command wraps the write in a database transaction. If a batch
fails, the import is rolled back rather than leaving a partially updated
dataset.

### Idempotency and duplicate handling

`food_cd` has a database uniqueness constraint and is the natural key used for
upserts. Re-running the import therefore updates the existing record instead of
creating another row.

During an import:

- Duplicate `id` values in the workbook keep the last occurrence.
- Duplicate `food_cd` values in the workbook keep the last occurrence.
- A `food_cd` already stored in PostgreSQL updates its mutable fields.
- The existing database `id` and `food_cd` are not changed by an upsert.

The database uniqueness constraint also protects normal API creation from
duplicate food codes.

### Missing values and type conversion

The normalization rules are:

| Input condition | Import behavior |
| --- | --- |
| Empty string, whitespace-only value, or `-` | Treated as missing |
| Missing or non-numeric nutrient | Converted to decimal zero |
| Valid nutrient | Converted to `Decimal` |
| Invalid or missing research year | Row rejected |
| Missing `id`, `food_cd`, or `food_name` | Row rejected |
| Missing optional text | Converted to an empty string |
| `id` or `food_cd` with surrounding spaces | Spaces trimmed |

The API independently rejects negative nutrient values and blank required
fields with HTTP 400 responses.

### Excel-to-API field mapping

`group_name` is a computed API field in the form
`"group_name_major - group_name_minor"`. The two component fields are retained
in API responses so records can also be created and edited without parsing the
display value.

| Excel column | Model/API field | Notes |
| --- | --- | --- |
| `SAMPLE_ID` | `id` | Primary key |
| `식품코드` | `food_cd` | Unique upsert key |
| `식품대분류` | `group_name_major` | Used to compute `group_name` |
| `식품상세분류` | `group_name_minor` | Used to compute `group_name` |
| — | `group_name` | `major - minor`, response-only |
| `식품명` | `food_name` | Required during import |
| `연도` | `research_year` | Integer, required during import |
| `지역 / 제조사` | `maker_name` | Region or manufacturer |
| `성분표출처` | `ref_name` | Reference source |
| `1회제공량` | `serving_size` | Serving quantity |
| `내용량_단위` | `serving_size_unit` | Serving unit |
| `에너지(㎉)` | `calorie` | kcal |
| `탄수화물(g)` | `carbohydrate` | g |
| `단백질(g)` | `protein` | g |
| `지방(g)` | `fat` | g |
| `총당류(g)` | `sugars` | g |
| `나트륨(㎎)` | `sodium` | mg |
| `콜레스테롤(㎎)` | `cholesterol` | mg |
| `총 포화 지방산(g)` | `saturated_fatty_acids` | g |
| `트랜스 지방산(g)` | `trans_fat` | g |

## REST API

Base URL: `http://localhost:8000/api/`

| Method | Endpoint | Behavior |
| --- | --- | --- |
| `GET` | `/api/foods/` | Search and list foods |
| `POST` | `/api/foods/` | Create a food |
| `GET` | `/api/foods/{id}/` | Retrieve a food |
| `PUT` | `/api/foods/{id}/` | Fully replace a food |
| `PATCH` | `/api/foods/{id}/` | Partially update a food |
| `DELETE` | `/api/foods/{id}/` | Delete a food |

Successful creation returns HTTP 201, retrieval and updates return HTTP 200,
and successful deletion returns HTTP 204 with no response body.

### Search behavior

`GET /api/foods/` supports these query parameters:

| Parameter | Behavior |
| --- | --- |
| `food_name` | Search by food name |
| `research_year` | Exact integer-year match |
| `maker_name` | Search by region or manufacturer |
| `food_code` | Search the model's `food_cd` field |
| `match` | `partial` (default) or `exact` for all text criteria |
| `page` | Page number |
| `page_size` | Items per page; maximum 100 |

Text searches are case-insensitive. Leading and trailing whitespace is removed,
and repeated whitespace in a query is collapsed. Multiple criteria are joined
with AND, so a result must satisfy every supplied condition. Empty criteria are
ignored.

Partial search example:

```bash
curl "http://localhost:8000/api/foods/?food_name=갈비&maker_name=춘천"
```

Exact, case-insensitive food-code search:

```bash
curl "http://localhost:8000/api/foods/?food_code=d000006&match=exact"
```

Combined search:

```bash
curl \
  "http://localhost:8000/api/foods/?food_name=닭갈비&research_year=2019&maker_name=춘천&food_code=D000008"
```

Invalid `match` values, non-integer years, and negative years return HTTP 400.

### Pagination

Lists use page-number pagination. The default page size is 20 and the maximum
client-selected page size is 100.

```bash
curl "http://localhost:8000/api/foods/?page=2&page_size=10"
```

Paginated responses use this shape:

```json
{
  "count": 90105,
  "next": "http://localhost:8000/api/foods/?page=3&page_size=10",
  "previous": "http://localhost:8000/api/foods/?page=1&page_size=10",
  "results": []
}
```

### Create example

`group_name` is read-only. Send `group_name_major` and `group_name_minor` when
creating or updating a record.

```bash
curl -X POST http://localhost:8000/api/foods/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "DEMO-001",
    "food_cd": "DEMO-FOOD-001",
    "group_name_major": "테스트",
    "group_name_minor": "테스트 식품",
    "food_name": "테스트 음식",
    "research_year": 2023,
    "maker_name": "테스트 제조사",
    "ref_name": "테스트 자료",
    "serving_size": "100",
    "serving_size_unit": "g",
    "calorie": "100.00",
    "carbohydrate": "20.00",
    "protein": "5.00",
    "fat": "2.00",
    "sugars": "3.00",
    "sodium": "50.00",
    "cholesterol": "0.00",
    "saturated_fatty_acids": "1.00",
    "trans_fat": "0.00"
  }'
```

### Update and delete examples

Partial update:

```bash
curl -X PATCH http://localhost:8000/api/foods/DEMO-001/ \
  -H "Content-Type: application/json" \
  -d '{"food_name": "수정된 테스트 음식"}'
```

`PUT` requires a complete writable representation. The primary `id` cannot be
changed during either `PUT` or `PATCH`.

Delete:

```bash
curl -i -X DELETE http://localhost:8000/api/foods/DEMO-001/
```

## Error handling

Errors use one envelope across validation, parsing, missing-resource, unsupported
method, and unexpected-server failures:

```json
{
  "error": {
    "status": 400,
    "code": "validation_error",
    "details": {
      "food_cd": ["food with this food cd already exists."]
    }
  }
}
```

| Situation | Status | Error code |
| --- | ---: | --- |
| Invalid create or update payload | 400 | `validation_error` |
| Duplicate `food_cd` or `id` | 400 | `validation_error` |
| Invalid search parameter | 400 | `validation_error` |
| Malformed JSON | 400 | `parse_error` |
| Missing retrieve/update/delete target | 404 | `not_found` |
| Unsupported HTTP method | 405 | `method_not_allowed` |
| Unexpected application failure | 500 | `internal_server_error` |

For example:

```bash
curl -i http://localhost:8000/api/foods/DOES-NOT-EXIST/
```

## API documentation

With the application running:

- Swagger UI: <http://localhost:8000/api/docs/>
- ReDoc: <http://localhost:8000/api/redoc/>
- Live OpenAPI schema: <http://localhost:8000/api/schema/>
- Generated schema file: [`schema.yml`](schema.yml)

Swagger UI supports interactive requests through **Try it out**.

Regenerate and validate the checked-in schema with:

```bash
./.venv/bin/python manage.py spectacular --file schema.yml --validate
```

## Testing

Tests use pytest and pytest-django. PostgreSQL must be running because the API,
serializer, command, and integration tests use Django's isolated test database.
The test database is created and destroyed by Django; tests do not use or modify
the development `food` database.

Start PostgreSQL and run the complete suite locally:

```bash
docker compose up -d db
./.venv/bin/pytest
```

Or run the suite inside the already-running web container:

```bash
docker compose exec web pytest
```

Run a specific test file:

```bash
./.venv/bin/pytest nutrition/tests/test_food_api.py
```

The suite covers:

- Reading the bundled Excel workbook and checking mapped columns
- Missing-value and type normalization
- Batched Django bulk creation options
- Management-command creation and idempotent updates
- End-to-end Excel read, normalization, database upsert, and HTTP search
- Serializer validation and whitespace trimming
- Create, retrieve, full update, partial update, and delete
- Duplicate `food_cd` and duplicate `id`
- Missing retrieve, update, and delete targets
- Invalid payloads and malformed JSON
- Partial, exact, case-insensitive, whitespace-normalized, and combined search
- Invalid search conditions
- Pagination
- Consistent error responses
- OpenAPI, Swagger, and ReDoc availability

VS Code is configured in `.vscode/settings.json` to discover `test_*.py` files
under `nutrition/tests` with pytest.

Additional checks:

```bash
./.venv/bin/ruff check .
./.venv/bin/python manage.py check
./.venv/bin/python manage.py makemigrations --check --dry-run
./.venv/bin/python manage.py spectacular --validate --file schema.yml
```

## Django admin

The `Food` model is registered with Django admin. Create a local administrator:

```bash
docker compose exec web python manage.py createsuperuser
```

Then visit <http://localhost:8000/admin/>.

## Project structure

```text
config/
  exceptions.py                 Consistent DRF exception envelope
  settings.py                   Django, PostgreSQL, logging, and schema settings
  urls.py                       API and documentation routes
nutrition/
  data_loader.py                Excel mapping and bulk upsert
  data_normalizer.py            Missing-value and type normalization
  management/commands/
    load_food_data.py           Import CLI command
  migrations/                   Database schema history
  models.py                     Food model
  openapi.py                    Reusable OpenAPI parameters and error schemas
  serializers.py                API representation and validation
  views.py                      CRUD, search, and pagination
  tests/                        Unit, API, command, and integration tests
Dockerfile
docker-compose.yml
schema.yml
```

## Design decisions and trade-offs

- **PostgreSQL** provides a real uniqueness constraint and native conflict
  updates for repeatable imports.
- **`food_cd` as the import key** matches the dataset's stable food identity,
  while `id` remains the REST detail-resource identifier.
- **Explicit normalization before persistence** makes missing-data behavior
  deterministic and independently testable.
- **A computed `group_name`** satisfies the requested API representation without
  discarding the source's major/minor category structure.
- **DRF `ModelViewSet` and router** provide conventional resource URLs and HTTP
  behavior with little custom routing code.
- **AND-based filters** make combined criteria predictable. Partial matching is
  the default for discovery, while exact matching is available when precision
  matters.
- **Page-size limits and 1,000-row import batches** bound response and insert
  sizes for the supplied dataset.
- **A shared exception handler** makes client-side error handling consistent.

The current text filters use database case-insensitive matching. For a much
larger dataset or heavier traffic, likely next steps would be PostgreSQL trigram
indexes for partial text search, an index on `research_year`, cursor pagination,
query monitoring, authentication and throttling, a production WSGI server, and
CI-based test execution. These are intentionally outside the required demo
scope.

## Reflection

The main implementation challenge was not exposing CRUD itself, but defining a
clear boundary between imperfect spreadsheet data and strict database/API
types. Keeping mapping, normalization, and persistence as separate layers made
those decisions visible and testable. The upsert command then made the dataset
safe to reload during development, while the end-to-end test demonstrated that
an actual Korean source row survives the complete path from Excel to API search.
