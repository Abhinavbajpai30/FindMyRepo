# Frontend API Endpoints Documentation

## Overview
The frontend requires 4 API endpoints from the backend to function properly. These endpoints handle search, personalized recommendations, repository listing with filters, and curated hidden gems.

---

## 1. Search Endpoint

**Path:** `/search` (or set via `VITE_SEARCH_API_URL` environment variable)

**Method:** `POST`

**Request Body:**
```json
{
  "query": "<search string>"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "results": [
    {
      "name": "react",
      "description": "A declarative, efficient, and flexible JavaScript library for building user interfaces.",
      "languages": ["JavaScript", "TypeScript", "HTML"],
      "stars": 220000,
      "updated_at": "2026-02-10T15:30:00Z",
      "open_issues": 1247,
      "url": "https://github.com/facebook/react",
      "full_name": "facebook/react"
    },
    ...
  ]
}
```

**Notes:**
- Frontend posts JSON with a query string
- Expects a `results` array of repository objects
- Falls back to local client-side search if API fails or returns non-200 status
- Frontend transformers accept: `name`, `description`, `languages`, `stars`, `updated_at`, `open_issues`, `url`, `full_name`

---

## 2. User Preferences → Personalized Recommendations

**Path:** `/userpreferences` (or set via `VITE_USER_PREFERENCES_API` environment variable)

**Method:** `POST`

**Request Body:**
```json
{
  "primaryDomains": ["web-development", "machine-learning"],
  "role": "backend-engineer",
  "expertise": "intermediate",
  "preferredLanguages": ["Python", "JavaScript", "TypeScript"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "results": [
    {
      "name": "fastapi",
      "full_name": "tiangolo/fastapi",
      "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production.",
      "url": "https://github.com/tiangolo/fastapi",
      "language": "Python",
      "languages": ["Python", "JavaScript", "HTML"],
      "stars": 68000,
      "open_issues": 123,
      "updated_at": "2026-02-10T12:00:00Z",
      "topics": ["framework", "api", "web-development"]
    },
    ...
  ]
}
```

**Backend Repository Object Schema:**
- `name` (string): Repository name
- `full_name` (string): Full owner/repo format (e.g., "facebook/react")
- `description` (string): Repository description
- `url` (string): Repository GitHub URL
- `language` (string): Primary language
- `languages` (array): List of programming languages used
- `stars` (number): Number of GitHub stars
- `open_issues` (number): Number of open issues
- `updated_at` (string): ISO format timestamp of last update
- `topics` (array): Repository topics/tags

**Notes:**
- Frontend caches results in localStorage under key `personalizedRepos`
- Called after user completes onboarding with preferences
- Frontend extracts owner from `full_name` (splits on `/`)

---

## 3. All Repositories (Paginated + Filtered)

**Path:** `/allrepos` (or set via `VITE_API_BASE_URL` + `VITE_ALL_REPOS_ENDPOINT` environment variables)

**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | number | Yes | Page number (1-indexed) |
| `limit` | number | Yes | Items per page (typically 20) |
| `sort_by` | string | Yes | Sort field: `stars`, `updated_at`, `forks`, `open_issues`, `name`, `created_at` |
| `sort_order` | string | Yes | Sort direction: `asc` or `desc` |
| `languages` | string | No | Comma-separated language names (e.g., `Python,JavaScript`) |
| `topics` | string | No | Comma-separated topic names |
| `min_stars` | number | No | Minimum number of stars |
| `max_stars` | number | No | Maximum number of stars |
| `min_forks` | number | No | Minimum number of forks |
| `max_forks` | number | No | Maximum number of forks |
| `license` | string | No | License type |
| `has_issues` | boolean | No | Only repos with issues enabled |
| `has_wiki` | boolean | No | Only repos with wiki enabled |
| `is_underrated` | boolean | No | Underrated repositories filter |
| `is_gsoc` | boolean | No | Google Summer of Code repositories |
| `is_hacktoberfest` | boolean | No | Hacktoberfest-eligible repositories |
| `has_good_first_issues` | boolean | No | Repos with "good first issue" labels |
| `name_contains` | string | No | Repository name contains text |
| `description_contains` | string | No | Description contains text |

**Example Request:**
```
GET /allrepos?page=1&limit=20&sort_by=stars&sort_order=desc&languages=Python,JavaScript&min_stars=100&max_stars=10000
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "name": "scikit-learn",
      "full_name": "scikit-learn/scikit-learn",
      "description": "Machine learning in Python. Simple and efficient tools for predictive data analysis.",
      "url": "https://github.com/scikit-learn/scikit-learn",
      "homepage": "https://scikit-learn.org",
      "language": "Python",
      "languages": ["Python", "Cython", "C++"],
      "topics": ["machine-learning", "python", "data-science"],
      "stars": 59000,
      "forks": 28000,
      "open_issues": 89,
      "license": "BSD",
      "has_issues": true,
      "has_wiki": true,
      "created_at": "2010-09-01T00:00:00Z",
      "updated_at": "2026-02-10T10:30:00Z"
    },
    ...
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 5000,
    "total_pages": 250,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null,
    "sort_by": "stars",
    "sort_order": "desc"
  },
  "filters_applied": {
    "languages": "Python,JavaScript",
    "min_stars": 100,
    "max_stars": 10000
  }
}
```

**Frontend Filter Mapping:**

The frontend UI filters map to backend query parameters as follows:

| Frontend UI Input | Backend Parameter | Example |
|------------------|-------------------|---------|
| Programming Language checkboxes | `languages` | `Python,JavaScript,TypeScript` |
| Topics/Tags checkboxes | `topics` | `machine-learning,web-development` |
| Hacktoberfest checkbox | `is_hacktoberfest` | `true` |
| GSOC checkbox | `is_gsoc` | `true` |
| Min Stars slider | `min_stars` | `100` |
| Max Stars slider | `max_stars` | `10000` |
| Min Forks input | `min_forks` | `50` |
| Max Forks input | `max_forks` | `5000` |
| Has Issues toggle | `has_issues` | `true` |
| Has Wiki toggle | `has_wiki` | `true` |
| Name search box | `name_contains` | `react` |
| Description search box | `description_contains` | `machine learning` |

**Notes:**
- Frontend sends debounced text search inputs (500ms delay)
- Pagination resets to page 1 when filters change
- Frontend supports multiple sort options via dropdown
- Filters are optional; omit to get all repositories

---

## 4. Hidden Gems (Paginated, Low-Star Repositories)

**Path:** `/hiddengem` (or set via `VITE_API_BASE_URL` + `VITE_HIDDEN_GEMS_ENDPOINT` environment variables)

**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | number | Yes | Page number (1-indexed) |
| `limit` | number | Yes | Items per page (typically 20) |
| `sort_by` | string | Yes | Sort field: `stars`, `updated_at`, `forks`, `open_issues`, `name`, `created_at` |
| `sort_order` | string | Yes | Sort direction: `asc` or `desc` |

**Example Request:**
```
GET /hiddengem?page=1&limit=20&sort_by=stars&sort_order=desc
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "name": "open-sauced",
      "full_name": "open-sauced/open-sauced",
      "description": "🍕 This is a project to identify your next open source contribution",
      "url": "https://github.com/open-sauced/open-sauced",
      "homepage": "https://opensauced.pizza",
      "language": "TypeScript",
      "languages": ["TypeScript", "JavaScript"],
      "topics": ["open-source", "contributions"],
      "stars": 1200,
      "forks": 500,
      "open_issues": 45,
      "license": "MIT",
      "has_issues": true,
      "has_wiki": false,
      "created_at": "2021-01-15T00:00:00Z",
      "updated_at": "2026-02-08T14:20:00Z"
    },
    ...
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 800,
    "total_pages": 40,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null,
    "sort_by": "stars",
    "sort_order": "desc"
  }
}
```

**Notes:**
- Implies filtering for repositories with fewer than 1,000 stars
- No additional filters exposed in UI (only pagination and sorting)
- Same sorting options as All Repos endpoint
- Returns Repository objects matching same schema as All Repos

---

## Environment Variables

Frontend expects these environment variables in `.env`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_SEARCH_API_URL=http://localhost:8000/search
VITE_ALL_REPOS_ENDPOINT=/allrepos
VITE_HIDDEN_GEMS_ENDPOINT=/hiddengem
VITE_USER_PREFERENCES_API=http://localhost:8000/userpreferences
```

If not set, defaults are:
- `VITE_API_BASE_URL`: `http://localhost:8000`
- `VITE_SEARCH_API_URL`: `http://localhost:8000/search`
- `VITE_ALL_REPOS_ENDPOINT`: `/allrepos`
- `VITE_HIDDEN_GEMS_ENDPOINT`: `/hiddengem`
- `VITE_USER_PREFERENCES_API`: `http://localhost:8000/userpreferences`

---

## Implementation Checklist

- [ ] Implement `/search` POST endpoint with search logic
- [ ] Implement `/userpreferences` POST endpoint for personalized recommendations
- [ ] Implement `/allrepos` GET endpoint with pagination, sorting, and flexible filtering
- [ ] Implement `/hiddengem` GET endpoint with pagination (< 1000 stars)
- [ ] Ensure all endpoints return correct response format with `success` boolean
- [ ] Support CORS for cross-origin requests from frontend
- [ ] Validate and sanitize query parameters
- [ ] Implement proper error handling and HTTP status codes
- [ ] Test pagination and sorting combinations
- [ ] Test filter combinations in All Repos endpoint

---

## Response Format Requirements

All endpoints must return proper JSON with:
- `success` (boolean): Indicates if request succeeded
- `data` or `results` (array): Repository objects for list endpoints
- `pagination` (object): For paginated endpoints with metadata
- Proper HTTP status codes (200 for success, 400 for bad request, 500 for server error)

