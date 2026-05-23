========================================================================
                         AI CODE REVIEWER
========================================================================

An elite, modern, web-based code quality review and remediation platform
powered by Gemini AI.

------------------------------------------------------------------------
1. WHY USE THIS PROJECT?
------------------------------------------------------------------------
Manual code review is time-consuming, prone to human error, and often 
misses subtle security vulnerabilities or performance bottlenecks. 
AI Code Reviewer acts as a 24/7 automated tech lead, enabling developers to:

* INSTANT CODE AUDITING: Receive comprehensive quality analysis, 
  vulnerability highlights, and optimization proposals in seconds.
* HANDS-ON LEARNING: Understand WHY certain practices are bad and 
  learn to correct them interactively with the AI follow-up assistant.
* REMEDIATION SPEED: Instantly compare original and corrected code 
  side-by-side and apply changes automatically with one click.
* INSTITUTIONAL MEMORY: Automatically log historical reviews to build 
  a searchable knowledge base of clean coding practices.

------------------------------------------------------------------------
2. PROJECT DESCRIPTION
------------------------------------------------------------------------
AI Code Reviewer is a full-featured Django web application designed to 
evaluate source code against elite engineering standards. It utilizes 
Gemini's advanced reasoning capabilities to analyze language syntax, find 
bugs, identify security weaknesses, assess readability, and suggest 
production-ready code rewrites.

The system calculates individual metrics for:
* SECURITY: OWASP compliance, injection detection, unsafe library usage, 
  and input sanitization.
* PERFORMANCE: Algorithmic complexity, memory management, and redundant 
  calculations.
* READABILITY: Variable naming conventions, structural complexity, 
  comments, and DRY principles.
* OVERALL: A weighted average grade representing general production 
  readiness.

------------------------------------------------------------------------
3. KEY FEATURES
------------------------------------------------------------------------
* CODE REVIEW WORKSPACE:
  - Multi-language Monaco Editor with syntax highlighting, autocomplete, 
    and code folding.
  - Language auto-mapping for Python, JavaScript, C++, Java, HTML, Go, 
    Rust, and Django.
  - Asynchronous AJAX submissions with typing indicator overlays.

* METRIC SCORES & DETAILED REPORTS:
  - Glassmorphic scoreboards showing individual metric scores out of 10.
  - Beautifully styled markdown report explanations and code snippets.

* SIDE-BY-SIDE REMEDIATION (CORRECTED CODE):
  - Secondary Monaco Editor showing Gemini's optimized code.
  - "Apply to Editor" button to load corrected code back to workspace.

* INTERACTIVE AI FOLLOW-UP CHAT:
  - Persistent chat logs saved to the database.
  - Beautiful speech bubbles with markdown compilation and typing 
    status animations.

* HISTORY MANAGEMENT & SEARCH:
  - Search history reviews by keyword matching.
  - Filter history by programming language.
  - Secure deletion of logs by owner or administrators.

* EXPORTERS:
  - PDF Export: Creates structured, formatted PDF downloads of reports.
  - CSV Export: Exports historical logs to spreadsheet formats.

------------------------------------------------------------------------
4. FUNCTIONALITY FLOW
------------------------------------------------------------------------
[User pastes code in Monaco Editor]
       |
       v
[User selects language & clicks Review]
       |
       v
[AJAX submission to Django View]
       |
       v
[Gemini AI analyzes code and constructs scores]
       |
       v
[Review report & corrected code saved in DB]
       |
       v
[Dashboard updates scores, markdown report, and corrected code]
       |
       v
[User starts Interactive Chat or Downloads PDF]
       |
       v
[Follow-up queries reference previous context dynamically]

1. AUTHENTICATION: Users sign up or log in. Anonymous users redirect.
2. ANALYSIS REQUEST: Paste code, select language, and run review.
3. AI PROCESSING: Django calls Gemini API with system instruction context.
4. INTERACTIVE CHAT: Users ask follow-up questions referencing previous 
   code review context.
5. ANALYTICS: Admin or user checks analytics dashboard to view scores 
   over time.

------------------------------------------------------------------------
5. TECH STACK
------------------------------------------------------------------------
* BACKEND:
  - Django 4.x / 5.x (Python)
  - Gemini 2.5 API integration
  - SQLite3 Database (indexing, cascade rules)
  - Python libraries: markdown, xhtml2pdf

* FRONTEND:
  - Custom glassmorphic light & dark themes
  - Monaco Editor (via CDN loader integration)
  - Bootstrap 5 & CSS3 Variables
  - FontAwesome 6, Google Fonts (Inter, Fira Code, Outfit)
========================================================================
