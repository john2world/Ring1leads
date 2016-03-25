# **rl_proto2: RingLead Data Optimization Platform**
###### The data optimization platform for sales and marketing pros
***

## **Product Overview**

Every department at every company relies on their CRM database.  Sales and marketing professionals rely on CRM data to be accurate, clean and complete to do their jobs.  While data management is historically the job of IT, the sales and marketing teams should have the means to easily and efficiently improve the quality of their data and to ensure that a high level of quality is maintained going forward.

The goal of this product is to improve sales and marketing performance with smart data operations.

These operations include but are not limited to deduplication, record enhancement, record validation, record completion and record normalization.  The system is extensible to allow the user or partners to implement third party or custom operations.

The Data Optimization Platform is a single application with multiple entry points and varied behavior based on user settings.  

With the Data Optimization Platform, users can:

- analyze  a Segment of their contact/company data stored in their CRM and marketing database and review data quality improvements over time.
- run some optimization actions on some subset of data or some incoming data (via web forms or API)
- create an endpoint so that data flowing into their connected system(s) leverage some
set of actions prior to entering that connected system.

The platform should also allow partner companies to build our data quality functions into their products.  For example, a company that provides person data as part of their offering may wish to call our Name Normalization API to provide their customers with properly formatted name information.


## **Product Roadmap**

_Note: Versions 0.1 - 0.9 will be suitable for a small group of users (5-10) to run batch programs and list imports.  We do not expect this to be suitable for sales.  We also do not expect this to be suitable for all RingLead customers to switch from one product to the new one._

### Version 0.1
###### Scheduled Release: February 5, 2016

In this version, users will be able to:

* register for a new account.
* connect with Salesforce.
* run a batch program on a set of data, get a quality score, and perform batch updates (deduplication, normalization and location optimization) on Leads in Salesforce.
* get a CSV file of the changes that _would be_ applied to the data set _but without actually applying those changes_ in the connected database.
* specify conditional filters for a batch program using all available fields in their connected system (Salesforce).

Some definitions:

* deduplication for batches, meaning:
    * setting matching logic (_Note_: one exact-match field is required.)
    * applying fuzzy logic (represented by "somewhat similar" and "very similar" in our UI).
    * setting default merge rules (aka Surviving Record Rules).
    * setting exception merge rules (aka Surviving Value Rules).
* normalization for batches meaning using all (or a simplified set) of the Broadlook Data Shield API options and applying them to the data set specified in the program
* address optimization for batches means using our location data provider to update address information


###### Go To Market

* Secure 10 alpha users; collect feedback.


### Version 0.2
###### Scheduled Release: April 8, 2016

In this version, users will be able to:

* import a CSV file, get a quality score, run some Actions on the file (normalization, location optimization) and optionally import that file to Salesforce.  When importing the file to Salesforce, we will need to evaluate the Dedupe rules twice: _first_ to dedupe records within the file _and again_ to prevent duplicates from being created in Salesforce.  (_Note_: We will evaluate CSV and Salesforce Leads as a single table)
* run batch program on Leads, Contacts, Accounts and Opportunities.
    * _Note_: batch programs will **not** work across tables in this release
    * _Note_: some functionality will not be available for Opportunities (e.g. Location Optimization)


### Version 0.3
###### Scheduled Release: May 6, 2016

* When importing a list to Salesforce, we will give the user the _option_ to compare (dedupe) their CSV file with Leads, Contacts or Accounts table in Salesforce.  This will replicate the functionality of the duplicate matching functionality that is available in [Unique Upload](https://www.youtube.com/watch?v=jvtujon5lTc).  (_Note_: We will evaluate CSV and Salesforce Leads, Contacts and Accounts as a single table.  There are some special rules that we will need to write for handling the creation of new contacts at existing Accounts, etc.)



## **Module Descriptions**

### *accounts*

A custom user model that handles user registration, login/logout and connection with external systems like Salesforce, Marketo, and others.

### *field_mapper*

todo: Caio to write up a few sentences on how this works.

### *integrations*

Contains specific authentication methods and operations for each connected system that we work with.

### *notifications*

Repository of notifications for a user related to their programs, billing information and/or customer support requests.

### *operations*

Contains different data operations that can be applied on many different types of programs.  Operations are written to be generic and expect a standard data input.  

### *payments*

Allows a user to manage their plans, method of payment.  Also allows a user to review payment history, invoices, and more.

### *qscore*

Generates a score, from 1-100, for a set of records representing the overall quality of a data set.  

The quality score is based on a variety of contributing factors including, but not limited to, data completeness, validity of email, phone and location information, age of data, recency of edits, and more.


## **Data Processing**

TODO: Javier to write up an explanation of how we work on each program type

### *Batch Programs*

TODO: writeup

### *List Import Programs*

TODO: writeup

### *Real-Time Programs*

Note: This is a future item and is not currently implemented.


## **Entity Relationship Diagrams**

This project includes two files: 1) rl_proto2.dot, and 2) rl_proto2_model.png that give an overview of the Django models.

These files were generated following the steps here:
  http://django-extensions.readthedocs.org/en/latest/graph_models.html


# **Setup**
***

## **Running the project locally on MacOS**

To run the project locally

1. Start Virtualenv ```source venv/bin/activate```
2. Start the Django web server: ```python manage.py runserver```
3. Start RabbitMQ server: ```/usr/local/sbin/rabbitmq-server```
4. Start Celery server: ```celery -A rl_proto2 worker```

**To install Kyoto Cabinet**

This project uses Kyoto Cabinet ( http://fallabs.com/kyotocabinet/ )

On Mac OS, you can use homebrew to install:

```
brew install kyoto-cabinet
```

## **Fixtures & Utilities**

Command to import CSV to your Salesforce account:

```
./manage.py import_csv you@mail.com --file /path/to/file.csv --object Lead
```

# **Resources & Documentation**
***

## Salesforce Resources
* Salesforce Developer Org Signup Page: https://developer.salesforce.com/signup
* Salesforce Fields Reference Guide: http://resources.docs.salesforce.com/198/17/en-us/sfdc/pdf/salesforce_field_names_reference.pdf

## Marketo Resources
* Marketo REST API Documentation: http://developers.marketo.com/documentation/rest/
