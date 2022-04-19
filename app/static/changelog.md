{% extends "main.html" %}
{% block page_content %}

# Changelog

Here you can find the changelog for this website, which I shall update whenever I merge a pull request to the `main` branch, regardless of whether it introduces a front facing feature or not.

## **v3.5.1** - 19/04/2022
* A script for mocking messages sent to the bot when running locally
* Lay the groundwork for scheduled bot behaviour

## **v3.5.0** - 18/04/2022
* Add functionality for tracking ⭐️
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