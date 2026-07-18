# WildPaths Development History

**Version 0.4 (Working Draft)**

# Introduction

WildPaths did not begin as a software project.

It began with a practical problem. Organizations were collecting
valuable information about volunteer opportunities, training, and
events, but there was no simple way for people to discover it. The
information already existed, but it was scattered across many sources,
difficult to search, and challenging to keep current.

The original goal was **not** to build an application. In fact, every
effort was made to avoid building one. If the problem could be solved
using tools that organizations already knew---such as Google Sheets or
Google Sites---there would be no reason to ask volunteers to learn new
technology or maintain a custom system.

Each prototype answered an important question while exposing a new
limitation. As the understanding of the problem deepened, the solutions
became progressively more sophisticated. Eventually it became clear that
the problem had outgrown the available tools. Building a custom
application was no longer an ambition; it had become the simplest way to
solve the problem.

WildPaths exists because every simpler solution was explored first.

------------------------------------------------------------------------

# Part I -- Exploration

## Streamlit -- Can the idea work?

The first interactive prototype was built with Streamlit. The objective
was to determine whether a modern, searchable interface would make the
information significantly more useful.

It did.

Searching, filtering, maps, and card-based layouts demonstrated the
value of an interactive experience. However, keeping the underlying
information current proved difficult. The interface was promising, but
maintaining the data was not sustainable.

That shifted the project toward solving the data-management problem.

## Google Sheets -- Meet people where they already are

Google Sheets was not selected because spreadsheets make good databases.
It was selected because it was already the tool organizations used to
maintain their information.

The goal was to leverage an existing workflow instead of introducing new
technology. If organizations could continue maintaining their
information in a familiar environment, adoption would be much easier.

As the project evolved, the limitations of using a spreadsheet as the
primary data store became increasingly apparent. Relationships,
validation, and consistency all became more difficult as the data model
grew.

The spreadsheet was never the problem. It simply reached the limits of
what it was designed to do.

## Google Sites

Google Sites was evaluated as a way to publish the information without
writing a custom application. Although it was quick to assemble, it did
not provide enough flexibility for the desired user experience.

## Google Apps Script (24 Aug 2025)

Apps Script connected Google Sheets to a dynamic web application,
allowing information to be published directly from the spreadsheet while
preserving a familiar editing experience.

## HTML / JavaScript / JSON (12 Sep 2025)

A client-side application built with HTML, JavaScript, and JSON provided
complete control over the interface while keeping deployment
lightweight.

This phase introduced an important architectural insight: data published
for an application should be shaped around the needs of the user
interface rather than simply mirroring the underlying storage.

## Looking Back

Every prototype was an attempt to avoid unnecessary complexity. The
project did not move to a new technology because it was fashionable; it
moved because the current solution could no longer solve the problem
well enough.

------------------------------------------------------------------------

# Part II -- Learning

## CS50 (Sep 2025 -- Jan 2026)

Only after exhausting simpler approaches did it become clear that a
custom application was necessary. Learning Python, Django, Git, and
modern web development became a means to solve the problem---not the
goal itself.

For that reason, the educational journey is part of the project's
history but is treated separately from the engineering effort invested
in WildPaths.

------------------------------------------------------------------------

# Part III -- Building WildPaths

## 21 February 2026

The Django project folder was created on **21 February 2026**. This
marks the beginning of software development for WildPaths itself.

Subsequent revisions of this document will trace the application's
architectural evolution using Git history, recovered prototypes, and
historical screenshots.

------------------------------------------------------------------------

# Historical Artifacts

Current archive includes screenshots and source from:

-   Streamlit prototype
-   Google Sites prototype
-   Google Apps Script web application
-   HTML / JavaScript / JSON prototype
-   Early Django application

Artifacts are stored under `docs/images/`.
