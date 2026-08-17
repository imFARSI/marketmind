# BRAC UNIVERSITY
## CSE471 : System Analysis and Design
### Lab Assignment on API Postman Collection

**Project Title:** MarketMind — Real-Time Competitor & Market Intelligence Platform  
**Group Number:** Group-06  
**Backend Framework:** Flask (Python) + SQLite (Flask-SQLAlchemy)  
**Submitted by:** Rifaat Nuha  
**Student ID:** 23301320  
**Section:** 02  
**Date:** August 11, 2026  
**Server Port:** `1320` (Last 4 digits of Student ID `23301320`)  

---

## Instructions Overview

This report documents all developed REST APIs for **Rifaat Nuha's** two assigned features in the **MarketMind** platform:
1. **Feature 01: Business Workspace Configuration** (`/nuha/workspace`)
2. **Feature 02: Competitor & Industry News Monitoring** (`/nuha/news`)

---

## Authentication Endpoint (Prerequisite for Postman Testing)

Since the Flask backend uses `Flask-Login` session authentication, API calls require an active authenticated user session. Execute the login endpoint first in Postman to generate the session cookie.

### API: User Login
- **Endpoint URL:** `http://127.0.0.1:1320/auth/login`
- **HTTP Method:** `POST`
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body (JSON):**
```json
{
  "email": "nuha.owner@example.com",
  "password": "password123"
}
```
- **Code Snippet:**
```python
@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return jsonify({
                'status': 'success',
                'message': 'Logged in successfully.',
                'user': {'id': user.id, 'email': user.email, 'role': user.role}
            }), 200
```
- **Response (200 OK):**
```json
{
  "message": "Logged in successfully.",
  "status": "success",
  "user": {
    "business_id": 9,
    "email": "nuha.owner@example.com",
    "id": 13,
    "role": "Business Owner",
    "username": "nuha_owner"
  }
}
```

---

# APIs of Feature - 01: Business Workspace Configuration

### Feature Overview
Allows business owners to configure, update, and manage their enterprise workspace attributes (e.g. company name, industry, niche, company size, founded year, contact email, and headquarters).

---

### API 1.1: Get Workspace Details

- **Endpoint URL:** `http://127.0.0.1:1320/nuha/workspace/api/details`
- **HTTP Method:** `GET`
- **Headers:**
  - `Accept: application/json`
- **Body / Parameters:** None

#### Code Snippet (`marketmind/routes/nuha/workspace.py`):
```python
@workspace_bp.route('/api/details', methods=['GET'])
@login_required
def api_details():
    """REST API: Returns current business workspace profile data as JSON."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No workspace found.'}), 404

    agent_count = User.query.filter_by(business_id=business.id).filter(User.id != current_user.id).count()

    return jsonify({
        'status': 'success',
        'business': {
            'id': business.id,
            'name': business.name,
            'industry': business.industry,
            'niche': business.niche,
            'contact_email': business.contact_email,
            'company_size': business.company_size,
            'founded_year': business.founded_year,
            'headquarters': business.headquarters,
            'description': business.description,
            'join_code': business.join_code,
            'owner_id': business.owner_id,
            'created_at': business.created_at.isoformat() if business.created_at else None
        },
        'agent_count': agent_count
    })
```

#### Expected JSON Response (200 OK):
```json
{
  "agent_count": 0,
  "business": {
    "company_size": "10-50",
    "contact_email": "nuha.owner@example.com",
    "created_at": "2026-08-11T08:48:37.604815",
    "description": "AI-driven competitive intelligence and market monitoring platform.",
    "founded_year": "2022",
    "headquarters": "Dhaka, Bangladesh",
    "id": 9,
    "industry": "Software & AI",
    "join_code": "BIZ1320",
    "name": "Nuha's Tech Enterprise",
    "niche": "Market Intelligence SaaS",
    "owner_id": 13
  },
  "status": "success"
}
```

---

### API 1.2: Update Workspace Configuration

- **Endpoint URL:** `http://127.0.0.1:1320/nuha/workspace/api/update`
- **HTTP Method:** `POST` (or `PUT`)
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body / Parameters (JSON):**
```json
{
  "name": "Nuha Global Intelligence Ltd.",
  "industry": "Software & AI Solutions",
  "niche": "AI SaaS & Analytics",
  "contact_email": "contact@nuhaglobal.com",
  "company_size": "50-100",
  "founded_year": "2023",
  "headquarters": "Dhaka, Bangladesh",
  "description": "Leading enterprise market intelligence and competitor news monitoring platform."
}
```

#### Code Snippet (`marketmind/routes/nuha/workspace.py`):
```python
@workspace_bp.route('/api/update', methods=['POST', 'PUT'])
@login_required
def api_update():
    """REST API: Accepts JSON payload or form data to update business workspace attributes."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No workspace found.'}), 404

    payload = request.get_json(silent=True) or request.form

    name = payload.get('name', business.name)
    industry = payload.get('industry', business.industry)
    niche = payload.get('niche', business.niche)
    contact_email = payload.get('contact_email', business.contact_email)
    company_size = payload.get('company_size', business.company_size)
    founded_year = payload.get('founded_year', business.founded_year)
    headquarters = payload.get('headquarters', business.headquarters)
    description = payload.get('description', business.description)

    if not name or not industry:
        return jsonify({'status': 'error', 'message': 'Name and Industry are required.'}), 400

    business.name = name
    business.industry = industry
    business.niche = niche
    business.contact_email = contact_email
    business.company_size = company_size
    business.founded_year = founded_year
    business.headquarters = headquarters
    business.description = description

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Workspace updated successfully',
        'business': {
            'id': business.id,
            'name': business.name,
            'industry': business.industry,
            'niche': business.niche,
            'contact_email': business.contact_email,
            'company_size': business.company_size,
            'founded_year': business.founded_year,
            'headquarters': business.headquarters,
            'description': business.description,
            'join_code': business.join_code,
            'owner_id': business.owner_id
        }
    })
```

#### Expected JSON Response (200 OK):
```json
{
  "business": {
    "company_size": "50-100",
    "contact_email": "contact@nuhaglobal.com",
    "description": "Leading enterprise market intelligence and competitor news monitoring platform.",
    "founded_year": "2023",
    "headquarters": "Dhaka, Bangladesh",
    "id": 9,
    "industry": "Software & AI Solutions",
    "join_code": "BIZ1320",
    "name": "Nuha Global Intelligence Ltd.",
    "niche": "AI SaaS & Analytics",
    "owner_id": 13
  },
  "message": "Workspace updated successfully",
  "status": "success"
}
```

---

# APIs of Feature - 02: Competitor & Industry News Monitoring

### Feature Overview
Integrates live external **NewsAPI.org** service to automatically fetch, cache, and serve news articles relevant to the business's industry and specific competitors.

---

### API 2.1: Fetch & Cache Industry / Competitor News (NewsAPI)

- **Endpoint URL:** `http://127.0.0.1:1320/nuha/news/api/fetch`
- **HTTP Method:** `POST`
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body / Parameters (JSON for Industry News):**
```json
{
  "category": "industry"
}
```
- **Body / Parameters (JSON for Competitor News):**
```json
{
  "category": "competitor",
  "competitor_id": 1
}
```

#### Code Snippet (`marketmind/routes/nuha/news.py`):
```python
@news_bp.route('/api/fetch', methods=['POST'])
@login_required
def api_fetch():
    """REST API: Accepts JSON payload or Form data to fetch latest news via NewsAPI and update cache."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    payload = request.get_json(silent=True) or request.form
    category = payload.get('category')

    if category == 'industry':
        industry = business.industry or ''
        niche = business.niche or ''
        query = f"{niche} {industry}".strip() or "business"

        success, msg = fetch_and_save_news(query, business.id, competitor_id=None)
        if success:
            count = NewsArticle.query.filter_by(business_id=business.id, competitor_id=None).count()
            return jsonify({
                'status': 'success',
                'message': msg,
                'articles_count': count
            })
        else:
            return jsonify({'status': 'error', 'message': msg}), 400

    elif category == 'competitor':
        competitor_id = payload.get('competitor_id')
        competitor = Competitor.query.filter_by(id=competitor_id, business_id=business.id).first()
        if not competitor:
            return jsonify({'status': 'error', 'message': 'Competitor not found.'}), 404

        success, msg = fetch_and_save_news(competitor.name, business.id, competitor_id=competitor.id)
        if success:
            count = NewsArticle.query.filter_by(business_id=business.id, competitor_id=competitor.id).count()
            return jsonify({
                'status': 'success',
                'message': msg,
                'articles_count': count
            })
        else:
            return jsonify({'status': 'error', 'message': msg}), 400
    else:
        return jsonify({'status': 'error', 'message': 'Invalid category selected.'}), 400
```

#### Expected JSON Response (200 OK):
```json
{
  "articles_count": 12,
  "message": "Successfully fetched and cached 12 articles.",
  "status": "success"
}
```

---

### API 2.2: Get Cached News Articles

- **Endpoint URL:** `http://127.0.0.1:1320/nuha/news/api/articles`
- **HTTP Method:** `GET`
- **Headers:**
  - `Accept: application/json`
- **Body / Parameters:** None

#### Code Snippet (`marketmind/routes/nuha/news.py`):
```python
@news_bp.route('/api/articles', methods=['GET'])
@login_required
def api_articles():
    """REST API: Returns JSON array of cached news articles for the user's business workspace."""
    if current_user.role not in ['Business Owner', 'Business User']:
        return jsonify({'status': 'error', 'message': 'Access denied.'}), 403

    business = current_user.user_business
    if not business:
        return jsonify({'status': 'error', 'message': 'No business workspace found.'}), 404

    industry_articles = NewsArticle.query.filter_by(business_id=business.id, competitor_id=None).order_by(NewsArticle.published_at.desc()).all()
    competitor_articles = NewsArticle.query.filter(NewsArticle.business_id == business.id, NewsArticle.competitor_id != None).order_by(NewsArticle.published_at.desc()).all()

    industry_data = [{
        'id': a.id,
        'title': a.title,
        'source': a.source,
        'url': a.url,
        'summary': a.summary,
        'published_at': a.published_at.isoformat() if a.published_at else None,
        'competitor_id': a.competitor_id
    } for a in industry_articles]

    competitor_data = [{
        'id': a.id,
        'title': a.title,
        'source': a.source,
        'url': a.url,
        'summary': a.summary,
        'published_at': a.published_at.isoformat() if a.published_at else None,
        'competitor_id': a.competitor_id
    } for a in competitor_articles]

    all_articles = industry_data + competitor_data

    return jsonify({
        'status': 'success',
        'count': len(all_articles),
        'industry_articles': industry_data,
        'competitor_articles': competitor_data,
        'articles': all_articles
    })
```

#### Expected JSON Response (200 OK):
```json
{
  "articles": [
    {
      "competitor_id": null,
      "id": 61,
      "published_at": "2026-08-10T12:00:00",
      "source": "PRNewswire",
      "summary": "Executive has more than 25 years of experience in finance leadership for technology companies CHICAGO, Aug. 10, 2026 /PRNewswire/ -- Trading Technologies International, Inc. (TT), a global capital markets technology provider, announced today the appointment o…",
      "title": "Trading Technologies Appoints Sal Lombardi as CFO",
      "url": "https://www.prnewswire.com/news-releases/trading-technologies-appoints-sal-lombardi-as-cfo-302846402.html"
    },
    {
      "competitor_id": null,
      "id": 62,
      "published_at": "2026-08-10T00:38:46",
      "source": "Newsbreak.com",
      "summary": "Chicago’s sales and marketing scene is packed with data-driven, client-facing roles right now—from entry-level field sales to executive analytics and AI-po",
      "title": " Chicago Sales & Marketing Jobs With Multiple $100K+ Roles - NewsBreak",
      "url": "https://www.newsbreak.com/chicago-il-daily-brief-373188216/4818754788218-chicago-sales-marketing-jobs-with-multiple-100k-roles"
    },
    {
      "competitor_id": null,
      "id": 63,
      "published_at": "2026-08-09T16:16:36",
      "source": "Marketingsharks.com",
      "summary": "The 1,224 Page YouTube & Video Marketing PLR Deal - Just $12 The 1,224 Page YouTube & Video Marketing PLR Deal - Just $12 The 1,224 Page YouTube & Video Marketing PLR Deal - Just $12 - From Tiffany Lambert Special Discount Vault: 13 Packs. 569,887 Words. $125…",
      "title": "The 1224 Page YouTube & Video Marketing PLR Deal",
      "url": "https://www.marketingsharks.com/the-1224-page-youtube-video-marketing-plr-deal-just-12/"
    },
    {
      "competitor_id": null,
      "id": 64,
      "published_at": "2026-08-09T15:04:19",
      "source": "MarketBeat",
      "summary": "VTEX (NYSE:VTEX) reported second-quarter results marked by modest subscription revenue growth amid weaker consumer demand in Brazil and Argentina, while prof...",
      "title": "VTEX Q2 Earnings Call Highlights",
      "url": "https://www.marketbeat.com/instant-alerts/vtex-q2-earnings-call-highlights-2026-08-09/?utm_source=yahoofinance&amp;utm_medium=yahoofinance"
    },
    {
      "competitor_id": null,
      "id": 65,
      "published_at": "2026-08-08T14:11:48",
      "source": "Affiliateincomestream.com",
      "summary": "Learn how to start AI affiliate marketing with $0 using free AI tools, organic traffic, content strategies, beginner-friendly affiliate tips",
      "title": "AI Affiliate Marketing for Absolute Beginners With $0 Budget\" – Affiliate Income Stream",
      "url": "https://affiliateincomestream.com/ai-affiliate-marketing-for-absolute-beginners-0-budget/"
    },
    {
      "competitor_id": null,
      "id": 66,
      "published_at": "2026-08-06T13:30:00",
      "source": "GlobeNewswire",
      "summary": "The U.S. ESG Reporting Software Market is Expected to Reach $2.39 Billion by 2035, While Europe is Projected to Hit $1.57 Billion, Driven by CSRD, SFDR, AI-Powered ESG Reporting, Automated Compliance, and Rising Corporate Sustainability Disclosure Requirement…",
      "title": "ESG Reporting Software Market Size to Surpass $6.80 Billion by 2035 | SNS Insider",
      "url": "https://www.globenewswire.com/news-release/2026/08/06/3340401/0/en/ESG-Reporting-Software-Market-Size-to-Surpass-6-80-Billion-by-2035-SNS-Insider.html"
    },
    {
      "competitor_id": null,
      "id": 67,
      "published_at": "2026-08-06T11:44:00",
      "source": "GlobeNewswire",
      "summary": "The U.S. market is projected to reach USD 3.17 Billion by 2035, while Europe is expected to hit USD 2.91 Billion, fueled by EHR integration, clinician shortages, and growing AI-powered patient engagement. The U.S. market is projected to reach USD 3.17 Billion…",
      "title": "Healthcare Chatbots Market Size to Hit USD 11.13 Billion by 2035 Driven by Generative AI and Virtual Healthcare Adoption | SNS Insider",
      "url": "https://www.globenewswire.com/news-release/2026/08/06/3340170/0/en/Healthcare-Chatbots-Market-Size-to-Hit-USD-11-13-Billion-by-2035-Driven-by-Generative-AI-and-Virtual-Healthcare-Adoption-SNS-Insider.html"
    },
    {
      "competitor_id": null,
      "id": 68,
      "published_at": "2026-08-06T11:31:09",
      "source": "Financial Post",
      "summary": "VANCOUVER, British Columbia, Aug. 06, 2026 (GLOBE NEWSWIRE) — ZenaTech, Inc. (Nasdaq: ZENA) (FSE: 49Q) (BMV: ZENA) (“ZenaTech”), a technology solution provider specializing in AI (Artificial Intelligence) drone, Drone as a Service (DaaS), enterprise SaaS, and…",
      "title": "ZenaTech Closes 27th Drone as a Service Acquisition Expanding into Idaho, Strengthening Drone-Based Surveying and Civil Engineering Services for Government and Construction Customers",
      "url": "https://financialpost.com/globe-newswire/zenatech-closes-27th-drone-as-a-service-acquisition-expanding-into-idaho-strengthening-drone-based-surveying-and-civil-engineering-services-for-government-and-construction-customers"
    },
    {
      "competitor_id": null,
      "id": 69,
      "published_at": "2026-08-06T11:30:00",
      "source": "GlobeNewswire",
      "summary": "ZenaTech Closes 27th Drone as a Service Acquisition Expanding into Idaho, Strengthening Drone-Based Surveying and Civil Engineering Services for Government",
      "title": "ZenaTech Closes 27th Drone as a Service Acquisition Expanding into Idaho, Strengthening Drone-Based Surveying and Civil Engineering Services for Government and Construction Customers",
      "url": "https://www.globenewswire.com/news-release/2026/08/06/3340144/0/en/ZenaTech-Closes-27th-Drone-as-a-Service-Acquisition-Expanding-into-Idaho-Strengthening-Drone-Based-Surveying-and-Civil-Engineering-Services-for-Government-and-Construction-Customer.html"
    },
    {
      "competitor_id": null,
      "id": 70,
      "published_at": "2026-08-06T01:03:51",
      "source": "MarketBeat",
      "summary": "EverCommerce (NASDAQ:EVCM) reported second-quarter revenue that grew 2.7% year over year to $152 million, while adjusted EBITDA of $44.5 million exceeded the...",
      "title": "EverCommerce Q2 Earnings Call Highlights",
      "url": "https://www.marketbeat.com/instant-alerts/evercommerce-q2-earnings-call-highlights-2026-08-05/?utm_source=yahoofinance&amp;utm_medium=yahoofinance"
    },
    {
      "competitor_id": null,
      "id": 71,
      "published_at": "2026-08-05T21:22:57",
      "source": "PitchBook News & Analysis",
      "summary": "Continued AI disruption fears are reshaping how leveraged loan investors view software credits. Application software, with $147 billion in leveraged loan out...",
      "title": "Application software loans, with $147B outstanding, hit hardest by AI fears",
      "url": "https://pitchbook.com/news/articles/application-software-loans-with-147b-outstanding-hit-hardest-by-ai-fears"
    },
    {
      "competitor_id": null,
      "id": 72,
      "published_at": "2026-08-05T16:56:41",
      "source": "HackRead",
      "summary": "Compare AI detection & response platforms for 2026, including Dash, Lakera, Operant AI, HiddenLayer and Prisma AIRS, for runtime threat protection and response.",
      "title": "5 Best AI Detection & Response Platforms for 2026",
      "url": "https://hackread.com/best-ai-detection-response-platforms-2026/"
    }
  ],
  "competitor_articles": [],
  "count": 12,
  "industry_articles": [
    {
      "competitor_id": null,
      "id": 61,
      "published_at": "2026-08-10T12:00:00",
      "source": "PRNewswire",
      "summary": "Executive has more than 25 years of experience in finance leadership for technology companies CHICAGO, Aug. 10, 2026 /PRNewswire/ -- Trading Technologies International, Inc. (TT), a global capital markets technology provider, announced today the appointment o…",
      "title": "Trading Technologies Appoints Sal Lombardi as CFO",
      "url": "https://www.prnewswire.com/news-releases/trading-technologies-appoints-sal-lombardi-as-cfo-302846402.html"
    }
  ],
  "status": "success"
}
```

---

## Step-by-Step Guide for Postman Testing & Submission

Follow these steps to test the APIs in Postman and prepare your Word/PDF document:

### Step 1: Start the Backend Flask Server
Open terminal in `marketmind/` and run:
```bash
venv\Scripts\python.exe app.py
```
*The server will start on port `1320` (`http://127.0.0.1:1320`), matching the last 4 digits of student ID `23301320`.*

### Step 2: Import the Postman Collection JSON
1. Open Postman desktop app.
2. Click **Import** (top left).
3. Select the file: `Nuha_MarketMind_Assignment3.postman_collection.json` located in `marketmind/`.
4. The collection **"MarketMind - Nuha APIs (Assignment 03)"** will appear in your Postman sidebar.

### Step 3: Run the Authentication Endpoint (Login)
1. Open folder `0. Authentication` -> Click `User Login (Business Owner)`.
2. Ensure Method is `POST` and URL is `http://127.0.0.1:1320/auth/login`.
3. Click **Send**.
4. You will receive a `200 OK` status and a success JSON response. Postman automatically saves the session cookie for subsequent requests.
5. **Take Screenshot 1** of this response window.

### Step 4: Test Feature 1 APIs
1. **Get Workspace Details:**
   - Open `Feature 1 - Business Workspace Configuration` -> `1. Get Workspace Details`.
   - Click **Send**.
   - Verify `200 OK` response with workspace attributes.
   - **Take Screenshot 2**.
2. **Update Workspace Configuration:**
   - Open `2. Update Workspace Configuration`.
   - Under **Body** tab -> select **raw** -> **JSON**.
   - Click **Send**.
   - Verify `200 OK` response with updated workspace info.
   - **Take Screenshot 3**.

### Step 5: Test Feature 2 APIs
1. **Fetch & Cache Industry News:**
   - Open `Feature 2 - Competitor & Industry News Monitoring` -> `1. Fetch & Cache Industry News (NewsAPI)`.
   - Click **Send**.
   - Verify `200 OK` response showing `Successfully fetched and cached 12 articles`.
   - **Take Screenshot 4**.
2. **Get Cached News Articles:**
   - Open `2. Get Cached News Articles`.
   - Click **Send**.
   - Verify `200 OK` response listing articles array.
   - **Take Screenshot 5**.

### Step 6: Assemble Assignment Submission Document
1. Open your Word document template (or `Template _ Assignment 03 API Postman Collection.docx`).
2. Fill in the cover page with:
   - Student Name: **Rifaat Nuha**
   - Student ID: **23301320**
   - Project Title: **MarketMind — Real-Time Competitor & Market Intelligence Platform**
   - Group Number: **Group-06**
   - Port Number: **1320**
3. Paste the code snippets, endpoint URLs, HTTP methods, headers, and request body JSON from this report.
4. Insert your screenshots below each endpoint section.
5. Save as PDF and export your Postman Collection JSON to submit!
