import urllib
import webapp2
import jinja2
import os

from google.appengine.api import users
from google.appengine.ext import ndb

# Globals
max_days = 30

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))

class MainPage(webapp2.RequestHandler):
    """ Handler for the front page."""

    def get(self):
        template = jinja_environment.get_template('front.html')
        self.response.out.write(template.render())

class MainPageUser(webapp2.RequestHandler):
    """ Front page for those logged in """

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
            self.redirect(self.request.host_url)

class Pledge(webapp2.RequestHandler):
    """ Front page for those logged in """
# Write the get method for the template pledge.html


# Datastore definitions
class Preference(ndb.Model):
    # Models a person's preference. Key is the nickname.
    email = ndb.StringProperty() # user email
    psi_limit = ndb.IntegerProperty()  # max acceptable PSI
    day_limit = ndb.IntegerProperty()  # max day above acceptable PSI before reminder
    last_reminder = ndb.DateProperty() # the last time reminder was sent


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

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/fighthaze', MainPageUser),
                               ('/pledge', Pledge),
                               ('/reminder', Reminder)],
                              debug=True)
