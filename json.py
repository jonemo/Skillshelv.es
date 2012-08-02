from google.appengine.dist import use_library
use_library('django', '1.2')

import os.path
import re

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.api import mail

import fluidinfo
import skillshelves
	
class MainPage(webapp.RequestHandler):
	def get(self, page):
	
		user = users.get_current_user()
		
		if re.match("^[A-Za-z0-9_-]*$", page):
			# the page displayed if the root url is requested
			if not page:
				self.response.out.write('404')
			
			elif page == 'usernamefree':
				username = self.request.get("u")
				query = skillshelves.DBUsers.all()
				query.filter('username = ', username)
				dbresults = query.fetch(1)
				
				if dbresults:
					self.response.out.write('ne')
				else:
					self.response.out.write('jo')

			elif page == 'addbooktouser':
				objectid = self.request.get("o")
				
				if user and skillshelves.get_username(user) :
					# create users tag on fluidinfo
					skillshelves.connectToFluidinfo()
					headers, content = fluidinfo.call('PUT', '/objects/' + objectid + '/' + skillshelves.fluidinfoRootNamespace() + '/user/' + skillshelves.get_username(user), body='has')
					self.response.out.write('jo')
					self.response.out.write(headers)
					self.response.out.write(content)
				else:	
					self.response.out.write('ne')
					
			elif page == 'deletebookfromuser':
				objectid = self.request.get("o")
				
				if user and skillshelves.get_username(user) :
					# delete users tag on fluidinfo
					skillshelves.connectToFluidinfo()
					headers, content = fluidinfo.call('DELETE', '/objects/' + objectid + '/' + skillshelves.fluidinfoRootNamespace() + '/user/' + skillshelves.get_username(user))
					
					self.response.out.write('jo')
				else:	
					self.response.out.write('ne')

		else:
			self.response.out.write('404')

 
	def post(self, page):
		if re.match("^[A-Za-z0-9_-]*$", page):
			# the page displayed if the root url is requested
			if not page:
				self.response.out.write('404')
			
			elif page == 'sendBetterSkills':
				msg = self.request.get("msg")
				book = self.request.get("book")
				mail.send_mail('jonas.neubert@gmail.com', 'jn@jonemo.de', 'Skill suggestion', book + ' --- ' + msg)
				self.response.out.write('jo')

		else:
			self.response.out.write('404')	
 
application = webapp.WSGIApplication([('/json/(.*)', MainPage)],debug=True)
 
def main():
   run_wsgi_app(application)
 
if __name__ == "__main__":
   main()