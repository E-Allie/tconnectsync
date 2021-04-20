import time

from .process import process_time_range
from .secret import (
    PUMP_SERIAL_NUMBER,
    AUTOUPDATE_DEFAULT_SLEEP_SECONDS,
    AUTOUPDATE_MAX_SLEEP_SECONDS,
    AUTOUPDATE_USE_FIXED_SLEEP
)

"""
Performs the auto-update functionality. Runs indefinitely in a loop
until stopped (ctrl+c).
"""
def process_auto_update(tconnect, nightscout, time_start, time_end, pretend):
    # Read from android api, find exact interval to cut down on API calls
    # Refresh API token. If failure, die, have wrapper script re-run.

    last_event_index = None
    last_event_time = None
    time_diffs = []
    while True:
        last_event = tconnect.android.last_event_uploaded(PUMP_SERIAL_NUMBER)
        if not last_event_index or last_event['maxPumpEventIndex'] > last_event_index:
            now = time.time()
            print('New event index:', last_event['maxPumpEventIndex'], 'last:', last_event_index)

            if pretend:
                print('Would update now')
            else:
                added = process_time_range(tconnect, nightscout, time_start, time_end, pretend)
                print('Added', added, 'items')

            if last_event_index:
                time_diffs.append(now - last_event_time)
                print('Time diffs:', time_diffs)

            last_event_index = last_event['maxPumpEventIndex']
            last_event_time = now
        else:
            print('No event index change:', last_event['maxPumpEventIndex'])

            if len(time_diffs) > 2:
                print('Sleeping 60 seconds after unexpected no index change')
                time.sleep(60)
                continue

        sleep_secs = AUTOUPDATE_DEFAULT_SLEEP_SECONDS
        if AUTOUPDATE_USE_FIXED_SLEEP != 1:
            if len(time_diffs) > 10:
                time_diffs = time_diffs[1:]

            if len(time_diffs) > 2:
                sleep_secs = sum(time_diffs) / len(time_diffs)

            if sleep_secs > AUTOUPDATE_MAX_SLEEP_SECONDS:
                sleep_secs = AUTOUPDATE_MAX_SLEEP_SECONDS

        # Sleep for a rolling average of time between updates
        print('Sleeping for', sleep_secs, 'sec')
        time.sleep(sleep_secs)