# Timeline Reports Script For the Career and Life Design Center at Oakland University

A script that uses data from Handshake reports to create a Timeline of all student engagements from 2019-present. With this timeline, the user has the ability to generate several other reports.

> [!NOTE]
>
> This script only generates csv files with the data of each report contained. If you need these reports in a better format (Google Sheets), that will have to be done separately.

> [!IMPORTANT]
>
> For the script to function, the configuration must be set properly.

See [Setup](#setup) for the necessary setup for these scripts to run automatically.

## Features

This script can currently create a timeline and 3 different types of reports based on a user-defined config file.

- [x] Report timeline of all student interactions including (Applications, Appointments, Events, Career Fairs, and Logins) from 2019-Present.
- [x] Report student engagements following CLDC appointments.
- [x] Report student engagements following COM1100 presentations.
- [x] Report student engagements vs. their FDS outcomes.

### Generated Report Types

All producable reports are delivered in three types of formats: 
> **Timeline:** Creates a timeline of student identifiers with their engagement types and dates.
>
>   | Student_ID      | Descriptive Information... | Event_Type      | Date     |
>   |-----------------|----------------------------|-----------------|----------|
>   | 000001          | ...                        | Logins          | 20240101 |
>   | 000001          | ...                        | Career_Fairs    | 20240103 |
>   | 000002          | ...                        | Appointments    | 20250102 |

> **Aggregate:** Balances student identifier and descriptive information with timeline aggregate counts.
>
>   | Student_ID      | Descriptive Information... | Total {Engagement Types}  |
>   |-----------------|----------------------------|---------------------------|
>   | 000001          | ...                        | 1 | 5 | 7 | 3 | 10        |
>   | 000002          | ...                        | 2 | 6 | 4 | 5 | 11        |
>   | 000003          | ...                        | 1 | 0 | 0 | 3 | 6         |

> * **Melted:** Takes the aggregated report and melts it for use in different visualization softwares.
>
>   | Student_ID      | Descriptive Information... | Event_Type  | Count | Year      |
>   |-----------------|----------------------------|-------------|-------|-----------|
>   | 000001          | ...                        | Logins      | 10    | Freshman  | 
>   | 000001          | ...                        | Logins      | 12    | Sophomore | 
>   | 000001          | ...                        | Logins      | 15    | Junior    | 

### Report Options

> ##### Timeline
> A timeline following the timeline format in [Report Types](#generated-report-types) of all student engagements in the following categories taken from scheduled Handshake Reports:
> * Applications
> * Appointments
> * Career_Fairs
> * Events
> * Logins

> ##### CLDC 
> Produces two reports that summarize student engagement following a CLDC appointment. The two reports are in the following [Report Types](#generated-report-types) formats:
> * Timeline
> * Aggregate

> ##### COM1100 
> Produces six reports that summarize student engagement following 1 COM1100 presentation, 2 COM1100 presentations, and no COM1100 presentations. Each of the conditions have 2  reports following [Report Types](#generated-report-types) formats:
> * Aggregate
> * Melt

> ##### FDS
> Produces two reports that summarize past student engagement for students that have filled out their First Destination Surverys. The two reports are in the following [Report Types](#generated-report-types) formats:
> * Aggregate
> * Melt

## Setup

1. Ensure all [dependencies](#dependencies) are configured and running properly
2. Clone the repository
   - If installing from github, use `-git clone https://github.com/CLDC-OU/Timeline_Reports`
3. Configure [Files](#configuring-files)
4. Configure [Reports](#configuring-reports)
5. Run main.py

## Dependencies

See [requirements.txt](requirements.txt) for a list of required packages.

```py
pip install -r requirements.txt
```

## Configuring Files

Files are setup in src/config/csv.config.json

> [!NOTE]
> src/config/config.structure.json includes required and optional formatting guidelines for all necessary reports that can be run in this script.
