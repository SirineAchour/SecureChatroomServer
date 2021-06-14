import ldap
import ldap.modlist
from user import User
import os
#remove this later on
from ldap3 import Server, Connection, SUBTREE, LEVEL

class LdapService:
    con=None
    created_group = False
    def __init__(self):
        print("in ldapservice constructor")
        self.connect_ldap()
        print("done constructing")

    def connect_ldap(self):
        try: 
            print("INITIALIZING LDAP SERVER ....")
            self.con = ldap.initialize('ldap://ldap-server')
            self.con.protocol_version = ldap.VERSION3
            self.con.set_option(ldap.OPT_REFERRALS, 0)
            print("BINDING TO LDAP SERVER ....")
            # At this point, we're connected as an anonymous user
            # If we want to be associated to an account
            # you can log by binding your account details to your connection
            print("l password :")
            print(str(os.getenv('OPENLDAP_ROOT_PASSWORD')))
            self.con.simple_bind_s("cn=Manager,dc=chat,dc=app", os.getenv('OPENLDAP_ROOT_PASSWORD'))
            print("LDAP Server Listening....")
        except ldap.LDAPError:
            print("l error :")
            print(str(ldap.LDAPError))

    def add_user(self,user):
        print("ADDING USER")
        dn = "uid="+user.name+",ou=Users,dc=chat,dc=app"
        name_surname = user.name+" "+user.surname
        modlist = {
            "objectClass": [b"inetOrgPerson",b"person"],
            "uid": [user.name.encode('utf-8')],
            "sn": [user.surname.encode('utf-8')],
            "givenName": [user.name.encode('utf-8')],
            "cn": [name_surname.encode('utf-8')],
            "displayName": [name_surname.encode('utf-8')],
            "userPassword": [ user.password.encode('utf-8')],
            }
        #USE "strongAuthenticationUser" objectClass for Certification, it needs a binary file,
        # addModList transforms your dictionary into a list that is conform to ldap input.
        print("about to add user")
        try:
            print("self.con :")
            print(str(self.con))
            result = self.con.add_s(dn, ldap.modlist.addModlist(modlist))
            print("User ADDED!")
            print("Result : "+str(result))
            self.con.unbind_s()
        except ldap.LDAPError as e:
            print("l error :")
            print(str(e))

    def delete_user(self,uid):
        ########## deleting (a user) #################################################
        print("Deleting user "+uid)
        dn = "uid="+uid+",ou=Users,dc=chat,dc=app"
        self.con.delete_s(dn)

    def search_user(self,uid):
        print("!!!!!!!!!Gonna Search for user")
        ldap_base = "ou=Users,dc=chat,dc=app"
        query = "(uid="+uid+")"
        print("query :")
        print(str(query))
        try:
            print(" gonna actually search")
            result = self.con.search_s(ldap_base, ldap.SCOPE_SUBTREE, query)
            print("done l9it resultat")
            print(str(result))
            print("gonna start unbinding")
            self.con.unbind_s()
            print("Connection closed!")
            if result==[]:
                print("User not found")
                return None
            else:
                uid = result[0][1]['uid']
                lastname = result[0][1]['sn']
                name = result[0][1]['givenName']
                password = result[0][1]['userPassword']
                user = User(uid, name, lastname, password, "")
                print("FOUND USER !")
                return user
        except ldap.LDAPError:
            print("l error :")
            print(str(ldap.LDAPError))
            #print("Couldn't Connect. " + str(error_message))
    
    def list_users(self):
        ldap_base = "ou=Users,dc=chat,dc=app"
        res =self.con.search_s(ldap_base, ldap.SCOPE_SUBTREE,'(objectClass=person)')
        for dn, entry in res:
            print(dn)
        return res