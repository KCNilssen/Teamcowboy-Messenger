<div align="center">

# Teamcowboy-Messenger

**Event alert messenger for Team Cowboy using the twilio messaging client**

<!-- ![Development Branch Status]() -->
<!-- ![Periodic External Test Status]() -->
<!-- [![PyPI version](https://badge.fury.io/py/python-teamcowboy-api.svg)](https://badge.fury.io/py/python-teamcowboy-api)
![Main Branch Status](https://github.com/KCNilssen/TeamCowboyApi-Python/actions/workflows/build-and-test.yml/badge.svg?event=push)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-teamcowboy-api)
![GitHub](https://img.shields.io/github/license/KCNilssen/TeamCowboyApi-Python) -->

![Logos](.github/images/tctwlogo.png)

<div align="left">

## Getting Started

*Teamcowboy-Messenger* is a Python script that with scheduled execution through github actions sends event alerts to team members from Team Cowboy via SMS using Twilio. *Teamcowboy-Messenger* Sends game event announcements four days before the event and game event reminders two days before the event. If there is an update to any event within the 4 day window, *Teamcowboy-Messenger* will alert team members via SMS to the updated event. 

Api keys, login credentials and other sensitive information is safely stored and used with github secrets.


<div align="center">


<div align="left">


## Github Actions Usage

### Schedule
```yml
on:
  schedule:
    # Run every day at 4:25/3:25 (DST) pm PST
    - cron:  '25 23 * * *'
```
### Secrets
```yml
- name: 
    env:
        PRIVATEAPIKEY: ${{ secrets.TCPRIVATEAPIKEY }}
        PUBLICAPIKEY: ${{ secrets.TCPUBLICAPIKEY }} 
        USERNAME: ${{ secrets.TCUSERNAME }}
        PASSWORD: ${{ secrets.TCPASSWORD }}
        TWILIOACCOUNTSID: ${{ secrets.TWILIOACCOUNTSID }}
        TWILIOAUTHTOKEN: ${{ secrets.TWILIOAUTHTOKEN }}
        TWILIOPHONENUMBER: ${{ secrets.TWILIOPHONENUMBER }}
        MYPHONENUMBER: ${{ secrets.MYPHONENUMBER }}
        BENPHONENUMBER: ${{ secrets.BENPHONENUMBER }}
        TEAMNAME: ${{ secrets.TEAMNAME }}
```

### Run
```yml
run: |
    python3 ./eventmessenger.py TEAMNAME PRIVATEAPIKEY PUBLICAPIKEY USERNAME PASSWORD TWILIOACCOUNTSID TWILIOAUTHTOKEN TWILIOPHONENUMBER
```