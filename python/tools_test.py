import tools
import timeutils
from datetime import datetime

assert tools.parse_date("02/05/2025") == "20250502"
assert tools.parse_date("02-05-2025") == "20250502"
assert tools.parse_date("02 05 2025") == "20250502"
assert tools.parse_date("02 5 2025") == "20250502"
assert tools.parse_date("02-5-2025") == "20250502"
assert tools.parse_date("2-5-2025") == "20250502"
assert tools.parse_date("2 5 2025") == "20250502"
assert tools.parse_date("2-05-2025") == "20250502"
assert tools.parse_date("2 05 2025") == "20250502"
assert tools.parse_date("02-05-25") == "20250502"
assert tools.parse_date("2-5-25") == "20250502"
assert tools.parse_date("2 mai 25") == "20250502"
assert tools.parse_date("2 mai 2025") == "20250502"
assert tools.parse_date("2 may 25") == "20250502"

year = str(datetime.now().year)

assert tools.parse_date("31/12") == year + "1231"
assert tools.parse_date("31 12") == year + "1231"
assert tools.parse_date("31 déc.") == year + "1231"
assert tools.parse_date("31 déc") == year + "1231"
assert tools.parse_date("31 dec") == year + "1231"
assert tools.parse_date("31 décembre") == year + "1231"
assert tools.parse_date("1 janvier") == str(int(year) + 1) + "0101"


# print(tools.parse_date("Demain"))

assert tools.parse_time("12:51") == "1251"
assert tools.parse_time("12h51") == "1251"
assert tools.parse_time("12 h 51") == "1251"
assert tools.parse_time("12:51:09") == "1251"
assert tools.parse_time("12h 51") == "1251"
assert tools.parse_time("12 51") == "1251"
assert tools.parse_time("midi") == "1200"


assert tools.formatted_time_span_string("1200", "1300") == "de **12 h** à **13 h**"
assert tools.formatted_time_span_string("0700", "1251") == "de **7 h** à **12 h 51**"
assert tools.formatted_time_span_string("0000", "0900") == "jusqu’à **9 h**"
assert tools.formatted_time_span_string("0000", "2359") == "**toute la journée**"
assert tools.formatted_time_span_string("0446", "2359") == "à partir de **4 h 46**"

assert tools.formatted_hhmm("0900") == "9 h"
assert tools.formatted_hhmm("1200") == "midi"
assert tools.formatted_hhmm("1600") == "16 h"
assert tools.formatted_hhmm("0250") == "2 h 50"

#assert tools.date_to_string("20250405") == "le **05/04/2025**"

assert tools.parse_mail("tom.loisil@telecomnancy.net") == "Tom LOISIL"

assert tools.parse_duration("1") == 3600
assert tools.parse_duration("1h") == 3600
assert tools.parse_duration("1 h") == 3600
assert tools.parse_duration("1 h 30") == 5400
assert tools.parse_duration("1:30") == 5400
assert tools.parse_duration("1h30") == 5400
assert tools.parse_duration("30m") == 1800
assert tools.parse_duration("30 m") == 1800
assert tools.parse_duration("30 min") == 1800

assert tools.duration_to_string(1800) == "30 m"
assert tools.duration_to_string(3600) == "1 h"
assert tools.duration_to_string(5400) == "1 h 30 m"
