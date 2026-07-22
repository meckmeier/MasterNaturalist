# Architecture Decisions

## Purpose

This document records the significant architectural decisions made
during the development of WildPaths. Rather than documenting *what* the
code does, it explains *why* important decisions were made, what
alternatives were considered, and what consequences followed.

Many of these decisions evolved over time as the project itself evolved.

------------------------------------------------------------------------

# AD-001 -- Build around existing organizational workflows

WildPaths began with the goal of helping organizations that already
maintained information in Google Sheets. The objective was to improve
access to information, not force organizations into a new system.

**Decision:** Design the system to fit existing organizational workflows
wherever possible.

------------------------------------------------------------------------

# AD-002 -- Separate Organizations from Activities

Organizations are long-lived entities. Activities are opportunities
offered by organizations.

------------------------------------------------------------------------

# AD- ? -- Locations are standalone entities

Originally Locations belonged to organizations but allows organization to use shared locations and turning locations into entities becuase they would correspond to flags on a map was important

------------------------------------------------------------------------

# AD-003 -- Separate Activities from Sessions

Activities describe **what** is offered.

Sessions describe **when**, **where**, and **how** it is offered. You can have multiple sessions per activity.

------------------------------------------------------------------------

# AD-004 -- Activity-centric application

Browsing is centered on opportunities rather than organizations.

------------------------------------------------------------------------


# AD-006 -- Validate imported data before publication

CSV → Pending Tables → Review → Publish

------------------------------------------------------------------------

# AD-007 -- Public information should remain public

Browsing organizations, activities, and events does not require an
account. This decision was made to make the app more marketable to organizations. They wanted to be able to see their efforts to provide people with access to the opportunities as not restricted to just Master Naturalists. We wanted to provide some features to Master Naturalists, but ultimately it became clear that requiring a login to browse opportunities was a hurdle that didn't make sense. Absolutely needed hurdles for changing data on the backend, so login is required for managing organizations. Ultimately 2FA should be implemented but I haven't done that yet.

------------------------------------------------------------------------

# AD-008 -- Data quality over data quantity

Accurate, maintainable information is preferred over exhaustive
coverage.

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

# AD-013 -- Why Pending Tables?

Every import passes through staging tables before publication, allowing
review, duplicate detection, and safer publishing.

------------------------------------------------------------------------

# AD-014 -- Why Invitation-only Registration?

Browsing remains public. Accounts are reserved for organization managers
and users needing personalized features.

------------------------------------------------------------------------

# AD-015 -- Why Organizations → Locations → Activities → Sessions?

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

## Future Architecture Decisions

-   Why organizations own their own data.
-   Why imports are preferred over manual entry.
-   Why the application is activity-centric.
-   Why minimizing maintenance is treated as a primary design
    constraint.
