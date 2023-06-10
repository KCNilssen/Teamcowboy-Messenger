from typing import List, Union
from dataclasses import dataclass

import sys
import os
from datetime import datetime, timedelta, timezone

from twilio.rest import Client
from teamcowboyapi import Teamcowboy, Event, User, Attendancelist

@dataclass
class Eventmessage:
    """
    The Eventmessage data class is used to represent a message related to an 
    event. 
    
    Attributes:
    -----------
    messagetype : str
        String representing the type of message (e.g. "alert", "update", etc.)
    eventtype : str
        The event type
    message : str
        String containing the message text
    eventid : int
        Unique identifier for the event
    teamid : int
        unique identifier for the team
    comments : str
        Additional comments or notes related to the message or event.
    """
    messagetype: str
    eventtype: str
    message: str
    eventid: int
    teamid: int
    comments: str

def Getteamidfor(tmcwby: Teamcowboy, teamname: str) -> int:
    """
    This function returns the team id from a team name
    
    Attributes:
    -----------
    tc : Teamcowboy
        Teamcowboy api object to workwith
    teamname : str
        Team name you want to get the teamid for

    Returns:
    --------
    teamid : int
        This is the teamid associated with the team name provided

    Exceptions:
    -----------
    When teamname is not found in users names a LookupError is raised.
    This alerts the user that they are using an incorrect teamname and
    as a result a teamid could not be found.
    """
    teams = tmcwby.User_GetTeams()

    for team in teams:
        if team.name == teamname:
            return team.teamId
    
    raise LookupError("Failed to find teamname in users teams. No teamid found.")

def Addrsvpcounts(event: Event, attendancelist: Attendancelist) -> Event:
    """
    Adds rsvp count message to end of message text from Event object and
    attendance list object.
    
    Attributes:
    -----------
    event : Event
        Event object to add rsvp for
    attendancelist : Attendancelist
        Attendance list object to add rsvp from
    """
    for count in attendancelist.countsByStatus:   
        if (count.status).lower() == "yes":            
            event.message += F"\n\nMen [{count.counts.byGender['m']}] Woman [{count.counts.byGender['f']}]"
            return event


def Handlemessages(teamcowboy: Teamcowboy, twilioclient: Client, twilionumber: str, handledEvents: List[Eventmessage]):
    """
    Handles finishing of event message creation and sends messages to team 
    members.

    Attributes:
    -----------
    teamcowboy : Teamcowboy
        Team cowboy python wrapper object
    twilioclient : Client
        Twilio client object
    twilionumber : str
        Phone number associated with twilio account
    handledEvents : List[Eventmessage]
        List of handled events to send messages for
    """
    if handledEvents:

        # Make a contact list
        # contactlist = {}
        # for player in teamcowboy.Team_GetRoster(208):
        #     if player.teamMeta.teamMemberType.titleLongSingular == "Full-time Team Member":
        #         print (player.userId, player.fullName)
        #         contactlist[str(player.userId)] = player.phone1

        # Spoof the contact list for testing
        contactlist = {os.environ.get("MYTCUSERID"):os.environ.get("MYPHONENUMBER"), os.environ.get("BENTCUSERID"):os.environ.get("BENPHONENUMBER"), os.environ.get("HARRYTCUSERID"):os.environ.get("HARRYPHONENUMBER")} # w/ ben
        # contactlist = {os.environ.get("MYTCUSERID"):os.environ.get("MYPHONENUMBER")} 

        for event in handledEvents:

            # Get the attendance list for this event
            attendancelist = teamcowboy.Event_GetAttendanceList(event.teamid, event.eventid)

            # Create str for attending rsvp numbers for men and woman
            if event.eventtype == "game":
                event = Addrsvpcounts(event, attendancelist)

            # Loop through contact list and send messages to active full-time 
            # team members
            for userid, phonenumber in contactlist.items():
                builtmessage = event.message

                # If our message is an announcment or a reminder then add the 
                # specific recipients rsvp status to their message.
                if event.messagetype == "announcement" or event.messagetype == "reminder":
                    if event.eventtype != "bye" and event.eventtype == "game":
                        for user in attendancelist.users:      
                            if str(user.user.userId) == userid:
                                builtmessage += F"\n\nRSVP Status: {user.rsvpInfo.statusDisplay}"
                
                # If there are comments with this eventmessage lets add them
                if event.comments:
                    builtmessage += F"\n\n{event.comments}"

                # Send message via twilio
                twiliosentmessage = twilioclient.messages.create(
                    body = builtmessage,
                    from_ = twilionumber,
                    to = phonenumber
                )

def Addeventtitle(titletype: str) -> str:
    """
    Creates an event title string and returns it
    
    Parameters:
    -----------
    titletype : str
        Title type to create title string for
    """        
    if titletype == "updated":
        return "Updated event for Trouble Blueing\n\n"
    elif titletype == "postponed":
        return "Postponed event for Trouble Blueing\n\n"
    elif titletype == "canceled":
        return "Canceled event for Trouble Blueing\n\n"
    elif titletype == "forfeited":
        return "forfeited event for Trouble Blueing\n\n"
    elif titletype == "reminder":
        return "Event reminder for Trouble Blueing\n\n"
    elif titletype == "announcement":
        return "Event announcement for Trouble Blueing\n\n"
    else:
        return F"{titletype}\n\n"

def Addgamemessage(event: Event) -> str:
    """
    Creates and returns the message body for a game event.

    Parameters:
    -----------
    event : Event
        Event object to create message for
    """
    team1_color = event.shirtColors.team1.title if event.shirtColors.team1 and event.shirtColors.team1.title else "None"
    team2_color = event.shirtColors.team2.title if event.shirtColors.team2 and event.shirtColors.team2.title else "None"

    vstag = F"{event.homeAway} [{team1_color}] vs. {event.title} [{team2_color}]"
    dayofweek= datetime.strptime(event.dateTimeInfo.startDateLocal,'%Y-%m-%d').strftime('%A')
    datetag = F"{dayofweek} {event.dateTimeInfo.startDateLocalDisplay} @ {event.dateTimeInfo.startTimeLocalDisplay}"
    locationtag = F"{event.location.name}\n{event.location.address.displayMultiLine}"
    return F"{vstag}\n{datetag}\n\n{locationtag}"

def Addbyemessage(event) -> str:
    """
    Creates and returns the message body for a bye event.

    Parameters:
    -----------
    event : Event
        Event object to create message for
    """
    byetag = "Bye (no game)"
    dayofweek= datetime.strptime(event.dateTimeInfo.startDateLocal,'%Y-%m-%d').strftime('%A')
    datetag = F"{dayofweek} {event.dateTimeInfo.startDateLocalDisplay} @ {event.dateTimeInfo.startTimeLocalDisplay}"
    return F"{byetag}\n{datetag}"

def Addpracticemessage(event) -> str:
    """
    Creates and returns the message body for practice bye event.

    Parameters:
    -----------
    event : Event
        Event object to create message for
    """
    practicetag = "Practice (Team)"
    dayofweek= datetime.strptime(event.dateTimeInfo.startDateLocal,'%Y-%m-%d').strftime('%A')
    datetag = F"{dayofweek} {event.dateTimeInfo.startDateLocalDisplay} @ {event.dateTimeInfo.startTimeLocalDisplay}"
    locationtag = F"{event.location.name}\n{event.location.address.displayMultiLine}"
    return F"{practicetag}\n{datetag}\n\n{locationtag}"

def Addmeetingemessage(event) -> str:
    """
    Creates and returns the message body for a meeting event.

    Parameters:
    -----------
    event : Event
        Event object to create message for
    """
    meetingtag = "Practice (Team)"
    dayofweek= datetime.strptime(event.dateTimeInfo.startDateLocal,'%Y-%m-%d').strftime('%A')
    datetag = F"{dayofweek} {event.dateTimeInfo.startDateLocalDisplay} @ {event.dateTimeInfo.startTimeLocalDisplay}"
    locationtag = F"{event.location.name}\n{event.location.address.displayMultiLine}"
    commentstag = ""
    if event.comments:
        commentstag = F"\n\n{event.comments}"
    return F"{meetingtag}\n{datetag}\n\n{locationtag}{commentstag}"

def Addotheremessage(event) -> str:
    """
    Creates and returns the message body for a "other" event.

    Parameters:
    -----------
    event : Event
        Event object to create message for
    """
    meetingtag = F"{event.eventType}"
    # datetag = event.oneLineDisplay
    # locationtag = F"{event.location.address.displayMultiLine}"
    # commentstag = ""
    if event.comments:
        commentstag = F"\n\n{event.comments}"
    return F"{meetingtag}"


def Createeventmessage(event: Event, messagetype: str) -> str:
    """
    
    Attributes:
    -----------
    event : Event
        Event object to create message for
    messagetype : str
        String representing the message type
    """
    message = ""
    message += Addeventtitle(messagetype)
    
    if event.eventType == "game":
        message += Addgamemessage(event)
    elif event.eventType == "bye":
        message += Addbyemessage(event)
    elif event.eventType == "practice":
        message += Addpracticemessage(event)
    elif event.eventType == "meeting":
        message += Addmeetingemessage(event)
    elif event.eventType == "other":
        message += Addotheremessage(event)

    return message


def Handleupdatedevent(event: Event) -> Eventmessage:
    """
    Handles events that have been updated from its original state.

    Attributes:
    -----------
    event : Event
        Event object to handle updated event for
    """
    if event.dateLastUpdatedUtc != event.dateCreatedUtc:
        if datetime.strptime(event.dateLastUpdatedUtc,'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) > (datetime.now(timezone.utc) - timedelta(days=1)):           
            return Eventmessage("updated", 
                                event.eventType, 
                                Createeventmessage(event, "updated"), 
                                event.eventId, 
                                event.team.teamId, 
                                "")


def Handletodayevent(event: Event) -> Union[Eventmessage, None]:
    """
    Takes an event that is happening today and handles it. We check if the 
    event is postponed, canceled, or forfeited and return a Eventmessage
    object for them or we check if the event has been updated since we last 
    checked. This would be 24 hours ago since that is the rate at which we 
    run this script. If none of these conditions are met, then return None.

    Parameters:
    -----------
    event : Event
        Event object that takes place today and needs to be handled
    """
    if event.status == "postponed":
        # Send out a postponed alert
        return Eventmessage("postponed", 
                            event.eventType, 
                            Createeventmessage(event, "postponed"), 
                            event.eventId, 
                            event.team.teamId, 
                            "")
    elif event.status == "canceled":
        # Send out a cancellation notice
        return Eventmessage("canceled", 
                            event.eventType, 
                            Createeventmessage(event, "canceled"), 
                            event.eventId, 
                            event.team.teamId, 
                            "")
    elif event.status == "forfeited":
        # Send out a forfeited alert?
        return Eventmessage("forfeited", 
                            event.eventType, 
                            Createeventmessage(event, "forfeited"), 
                            event.eventId, 
                            event.team.teamId, 
                            "")
    else:
        # We want to check if there has been updates since two days ago
        return Handleupdatedevent(event)


def Handletwodaysoutevent(event: Event) -> Eventmessage:
    """
    Takes an event that happens two days from now and "handles" it.

    Parameters:
    -----------
    event : Event
        Event object that takes place two days from now and needs to be handled
    """
    # if (event.eventType != "bye"):
        # If the event is not a bye we need to send an event reminder.
        # This is in standard with our current practices    
    comment = ""

    if event.dateLastUpdatedUtc != event.dateCreatedUtc:
        if event.dateLastUpdatedUtc < (datetime.now(timezone.utc) - timedelta(days=1)):
            comment = "\n\n Event updated: Check detailes for changes if any"

    return Eventmessage("reminder", 
                        event.eventType, 
                        Createeventmessage(event, "reminder"), 
                        event.eventId, 
                        event.team.teamId, 
                        comment)


def Handlefourdaysoutevent(event: Event) -> Eventmessage:
    """
    Takes an event that happens four days from now and "handles" it.

    Parameters:
    -----------
    event : Event
        Event object that takes place two days from now and needs to be handled
    """
    if (event.eventType != "other" and event.eventType != "meeting"):
        # Lets only send one message for others and meetings twi days in 
        # advance, excluding the four days in advance to cut back on
        # the number of messages sent over twilio
        comment = ""

        if event.dateLastUpdatedUtc != event.dateCreatedUtc:
            if event.dateLastUpdatedUtc < (datetime.now(timezone.utc) - timedelta(days=1)):
                comment = "\n\n Event updated: Check detailes for changes if any"

        return Eventmessage("announcement", 
                    event.eventType, 
                    Createeventmessage(event, "announcement"), 
                    event.eventId, 
                    event.team.teamId, 
                    comment)


def Handleteamevents(events: List[Event]) -> List[Eventmessage]:
    """
    Handles team events 

    Attributes:
    -----------
    events : List[Event]
        List of team event objects to be handled
    """
    nowdate = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), '%Y-%m-%d')
    twodate = datetime.strptime((datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), '%Y-%m-%d')
    fourdate = datetime.strptime((datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"), '%Y-%m-%d')
    handledevents = []
    
    for event in events:
        eventdate = datetime.strptime(event.dateTimeInfo.startDateLocal, '%Y-%m-%d')
        handledevent = None

        if eventdate == nowdate:
            handledevent = Handletodayevent(event) 
        elif eventdate == twodate:
            handledevent = Handletwodaysoutevent(event)
        elif eventdate == fourdate:
            handledevent = Handlefourdaysoutevent(event)
        else:
            handledevent = Handleupdatedevent(event)
        
        if handledevent:
            handledevents.append(handledevent)

    return handledevents
            

def main(teamname:str, privateapikey:str, publicapikey:str, username:str, password:str, account_sid:str, auth_token:str, phonenumber:str):
    """
    Uses the teamcowboy python wrapper and the Twilio messaging client to be
    called by github actions every 24 hours to send text messages to active 
    team members that alerts them to events and changes to events.

    Sends messages out 4 days in advance and 2 days in advance. 
    If there is an update to an event between the programs running, that update
    will then be sent out as a text to alert team members.
    
    Attributes:
    -----------
    teamname : str
        Team name you want to be working with
    privateapikey : str
        This is the private API key granted to you along with your API account.
    publicapikey : str
        This is the public API key granted to you along with your API account.
    username : str
        Team leaders accound username
    password : str
        Team leaders account password
    """
    teamcowboy = Teamcowboy(privateapikey, publicapikey, username, password)
    twilioclient = Client(account_sid, auth_token)
    team_id = Getteamidfor(teamcowboy, teamname)

    teamevents = Handleteamevents(teamcowboy.User_GetTeamEvents(teamId=team_id))

    if not teamevents:
        print ("No upcoming team events scheduled")
    else:
        Handlemessages(teamcowboy, twilioclient, phonenumber, teamevents)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])

