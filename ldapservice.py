import ldap
import ldap.modlist
from user import User
import os

class LdapService:
    con=None
    created_group = False
    def __init__(self):
        print "in ldapservice constructor"
        self.connect_ldap()
        print "done constructing"

    def connect_ldap(self):
        try: 
            print "INITIALIZING LDAP SERVER ...."
            self.con = ldap.initialize('ldap://ldap-server')
            self.con.protocol_version = ldap.VERSION3
            self.con.set_option(ldap.OPT_REFERRALS, 0)
            print "BINDING TO LDAP SERVER ...."
            # At this point, we're connected as an anonymous user
            # If we want to be associated to an account
            # you can log by binding your account details to your connection

            self.con.simple_bind_s("cn=Manager,dc=chat,dc=app", os.getenv('OPENLDAP_ROOT_PASSWORD'))
            print "LDAP Server Listening...."

            if not LdapService.created_group:
                print "gonna start creating group"
                fs_dn = 'dc=chat,dc=app'
                groupname = 'Users'

                attr = {}
                attr['objectClass'] = ['top','organizationalunit']
                #attr['groupType'] = '-2147483646'
                attr['ou'] = groupname
                #attr['name'] = groupname
                #attr['sAMAccountName'] = groupname

                ldif = ldap.modlist.addModlist(attr)
                print "fott l ldif"
                LdapService.created_group = True
                self.con.add_s(fs_dn,ldif)
                print "added group all good"
        except ldap.LDAPError, error_message:
            print "Couldn't Connect. %s " % error_message

    def add_user(self,user):
        print "ADDING USER"
        dn = "uid="+user.name+",ou=Users,dc=chat,dc=app"
        modlist = {
            "objectClass": ["inetOrgPerson","person"],
            "uid": user.name,
            "sn": user.surname,
            "givenName": user.name,
            "cn": user.name+" "+user.surname,
            "displayName": user.name+" "+user.surname,
            "userPassword": user.password,
            "description": user.card_number,
            "mail":user.email
            }
        #USE "strongAuthenticationUser" objectClass for Certification, it needs a binary file,
        # addModList transforms your dictionary into a list that is conform to ldap input.
        print "about to add user"
        try:
            print "self.con :"
            print str(self.con)
            result = self.con.add_s(dn, ldap.modlist.addModlist(modlist))
            print "User ADDED!"
            print "Result : "+str(result)
            self.con.unbind_s()
        except ldap.LDAPError, error_message:
            print "l error :"
            print str(ldap.LDAPError)
            print "Couldn't Connect. %s " % error_message

    def delete_user(self,uid):
        ########## deleting (a user) #################################################
        print "Deleting user "+uid
        dn = "uid="+uid+",ou=Users,dc=chat,dc=app"
        self.con.delete_s(dn)

    def search_user(self,uid):
        print "!!!!!!!!!Gonna Search for user"
        ldap_base = "ou=Users,dc=chat,dc=app"
        query = "(uid="+uid+")"
        print "query :"
        print str(query)
        try:
            print " gonna actually search"
            result = self.con.search_s(ldap_base, ldap.SCOPE_SUBTREE, query)
            print "done l9it resultat"
            print str(result)
            print "gonna start unbinding"
            self.con.unbind_s()
            print "Connection closed!"
            if result==[]:
                print "User not found"
                return None
            else:
                uid = result[0][1]['uid']
                lastname = result[0][1]['sn']
                name = result[0][1]['givenName']
                password = result[0][1]['userPassword']
                card_number = result[0][1]['description']
                email = result[0][1]['mail']
                user = User(uid, name, lastname, email, password, card_number, "")
                print "FOUND USER !"
                return user
        except ldap.LDAPError, error_message:
            print "l error :"
            print str(ldap.LDAPError)
            print "Couldn't Connect. %s " % error_message


