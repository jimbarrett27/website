{% extends "main.html" %}
{% block page_content %}

# Changelog

Here you can find the changelog for this website, which I shall update whenever I merge a pull request to the `main` branch, regardless of whether it introduces a front facing feature or not.

## **v3.7.1** - 07/08/2024
* Remove some unfinished pages
* Add patents to the publications page

## **v3.7.0** - 21/07/2023
* Rework how blog posts are loaded to no longer require a separate index file
* Add a custom 404 page for missing blog posts

## **v3.6.2** - 04/07/2023
* Add a sitemap

## **v3.6.1** - 31/03/2023
* Add a link to the relevant problem to the advent of code page

## **v3.6.0** - 24/03/2023
* Add a page to show my solutions to advent of code problems

## **v3.5.3** - 18/03/2023
* Upgrade backend to Python 3.11

## **v3.5.2** - 10/03/2023
* Added a link to the latest version of my CV to the homepage 

## **v3.5.1** - 19/04/2022
* A script for mocking messages sent to the bot when running locally
* Lay the groundwork for scheduled bot behaviour

## **v3.5.0** - 18/04/2022
* Add functionality for tracking gold stars
* Add a permissive robots.txt

## **v3.4.0** - 18/04/2022
* Refactor out the telegram bot functionality
* Add echo and weight tracking functionality to the bot
* Add some error checking to the bot

## **v3.3.0** - 17/04/2022
* Scrap the previous changes
* Create a route to act as a webhook for the telegram bot 

## **v3.2.0** - 01/11/2021

* Launch the app from a script rather than the command line
* Host a hello world telegram bot

## **v3.1.1** - 25/09/2021

* Refactor how the base page contents are passed to other templates
* Add Floor's STROOPWAFEL paper

## **v3.1.0**  -  23/09/2021 

* Introduced this changelog!

{% endblock %}
