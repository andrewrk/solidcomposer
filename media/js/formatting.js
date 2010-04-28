/* formatting.js
 *
 * contains useful functions for displaying things and messing with
 * time.
 *
 * depends on 2 global variables existing before this code loads
 * which should look like:
 *
 *      <script type="text/javascript">
 *          var server_time = new Date('{{ server_time }}');
 *          var local_time = new Date();
 *      </script>
 *
 */

// pads an integer with a zero if necessary and returns a string
function pad(num) {
    return ((num < 10) ? "0" : "") + num;
}

// takes milliseconds and returns a nice display like 0:00
function timeDisplay(ms) {
    var sec = ms / 1000;
    var min = sec / 60;
    var hr = min / 60;

    if (hr >= 1) {
        hr = Math.floor(hr);
        min = Math.floor(min - hr * 60);
        sec = Math.floor(sec - (hr * 60 + min) * 60);
        return hr + ":" + pad(min) + ":" + pad(sec);
    } else {
        min = Math.floor(min);
        sec = Math.floor(sec - min * 60);
        return min + ":" + pad(sec);
    }
}

// return how many minutes until a server time in a nice display format
function timeDisplayUntil(serverTime) {
    var local = localTime(serverTime);
    var now = new Date();
    return timeDisplay(local - now);
}

// return how many minutes since a server time in a nice display format
function timeDisplaySince(serverTime) {
    var local = localTime(serverTime);
    var now = new Date();
    return timeDisplay(now - local);
}

// make sure parameter is converted to a date
function coerceDate(date_or_string) {
    if (date_or_string instanceof Date)
        return date_or_string;
    else
        return new Date(date_or_string);
}

// pretty print a datetime
function formatDate(datetime) {
    return datetime.toString();
}

// convert a sever time to a local time
function localTime(_serverTime) {
    _serverTime = coerceDate(_serverTime);

    // find the difference between the local and the server time
    var diff = server_time - local_time;
    // apply the differece to the input _serverTime
    return new Date(_serverTime - diff);
}

// convert a local time to a server time
function serverTime(_localTime) {
    _localTime = coerceDate(_localTime);

    // find the difference between the local and the server time
    var diff = local_time - server_time;
    // apply the differece to the input _localTime
    return new Date(_localTime - diff);
}

// return in a nice printable string how much time until then
function printableTimeUntil(serverTime) {
    return printableTimeDiff(secondsUntil(serverTime));
}

function printableTimeSince(serverTime) {
    return printableTimeDiff(secondsSince(serverTime));
}

// display n amount of seconds in a format like
// x days, y hours, z minutes
function printableTimeDiff(seconds) {
    var minutes = seconds / 60;
    var hours = minutes / 60;
    var days = hours / 24;
    var weeks = days / 7;
    var months = days / 30;
    var years = days / 365;

    if (years >= 1)
        return plural(Math.ceil(years), "year", "years");

    if (months >= 1)
        return plural(Math.ceil(months), "month", "months");

    if (weeks >= 1)
        return plural(Math.ceil(weeks), "week", "weeks");

    if (days >= 1)
        return plural(Math.ceil(days), "day", "days");

    if (hours >= 1)
        return plural(Math.ceil(hours), "hour", "hours");

    if (minutes >= 1)
        return plural(Math.ceil(minutes), "minute", "minutes");

    return plural(Math.ceil(seconds), "second", "seconds");
}

function plural(n, singular, plural) {
    return n + " " + ((n == 1) ? singular : plural);
}

function secondsUntil(serverTime) {
    // convert to local time
    var local = localTime(serverTime);
    // get current time
    var current = new Date();
    // return the difference
    return (local - current)/1000;
}

function secondsSince(serverTime) {
    // convert to local time
    var local = localTime(serverTime);
    // get current time
    var current = new Date();
    // return the difference
    return (current - local)/1000;
}
