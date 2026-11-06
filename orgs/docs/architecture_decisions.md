# Architecture Decisions

## Purpose

This document records the significant architectural decisions made
during the development of WildPaths. Rather than documenting *what* the
code does, it explains *why* important decisions were made, what
alternatives were considered, and what consequences followed.

Many of these decisions evolved over time as the project itself evolved.

------------------------------------------------------------------------

# AD-001 -- Build around existing organizational workflows

Wild Paths Wisconsin began with the goal of helping organizations that already
maintained information in Google Sheets. The objective was to improve
access to information, not force organizations into a new system.

**Decision:** Design the system to fit existing organizational workflows
wherever possible.

------------------------------------------------------------------------

# AD-002 -- App is Data Driven... Model Decisions
Not a spreadsheet. Starting with spreadsheets and encountering the limitations meant that switching to a data driven model was the best for me personally but also for the long term viability of the app. Browsing is centered on opportunities rather than organizations.

------------------------------------------------------------------------

Why Organizations → Locations → Activities → Sessions?

Separating these concepts produced a cleaner and more flexible model.

``` text
Organization
    │
    ├── Locations
    │
    └── Activities
             │
             └── Sessions
```

------------------------------------------------------------------------

Separate Organizations from Activities

Organizations are long-lived entities. Activities are opportunities
offered by organizations.
** Decision: ** Organizations own their data. This means that one person is not responsible for maintaining or inputing the data.
------------------------------------------------------------------------
Locations are standalone entities

Originally Locations belonged to organizations but allows organization to use shared locations and turning locations into entities becuase they would correspond to flags on a map was important

------------------------------------------------------------------------


Separate Activities from Sessions

Activities describe **what** is offered.

Sessions describe **when**, **where**, and **how** it is offered. You can have multiple sessions per activity.

------------------------------------------------------------------------
Data quality over data quantity

Accurate, maintainable information is preferred over exhaustive
coverage.

------------------------------------------------------------------------
# AD-007 -- Access Model: Public information should remain public

Browsing organizations, activities, and events does not require an
account. This decision was made to make the app more marketable to organizations. They wanted to be able to see their efforts to provide people with access to the opportunities as not restricted to just Master Naturalists. We wanted to provide some features to Master Naturalists, but ultimately it became clear that requiring a login to browse opportunities was a hurdle that didn't make sense. Absolutely needed hurdles for changing data on the backend, so login is required for managing organizations. Ultimately 2FA should be implemented but I haven't done that yet.

------------------------------------------------------------------------

# AD-009 -- Mobile-first, volunteer-friendly interface

Interfaces should minimize training, clicks, and cognitive load.

------------------------------------------------------------------------

# AD-010 -- Why Django instead of Google Apps Script?

The project began with Google Sheets, Apps Script, and Google Sites
because organizations already used those tools. As requirements
expanded, those platforms became limiting.

**Decision:** Move to Django while continuing to support spreadsheet
imports.
z
------------------------------------------------------------------------

# AD-011 -- Why PostgreSQL?

SQLite worked well during early development, but PostgreSQL provided the
reliability and scalability needed for production.

------------------------------------------------------------------------

# AD-012 -- Why Leaflet?

Leaflet was selected because it is open source, integrates well with
Django, supports GeoJSON overlays, and avoids vendor lock-in.

------------------------------------------------------------------------

# AD-013 -- Provide an IMPORT feature
Entering each activity manually thru the forms is fine for small organizations but providing a bulk entry option seemed valuable for larger organizations. Still floating the idea of building an API that would pull or push the data from their existing systems... but no takers yet.

Validate imported data before publication
**  CSV imports require review. ** Data quality is protected through staging and review rather than direct import.
CSV → Pending Tables → Review → Publish

------------------------------------------------------------------------
Why Pending Tables:
Every import passes through staging tables before publication, allowing
review, duplicate detection, and safer publishing.



------------------------------------------------------------------------


# AD-016 -- Multi-State architecture
Oct 2026: Once the Master Naturalist association saw the app, they were super excited to see it implemented for all 50 states. I wasn't quite sure how to do that and consulted with Claude to see what might be the best approach and creating a single large federated database, with a state switcher made my work maintaining 50 states significantly easier and cheaper. Keeping the principle of making it as cost effective and simple for volunteers as possible, that is the route we are going now. This rewrite (incorporating query set views on Orgs, Locations, Activitys and Sessions) to separate out the states is probably 3 weeks of work. I need a new state wide management ability - and right now it's actually implemented in Admin since the only people that will do this are the superusers.


