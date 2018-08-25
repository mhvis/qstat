from ldap3 import Server

ldap_server = Server('somehost', 636, use_ssl=True)
ldap_binddn = 'cn=someone'
ldap_bindpass = 'pass'