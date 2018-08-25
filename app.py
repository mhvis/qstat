from flask import Flask, render_template, request
from datetime import datetime, date
from ldap3 import Connection, SIMPLE, LEVEL, ALL_ATTRIBUTES
from config import ldap_server, ldap_binddn, ldap_bindpass
from collections import Counter

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
    conn.search('ou=People,dc=esmgquadrivium,dc=nl', '(memberOf=cn=Current members,ou=Groups,dc=esmgquadrivium,dc=nl)',
                LEVEL, attributes=ALL_ATTRIBUTES)
    current_member_dict = {entry['dn']: entry['attributes'] for entry in conn.response if entry['type'] == 'searchResEntry'}

    # Convert date of birth to Python datetime (in place)
    for member in current_member_dict.values():
        if not 'qDateOfBirth' in member:
            continue
        year = member['qDateOfBirth'] // 10000
        month = member['qDateOfBirth'] % 10000 // 100
        day = member['qDateOfBirth'] % 100
        member['qDateOfBirth'] = date(year, month, day)

    # Start new stat string
    new_stat_string = 'Live stats:\n'

    # Aantal leden
    new_stat_string += "We hebben nu " + str(len(current_member_dict)) + " leden.\n"

    # Volgende verjaardagen
    who = []
    delta = 10000
    today = date.today()
    for member in current_member_dict.values():
        if not 'qDateOfBirth' in member:
            continue
        dob = member['qDateOfBirth']
        birthday_in_next_year = dob.month < today.month or (dob.month == today.month and dob.day < today.day)
        birthday = date(today.year + 1 if birthday_in_next_year else today.year, dob.month, dob.day)
        bd_delta = (birthday - today).days
        if bd_delta < delta:
            who = [member['cn'][0]]
            delta = bd_delta
        elif bd_delta == delta:
            who.append(member['cn'][0])
    plural = len(who) > 1
    who_string = (" en ").join(who)
    if delta == 0:
        if plural:
            new_stat_string += who_string + " zijn vandaag jarig!\n"
        else:
            new_stat_string += who_string + " is vandaag jarig!\n"
    elif delta == 1:
        if plural:
            new_stat_string += who_string + " zijn morgen jarig!\n"
        else:
            new_stat_string += who_string + " is morgen jarig!\n"
    else:
        if plural:
            new_stat_string += who_string + " zijn over " + str(delta) + " dagen jarig!\n"
        else:
            new_stat_string += who_string + " is over " + str(delta) + " dagen jarig!\n"

    # Instrument/voice
    instrument_cnt = Counter()
    for member in current_member_dict.values():
        if not 'qInstrumentVoice' in member:
            continue
        for instrument in member['qInstrumentVoice']:
            instrument_cnt[instrument] += 1
    most_common = instrument_cnt.most_common(4)
    new_stat_string += "Er spelen/zingen bij ons " + str(most_common[0][1]) + " mensen " + most_common[0][0] + ", "
    new_stat_string += str(most_common[1][1]) + " mensen " + most_common[1][0] + ", "
    new_stat_string += str(most_common[2][1]) + " mensen " + most_common[2][0] + " en "
    new_stat_string += str(most_common[3][1]) + " mensen " + most_common[3][0] + ".\n"

    # English/Dutch
    english = 0
    dutch = 0
    for member in current_member_dict.values():
        if not 'preferredLanguage' in member:
            continue
        if member['preferredLanguage'].lower().startswith("nl"):
            dutch += 1
        if member['preferredLanguage'].lower().startswith("en"):
            english += 1
    new_stat_string += str(dutch) + " mensen spreken Nederlands, " + str(english) + " spreken Engels.\n"

    # Apply
    stat_string = new_stat_string
