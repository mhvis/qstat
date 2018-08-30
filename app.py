from flask import Flask, render_template, request
from datetime import datetime
from ldap3 import Connection, SIMPLE, LEVEL, ALL_ATTRIBUTES
from config import ldap_server, ldap_binddn, ldap_bindpass
from statbuilder import StatBuilder

app = Flask(__name__)

stat_string = 'Refresh to get stats'
last_refresh = datetime.min


@app.route("/", methods=['GET', 'POST'])
def index():
    global last_refresh
    refreshed = ''
    if request.method == 'POST' and request.form.get('refresh'):
        if allow_refresh():
            refresh_stats()
            last_refresh = datetime.now()
            refreshed = 'ok'
        else:
            refreshed = 'toosoon'

    return render_template('index.html', refresh=refreshed, stat_string=stat_string)


def allow_refresh():
    return (datetime.now() - last_refresh).total_seconds() > 5 * 60


def refresh_stats():
    global stat_string
    conn = Connection(ldap_server, ldap_binddn, ldap_bindpass, authentication=SIMPLE, read_only=True,
                      raise_exceptions=True, auto_bind=True, check_names=True)
    # Fetch people
    conn.search('ou=People,dc=esmgquadrivium,dc=nl', '(objectClass=esmgqPerson)', LEVEL, attributes=ALL_ATTRIBUTES)
    people_dict = {entry['dn'].lower(): entry['attributes']
                   for entry in conn.response if entry['type'] == 'searchResEntry' }

    # Fetch groups
    conn.search('ou=Groups,dc=esmgquadrivium,dc=nl', '(objectClass=esmgqGroup)', LEVEL, attributes=ALL_ATTRIBUTES)
    groups_dict = {entry['dn'].lower(): entry['attributes']
                   for entry in conn.response if entry['type'] == 'searchResEntry'}

    stat_builder = StatBuilder(people_dict, groups_dict)
    stat_string = stat_builder.get_stat_string()