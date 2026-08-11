# MarketMind — Real-Time Competitor & Market Intelligence Platform

> **Tagline**: *"Track Competitors Live. Analyze Markets. Decide Faster."*  
> **Course**: CSE 471 — System Analysis and Design | **Semester**: Fall 2025  
> **Group**: 06 | **Section**: 04

---

## 👥 Team Members & Responsibilities

| Student Name | Student ID | GitHub Role | Assigned Features |
|--------------|------------|-------------|-------------------|
| **Salman Farsi** | **23101518** | **Repository Owner / Gatekeeper** | Competitor Management, Field Research Task Assignment, AI Companion Ask-Anything Chat, Meeting & Business Expense Management |
| **Rifaat Nuha** | **23301320** | Team Contributor | Business/Workspace Configuration, Competitor & Industry News Monitoring, To-Do & Quick Notes, Strategic Recommendation Report |
| **Mumtahenah Binta Hashem** | **23201398** | Team Contributor | Product & Price Catalog Management, Live Field Agent Location Tracking, Competitor Discovery & Search Visibility Tracker, Agents On-Site Findings & Email Alert |

---

## 🛠️ Tech Stack

- **Backend**: Python / Flask
- **Frontend**: Jinja2 + Bootstrap 5
- **Database**: SQLite (Flask-SQLAlchemy ORM)
- **External APIs**:
  1. **NVIDIA NIM API** (Meta Llama 3.1 8B — AI Companion Chat)
  2. **Google Gemini API** (Strategic Recommendation Report: SWOT & PESTEL)
  3. **NewsAPI.org** (Competitor & Own Business Industry News Monitoring)
  4. **Google Custom Search API** (Competitor Discovery & Search Visibility Tracker)
  5. **LocationIQ / Geolocation API** (Live Field Agent Location Tracking)
  6. **Resend API** (Automated Email Alerts)

---

## 📋 Functional Requirements Matrix

### Module 1
| Member | Feature | Description |
|--------|---------|-------------|
| **Salman Farsi** | Competitor Management | Add, edit, delete, and view competitor profiles grouped by industry. |
| **Rifaat Nuha** | Business/Workspace Configuration | Manages workspace setup, business niche, contact details, and team configurations. |
| **Mumtahenah** | Product & Price Catalog Management | Add each competitor's products and current listed prices (manual entry or via URL link import). |

### Module 2
| Member | Feature | Description |
|--------|---------|-------------|
| **Salman Farsi** | AI Companion Ask-Anything Chat | High-speed conversational AI chat assistant powered by Llama 3.1 8B API (NVIDIA NIM). |
| **Rifaat Nuha** | Competitor & Industry News Monitoring | Monitor competitor news and own business industry news via NewsAPI with caching and refresh controls. |
| **Mumtahenah** | Live Field Agent Location Tracking | Agent clicks "Accept & Share Location" ➔ browser GPS permission ➔ store coordinates ➔ Assigner portal map display. |

### Module 3
| Member | Feature | Description |
|--------|---------|-------------|
| **Salman Farsi** | Field Research Task Assignment | Assign store research tasks to enrolled field agents with status tracking. |
| **Salman Farsi** | Meeting Management & Business Expense Management | Single-page hub to create, edit, delete, and manage business meetings and calculate business expenses. |
| **Rifaat Nuha** | To-Do & Quick Notes | Users can create, edit, delete, and view tasks, reminders, or quick notes to complete later. |
| **Rifaat Nuha** | Strategic Recommendation Report | Generate own business SWOT & PESTEL by reasoning business model vs competitors + marketing strategy and next move (Gemini API). |
| **Mumtahenah** | Competitor Discovery & Search Visibility Tracker | Track search visibility and discover competitors using own business model details (Google Custom Search API). |
| **Mumtahenah** | Agents On-Site Findings Submission & Email Alert | Submit on-site field findings and trigger automated email alerts via Resend API. |

---

## 🚀 How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/imFARSI/marketmind.git
   cd marketmind
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables (`.env`):
   ```ini
   SECRET_KEY=marketmind_secret_key
   NVIDIA_API_KEY=your_nvidia_nim_api_key
   GEMINI_API_KEY=your_gemini_api_key
   NEWS_API_KEY=your_news_api_key
   GOOGLE_SEARCH_API_KEY=your_google_custom_search_key
   LOCATIONIQ_API_KEY=your_locationiq_key
   RESEND_API_KEY=your_resend_key
   ```

4. Run the Flask application:
   ```bash
   python app.py
   ```

5. Open browser at `http://localhost:5000`
