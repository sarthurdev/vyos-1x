# Copyright 2020-2022 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import re

def format_task(minute="*", hour="*", day="*", dayofweek="*", month="*", user="root", spec=None, command=""):
    if spec:
        return f'{spec} {user} {command}\n'
    return f'{minute} {hour} {day} {month} {dayofweek} {user} {command}\n'

def split_interval(s):
    result = re.search(r"(\d+)([mdh]?)", s)
    value = int(result.group(1))
    suffix = result.group(2)
    return ( (value, suffix) )

def format_crontab_line(command, spec=None, interval=None):
    if spec:
        return format_task(spec=spec, command=command)

    value, suffix = split_interval(interval)
    if not suffix or suffix == "m":
        return format_task(command=command, minute=f'*/{value}')
    elif suffix == "h":
        return format_task(command=command, minute="0", hour=f'*/{value}')
    elif suffix == "d":
        return format_task(command=command, minute="0", hour="0", day=f'*/{value}')

    return None
