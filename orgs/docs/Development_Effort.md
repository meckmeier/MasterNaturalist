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

### Phase 1 – Capstone to Render

At this point I had a working capstone for my class, and I refined it by adding to the data model and setting it up to use PostGre, and Render as the site. 
Feb 28-March 15. 2 weeks. 20 hours per week. 40 hours

**Estimated effort:** 40 hours/ 2 weeks.

### Phase 2 – First Application- Canopy

March 15 - Apr 4th. The earliest commits establish the Django application, deployment, mapping, email, and core functionality. Entry forms using formsets, refinement to the model, entry forms with rules for ease of entry.

**Evidence:** concentrated commits during late March. 

**Estimated effort:** 45 hours/ 3 weeks

### Phase 3 – WildPaths App is born

April 4th - May 6th renamed app to WildPaths. Repeated evolution of Organizations, Locations, Activities, Sessions, Regions, and related models demonstrates that substantial effort was invested in finding the correct data architecture. Also a lot of work on the look. Incorporated new logos, worked with Lyle on layout options, updated CSS, refined button build, etc. Bought domain name, and incorporated it into the Render site. Set up environment variables, refined the development environment.

* redesigning the data architecture
* evolving Organizations, Locations, Activities, and Sessions
* regions and geographic organization
* maps
* UI/CSS refinement
* logo work
* layout discussions
* domain purchase/setup
* Render configuration
* environment variables
* development environment refinement

**Estimated effort:** 80 hours/ 5 weeks

### Phase 4 – Organization Introduction

May 6-13: User Testing. Sage, Cassie and Becky provided some testing, and feedback. At this point there is not a lot of functionality, but refinements around bugs and making the flow of the app work better. A long series of commits focused on maps, filters, cards, responsive layouts, templates, and usability improvements.

The addition of allauth for authorization into the system introduced a series of bot attacks that used up all my email options (free from PostMark) so I had to kind of suspend everything that relied on email until I got the new allotment. I worked alot on adding in captcha and other defensive maneuvers to prevent bot attacks. Migrated DNS to Cloudflare. There were lots of infrastructure efforts during this phase.

In addition I reworked the site so that registration was not required for users to get the full browser experience. It simplified the need for email, and login overhead. I was able to rework all that and get it up and running at about the same time my email allotment reappeared. It also made the site a better "sell" to organizations since you didn't HAVE to be a master naturalist to use the site.

* user testing and feedback
* allauth
* email verification
* bot attacks
* spam accounts
* Cloudflare Turnstile
* Postmark
* DNS/DKIM issues
* Cloudflare DNS migration
* changing the site's registration model
* making public browsing work without authentication
* filters, maps, cards, templates, responsive behavior

**Estimated effort:** 60 hours / 3 weeks

### Phase 5 – Import Architecture

late May and early June - Implemented the new upload process. This is the largest engineering investment visible in the repository.

Evidence includes commits for:
- ActivityUpload
- staging tables
- pending records
- upload templates
- review workflow
- cleanup utilities
- publication process
- rollback considerations
- CSV encoding issues
- pandas compatibility
- Python version problems
- Render build failures
- column mapping
- RawLoadData
- staging models
- Pending_Location
- Pending_Activity
- Pending_Session
- location fingerprints
- duplicate detection
- matching existing locations
- merging pending locations
- review interfaces
- publishing
- cleanup
- rollback questions
- parsing categories
- dates
- session formats
- activity types
- multi-step workflow logic

This work spans multiple months and represents a complete ETL-style workflow rather than a simple CSV import.

**Estimated effort:** 75 hours / 3 weeks

### Phase 7 – Organization Onboarding/ Launch Prep

June and July. Adding in video help files, plus other user documentation. Minor adjustments to the flow. Introduced the calendar view, which caused me to create summary cards. Commits shift toward making the application usable by organizations through documentation, workflows, permissions, and upload support. There was a lot of "waiting" time during these days, while we tried to schedule a launch. I spent some time learning how to build videos, and edit them. 

**Estimated effort:** 50 hours / 2 months


## Revised Estimate

| Phase | Hours |
|---|---:|
| Exploration | 250 |
| Captstone to Render | 40 |
| First Application - Canopy | 45 |
| WildPathsWI | 80 |
| Organization Introduction | 60 |
| Import Architecture | 75 |
| Organization Onboarding/ Launch Prep | 50 |

| **Total** | **350 hours** |

## Confidence

The Git history substantially increases confidence in the engineering estimate because it confirms prolonged, clustered development rather than isolated feature additions. The remaining uncertainty comes primarily from the pre-Git exploration and from design, debugging, and research time that is not directly represented by commits.


