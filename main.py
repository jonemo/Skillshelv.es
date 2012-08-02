from google.appengine.dist import use_library
use_library('django', '1.2')

import os.path
import re
import random

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

import fluidinfo
import skillshelves
	
 
class MainPage(webapp.RequestHandler):
	def get(self, page):

		# this is the dictionary in which we keep all template values
		template_values = {
			'skillshelves_logo' : '<span class="skillshelves"><span class="blue">S</span><span class="lightblue">K</span><span class="orange">I</span><span class="blue">L</span><span class="lightblue">L</span><span class="orange">S</span><span class="blue">H</span><span class="lightblue">E</span><span class="orange">L</span><span class="blue">V</span><span class="lightblue">E</span><span class="orange">S</span></span>',
			'skillshelf_logo' : '<span class="skillshelves"><span class="blue">S</span><span class="lightblue">K</span><span class="orange">I</span><span class="blue">L</span><span class="lightblue">L</span><span class="orange">S</span><span class="blue">H</span><span class="lightblue">E</span><span class="orange">L</span><span class="blue">F</span></span>'
		}
		
		# determine the oauth username of the currently logged in user
		user = users.get_current_user()
		
		if user:  # signed in already
			template_values["user_nickname"] 		= user.nickname()
			template_values["user_email"] 			= user.email()
			template_values["user_id"] 				= user.user_id()
			template_values["federated_identity"]	= user.federated_identity()
			template_values["federated_provider"]	= user.federated_provider()
			template_values['logout_url']			= users.create_logout_url('/_logout')
			if skillshelves.do_we_know_this_guy(user):
				template_values['username']			= skillshelves.get_username(user)
		else:
			template_values["google_login_url"] 	= users.create_login_url(federated_identity='google.com/accounts/o8/id', dest_url='/_login')
			template_values["yahoo_login_url"] 		= users.create_login_url(federated_identity='yahoo.com', dest_url='/_login')
			template_values["myspace_login_url"] 	= users.create_login_url(federated_identity='myspace.com', dest_url='/_login')
			template_values["aol_login_url"] 		= users.create_login_url(federated_identity='aol.com', dest_url='/_login')
			template_values["myopenid_login_url"] 	= users.create_login_url(federated_identity='myopenid.com', dest_url='/_login')
		
		# the list of tags is needed in various  places, so we make it globally available to any page
		template_values["tag_list"] = []
		template_values['taglistasurlparams'] = ''
		tag_list = skillshelves.get_tag_list()
		for tag in tag_list :				
			template_values["tag_list"].append(tag)
			template_values['taglistasurlparams'] =  template_values['taglistasurlparams'] + '&tag=skillshelves/skills/' + tag['tag']

		
		if re.match("^[A-Za-z0-9_-]*$", page):

			# ROOT URL
			if not page or page == '_main':
				if not user or not skillshelves.do_we_know_this_guy(user):
					page = '_main'
				else:
					self.redirect('/_my_skillshelf')
		
			# USERPAGE
			elif page[0] != '_': # not in ['_404', '_main', '_login', '_loginform', '_register', '_logout', '_my_skillshelf', '_addbooks', '_managebooks']:
				template_values["whose_shelf"] = page
				page = 'userpage'		
		
			# BOOK
			elif page == '_book':
				template_values['bookid'] = self.request.get('b')
				
			# TAG
			elif page == '_tag':
				requestedtag = self.request.get('t')
				template_values['requestedtagdisplay'] = 'Skill Information'
				
				for item in tag_list:
					if item['tag'] == requestedtag:
						template_values['requestedtag'] = item['tag']
						template_values['requestedtagdisplay'] = item['display']
	
			# TAG LIST
			# nothing to be said here
			
			# REGISTER
			if page == '_register':
				if user and len(self.request.get('username')) > 2 and len(self.request.get('email')) > 6:
					theusername = self.request.get('username')
					# store user in database
					newuser = skillshelves.DBUsers()
					newuser.federated_identity = user.federated_identity()
					newuser.federated_provider = user.federated_provider()
					newuser.user_id = user.user_id()
					newuser.username = theusername
					newuser.email = self.request.get('email')
					newuser.put()
					# create users tag on fluidinfo
					skillshelves.connectToFluidinfo()
					result = fluidinfo.call('POST', '/tags/' + skillshelves.fluidinfoRootNamespace() + '/user', {'indexed': True, 'description': 'www.skillshelv.es uses this tag to show that the user ' + theusername + ' has this book on her Skillshelf', 'name': theusername})
					template_values["log_list"] = result
					page = '_addbooks'
				else:
					self.redirect('_login')
					
			# SELECT BOOKS
			if page == '_addbooks' or page == '_managebooks':
				if not user:
					self.redirect('_login')
				else:
					if page == '_addbooks':
						template_values["booklisttitle"] = 'fill your skillshelf'
						template_values["pagetitle"] = 'fill your skillshelf'
					else:
						template_values["booklisttitle"] = 'add/remove books'
						template_values["pagetitle"] = 'add/remove books'
						page = '_addbooks'
			
			# RANDOM SKILLSHELF
			if page == '_random':
				random.seed()
				userno = random.randint(0, skillshelves.get_user_count() - 1)
				query = skillshelves.DBUsers.all()
				dbresult = query.fetch(userno+1)
				# make sure it actually exists
				if len(dbresult)-1 < userno:
					userno = random.randint(0, len(dbresult)-1)
				self.redirect('/' + dbresult[userno].username)
				

			# LOGIN
			if page == '_login':
				if not user:
					page = '_loginform'	# it's not really a loginform, just links for logging in
				elif skillshelves.do_we_know_this_guy(user):
					self.redirect('_my_skillshelf')
				else:	# display the form that users see on first login
					suggestedusername = user.nickname()
					while not suggestedusername.isalnum() and not suggestedusername == '':
						suggestedusername = suggestedusername[0:len(suggestedusername)-2]
					template_values["suggestedusername"] = suggestedusername
					
			# MY SKILLSHELF
			if page == '_my_skillshelf' or page == '_my-skills':
				if not user:
					self.redirect('/_login')
				else:				
					template_values["whose_shelf"] = skillshelves.get_username(user)						
				

				
				
			# what if we figured out to show a page for which we don't actually have a template?
			# should never happen
			if not os.path.exists(page + '.html'):
				page = '_404'
		else:
			page = '_404'
 
		template_values["page"] = page
		template_values["page_filename"] = page + '.html'
 
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))
 
	def post(self, page):
		self.get(page)
 
class LoginRequired(webapp.RequestHandler):
	def get (self):
		self.response.out.write('Login Required')
 
application = webapp.WSGIApplication([('/_ah/login_required', LoginRequired),('/_ah/login', LoginRequired),('/(.*)', MainPage)],debug=True)
 
def main():
   run_wsgi_app(application)
 
if __name__ == "__main__":
   main()