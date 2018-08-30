from datetime import date
from collections import Counter


class StatBuilder:
    def __init__(self, people, groups):
        """Expects a people and group dictionary in the format 'dn: attributes'."""
        current_members_dn = 'cn=Huidige leden,ou=Groups,dc=esmgquadrivium,dc=nl'
        self.people = people
        self.groups = groups
        # Add isMember attribute to people
        for person in self.people.values():
            person['isMember'] = 'memberOf' in person and current_members_dn in person['memberOf']

        # Convert date of birth to Python datetime (in place)
        for person in people.values():
            if not 'qDateOfBirth' in person:
                continue
            year = person['qDateOfBirth'] // 10000
            month = person['qDateOfBirth'] % 10000 // 100
            day = person['qDateOfBirth'] % 100
            person['qDateOfBirth'] = date(year, month, day)

        # Construct members only dictionary
        self.members = {k: v for (k, v) in people.items() if v['isMember']}

    def _next_birthdays_string(self):
        """Upcoming birthday(s) string."""
        who = []
        delta = 10000
        today = date.today()
        for member in self.members.values():
            if not 'qDateOfBirth' in member:
                continue
            dob = member['qDateOfBirth']
            birthday_in_next_year = dob.month < today.month or (dob.month == today.month and dob.day < today.day)
            birthday = date(today.year + 1 if birthday_in_next_year else today.year, dob.month, dob.day)
            bd_delta = (birthday - today).days
            if bd_delta < delta:
                who = [member['givenName'][0]]
                delta = bd_delta
            elif bd_delta == delta:
                who.append(member['givenName'][0])
        plural = len(who) > 1
        who_string = (" en ").join(who)
        if delta == 0:
            if plural:
                return who_string + " zijn vandaag jarig!\n"
            else:
                return who_string + " is vandaag jarig!\n"
        elif delta == 1:
            if plural:
                return who_string + " zijn morgen jarig!\n"
            else:
                return who_string + " is morgen jarig!\n"
        else:
            if plural:
                return who_string + " zijn over " + str(delta) + " dagen jarig!\n"
            else:
                return who_string + " is over " + str(delta) + " dagen jarig!\n"

    def _instrument_voice_string(self):
        """Find top 4 played/sung instruments"""
        instrument_cnt = Counter()
        for member in self.members.values():
            if not 'qInstrumentVoice' in member:
                continue
            for instrument in member['qInstrumentVoice']:
                instrument_cnt[instrument] += 1
        most_common = instrument_cnt.most_common(4)

        s = "Er spelen/zingen bij ons " + str(most_common[0][1]) + " mensen " + most_common[0][0] + ", "
        s += str(most_common[1][1]) + " mensen " + most_common[1][0] + ", "
        s += str(most_common[2][1]) + " mensen " + most_common[2][0] + " en "
        s += str(most_common[3][1]) + " mensen " + most_common[3][0] + ".\n"
        return s

    def _preferred_language_string(self):
        """Number of English and Dutch speaking people."""
        english = 0
        dutch = 0
        for member in self.members.values():
            if not 'preferredLanguage' in member:
                continue
            if member['preferredLanguage'].lower().startswith("nl"):
                dutch += 1
            if member['preferredLanguage'].lower().startswith("en"):
                english += 1
        return str(dutch) + " mensen spreken Nederlands, " + str(english) + " spreken Engels.\n"

    def _get_name(self, person_dn):
        person = self.people[person_dn.lower()]
        if 'givenName' not in person:
            name = person['cn'][0]
        else:
                name = person['givenName'][0]
        if not person['isMember']:
            name += " (geen lid)"
        return name

    def _group_summary_string(self):
        """Group summary."""
        exclude_groups = {'Huidige leden', 'Archivarissen', 'Secretaris', 'Penningmeester', 'Voorzitter',
                          'Violin players'}

        summary = "Groepjesoverzicht (uit database, gelinkt aan maillijst):\n"
        for group in self.groups.values():
            if group['cn'][0] in exclude_groups or 'member' not in group:
                continue

            group_name = group['cn'][0]
            group_members = [self._get_name(member_dn) for member_dn in group['member']]
            summary += "- " + group_name + ": "
            if len(group_members) > 1:
                summary += ", ".join(group_members[1:]) + " en "
            summary += group_members[0] + "\n"
        return summary

    def get_stat_string(self):
        # Start new stat string
        s = 'Live random stats (gegenereerd uit de database):\n'

        # Aantal leden
        s += "We hebben nu " + str(len(self.members)) + " leden.\n"

        # Birthdays
        s += self._next_birthdays_string()

        # Instrument/voice
        s += self._instrument_voice_string()

        # English/Dutch
        s += self._preferred_language_string()

        # Group summary
        s += "\n"
        s += self._group_summary_string()

        return s
