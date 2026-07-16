# Development Effort

**Version:** 0.2 (Evidence Draft)  
**Last Updated:** July 16, 2026

## Purpose

This revision incorporates evidence from the complete Git history together with the known pre-development work.

## Evidence Summary

The Git repository spans approximately **February 26, 2026 through July 15, 2026** and contains **172 commits**. The commit history shows several distinct development clusters rather than a steady rate of work.

| Period | Observations |
|---|---|
| Pre-Git | Approximately nine months of exploration using Google Sheets, website builders, GitHub Pages, and planning before the Django application. |
| Feb–Mar 2026 | Initial Django application, data model, deployment, authentication, maps, email, and project foundation. |
| April 2026 | Largest development burst. Uploads, staging tables, file handling, schema evolution, locations, maps, UI, and major architectural work. |
| May 2026 | Heavy refinement, filters, UI improvements, organization workflows, upload templates, authentication, and usability. |
| June 2026 | Production hardening, allauth migration, logging, activity tracking, upload process completion, cleanup tools. |
| July 2026 | Documentation, launch preparation, tutorials, and repository organization. |

## Major Development Clusters

### Phase 0 – Exploration (Pre-Git)

Approximately nine months of experimentation occurred before the repository was created. This work established the requirements and ultimately led to the decision to build a database application rather than another website.

**Estimated effort:** 250 hours

### Phase 1 – Learning

The transition into Python, Django, Git, and CS50 laid the technical foundation for the project.

**Estimated effort:** 180 hours

### Phase 2 – First Application

The earliest commits establish the Django application, deployment, mapping, email, and core functionality.

**Evidence:** concentrated commits during late February and March.

**Estimated effort:** 120 hours

### Phase 3 – Data Model

Repeated evolution of Organizations, Locations, Activities, Sessions, Regions, and related models demonstrates that substantial effort was invested in finding the correct data architecture.

**Estimated effort:** 220 hours

### Phase 4 – User Experience

A long series of commits focused on maps, filters, cards, responsive layouts, templates, and usability improvements.

Representative commit topics include:
- adding ongoing filters
- organization cards
- location tabs
- layout improvements
- map refinements

**Estimated effort:** 170 hours

### Phase 5 – Import Architecture

This is the largest engineering investment visible in the repository.

Evidence includes commits for:
- ActivityUpload
- staging tables
- pending records
- upload templates
- review workflow
- cleanup utilities
- publication process
- rollback considerations

This work spans multiple months and represents a complete ETL-style workflow rather than a simple CSV import.

**Estimated effort:** 360 hours

### Phase 6 – Production Readiness

Evidence includes:
- Render deployment
- PostgreSQL
- Postmark email
- allauth migration
- activity logging
- security improvements
- server configuration

**Estimated effort:** 140 hours

### Phase 7 – Organization Onboarding

Commits shift toward making the application usable by organizations through documentation, workflows, permissions, and upload support.

**Estimated effort:** 90 hours

### Phase 8 – Launch Preparation

Documentation, tutorials, repository cleanup, and launch polishing.

**Estimated effort:** 70 hours

## Revised Estimate

| Phase | Hours |
|---|---:|
| Exploration | 250 |
| Learning | 180 |
| First Application | 120 |
| Data Model | 220 |
| User Experience | 170 |
| Import Architecture | 360 |
| Production Readiness | 140 |
| Organization Onboarding | 90 |
| Launch Preparation | 70 |
| **Total** | **1,600 hours** |

## Confidence

The Git history substantially increases confidence in the engineering estimate because it confirms prolonged, clustered development rather than isolated feature additions. The remaining uncertainty comes primarily from the pre-Git exploration and from design, debugging, and research time that is not directly represented by commits.

## Next Revision

The next revision should map every commit into a phase and produce:
- commit counts by phase
- calendar timeline
- cumulative development curve
- evidence-adjusted hour estimates
