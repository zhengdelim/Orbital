# Request handlers for http://fighthazepledge.appspot.com/
# Written as example app for SoC Orbital program
# Author: Lee Wee Sun

# To run the cron job that the PSI reading, you need to get your own api-key
# from https://developers.data.gov.sg/ and replace the dummy key in the GetPSI class.

import urllib
import webapp2
import jinja2
import os
import datetime
import urllib2
import json

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import mail

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))

# Globals
max_days = 30
psi_query = ndb.Query()

# Datastore definitions
class Preference(ndb.Model):
    # Models a person's preference. Key is the nickname.
    email = ndb.StringProperty() # user email
    psi_limit = ndb.IntegerProperty()  # max acceptable PSI
    day_limit = ndb.IntegerProperty()  # max day above acceptable PSI before reminder
    last_reminder = ndb.DateProperty() # the last time reminder was sent

class PSI(ndb.Model):
    # Daily PSI at 12:00 Singapore time
    psi_date = ndb.DateProperty() # date of the record
    psi_measurement = ndb.IntegerProperty() # PSI on that date

# This part for the front page
class MainPage(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            template_values = {
                'user_nickname': users.get_current_user().nickname(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('front.html')
            self.response.out.write(template.render(template_values))
        else:
            template = jinja_environment.get_template('front.html')
            self.response.out.write(template.render())

# This is the About page
class About(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            template_values = {
                'user_nickname': users.get_current_user().nickname(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('about.html')
            self.response.out.write(template.render(template_values))
        else:
            template = jinja_environment.get_template('about.html')
            self.response.out.write(template.render())

# Handler for pledge page                            
class Pledge(webapp2.RequestHandler):
    """ Pledge and info. """

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            template_values = {
                'user_nickname': users.get_current_user().nickname(),
                'logout': users.create_logout_url(self.request.host_url),
                }
            template = jinja_environment.get_template('pledge.html')
            self.response.out.write(template.render(template_values))
        else:
            template = jinja_environment.get_template('pledge.html')
            self.response.out.write(template.render())


# Handler for the Reminder page
class Reminder(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already            # Retrieve person
            curr = ndb.Key('Preference', users.get_current_user().nickname())
            person = curr.get()
            if person == None:
                template_values = {
                    'user_nickname': users.get_current_user().nickname(),
                    'logout': users.create_logout_url(self.request.host_url),
                    'max_limit': max_days,
                    }
                template = jinja_environment.get_template('reminder.html')
                self.response.out.write(template.render(template_values))
            else:
                template_values = {
                    'user_nickname': users.get_current_user().nickname(),
                    'logout': users.create_logout_url(self.request.host_url),
                    'curr_psi_limit': person.psi_limit,
                    'curr_day_limit': person.day_limit,
                    'max_limit': max_days,
                    }

                template = jinja_environment.get_template('reminder.html')
                self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

    def post(self):
        # Retrieve person
        curr = ndb.Key('Preference', users.get_current_user().nickname())
        person = curr.get()
        if person == None:
            person = Preference(id=users.get_current_user().nickname())
            person.email = users.get_current_user().email()
        psi_limit = self.request.get_range('psilimit')
        day_limit = self.request.get_range('daylimit')
        singapore_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        person.last_reminder = singapore_time.date()
        if (psi_limit > 0) and (day_limit > 0) and (day_limit <= max_days):
            person.psi_limit = psi_limit
            person.day_limit = day_limit
            person.put()

        template_values = {
            'user_nickname': users.get_current_user().nickname(),
            'logout': users.create_logout_url(self.request.host_url),
            'curr_psi_limit': person.psi_limit,
            'curr_day_limit': person.day_limit,
            'max_limit': max_days,
            }

        template = jinja_environment.get_template('reminder.html')
        self.response.out.write(template.render(template_values))

# For deleting reminder
class DeleteReminder(webapp2.RequestHandler):
    # Delete reminder of a user

    def get(self):
        pref = ndb.Key('Preference', users.get_current_user().nickname())
        pref.delete()
        self.redirect('/reminder')

# Check the day's PSI from data.gov.sg API and add to datastore. Read past PSI into global variable. Call this through CRON job after midday once a day some time before Send Reminder.
class GetPSI(webapp2.RequestHandler):

    def get(self):
        global psi_query # global to use for later requests
        
        # Call data.gov.sg API
        headers = { 'api-key': 'Your own key here' }
        singapore_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        currdate = singapore_time.date()
        data = { 'date_time': currdate.isoformat() + 'T12:00:00' }
        url = 'https://api.data.gov.sg/v1/environment/psi?' + urllib.urlencode(data)
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        assert response.code == 200
        
        response_dict = json.loads(response.read())
        # Check the contents of the response.
        result = response_dict["items"][0]["readings"]["psi_twenty_four_hourly"]["national"]
        
        qry = PSI.query(PSI.psi_date == currdate)
        if qry.count() == 0:
            psi = PSI(psi_date=currdate,psi_measurement=result)
            psi.put()
            
        limit_date = currdate + datetime.timedelta(days = -max_days)
        psi_query = PSI.query(PSI.psi_date > limit_date).order(-PSI.psi_date)

# Send reminders. Run through CRON job after midday once a day some time after calling GetPSI.
class SendReminder(webapp2.RequestHandler):

    def get(self):
        qry = Preference.query()
        singapore_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        for pref in qry:
            # Check that day_limit has passed since last reminder
            if pref.last_reminder + datetime.timedelta(days=pref.day_limit) <= singapore_time.date():
                curr_email =  pref.email
                psi_target = pref.psi_limit
                day_target = pref.day_limit
                count = 1
                send_reminder = False
                # Check that every day in day_limit pass psi_target
                for past_psi in psi_query:
                    if past_psi.psi_measurement < psi_target:
                        break
                    else:
                        if count == day_target:
                            send_reminder = True
                            break
                        else:
                            count = count + 1
                if send_reminder:
                    message = mail.EmailMessage(sender="FightHazePledge <fighthazeapp@gmail.com>", subject="Reminder from FightHazePledge")

                    message.to = pref.email
                    message.body = """
Hi,

This is a reminder that you pledged to fight haze by buying products certified for sustainability whenever there are choices. To be reminded of the types of products that you should buy or to stop the reminders, visit http://fighthazepledge.appspot.com/

FightHazePledge
"""
                    
                    message.send()
                    pref.last_reminder = singapore_time.date()
                    pref.put()


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/fighthaze', MainPage),
                               ('/about', About),
                               ('/pledge', Pledge),
                               ('/getpsi', GetPSI),
                               ('/sendreminder', SendReminder),
                               ('/deletereminder', DeleteReminder),
                               ('/reminder', Reminder)],
                              debug=True)

