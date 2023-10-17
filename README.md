# Fuhrem App

## Our project is a web application that enables users to search for creative assets on Shutterstock, with options for selecting categories (Photography, Vector, Illustration, Video), specifying search criteria, and automating the data retrieval. Users can store and process the collected data, then export it as an Excel file.

## Features

- Choose from four different categories: Photography, Vector, Illustration, Video.
- Specify search criteria and the number of results you want.
- Automate web actions using Playwright to retrieve keywords and titles from Shutterstock.
- Store the collected information in a database.
- Process and present the data based on user selections.
- Export information as an Excel file.

## Getting Started

### Prerequisites

These are the commands necessary for the program to run:

```bash
pip install beautifulsoup4
pip install matplotlib
pip install openpyxl
pip install pandas
pip install seaborn
pip install django==4.1.3
pip install playwright
playwright install
```
### Installation

#### Clone the repository
```bash
git clone https://github.com/Poeron/fuhremapp
```

### Usage
type this in terminal to start the project:
```bash
python manage.py runserver
```
the domain is: http://127.0.0.1:8000/
