/* time.js
 *
 * contains useful functions for displaying things and messing with
 * time.
 *
 * To use any of the functions that take serverTime (the most useful ones),
 * this class needs to be initialized like this:
 *
 * Time.initialize(server_time, local_time);
 *
 * which should look like:
 *
 *      <script type="text/javascript">
 *          // as soon as possible in loading the html
 *          var server_time = new Date('{{ server_time }}');
 *          var local_time = new Date();
 *
 *          // then later, when the document is ready
 *          Time.initialize(server_time, local_time);
 *      </script>
 *
 */

var Time = function () {
    // private variables
    var that;
    var month_names_full = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December'
    ];
    var server_time = new Date();
    var local_time = new Date();

    // private functions
    that = {
        // public variables

        // public methods
        // see top of this file
        initialize: function (init_server_time, init_local_time) {
            server_time = init_server_time;
            local_time = init_local_time;
        },

        // pads an integer with a zero if necessary and returns a string
        pad: function (num) {
            return ((num < 10) ? "0" : "") + num;
        },

        // display a server time prettily, discard date
        prettyTime: function (serverTime) {
            var local = this.localTime(serverTime);

            var hour = local.getHours();
            var min = this.pad(local.getMinutes());
            var sec = this.pad(local.getSeconds());

            var ampm = "am";
            if (hour > 12) {
                hour -= 12;
                ampm = "pm";
            }

            return hour + ":" + min + ":" + sec + " " + ampm;
        },

        // takes seconds and returns a nice display like 0:00
        timeDisplay: function (sec) {
            var min = sec / 60;
            var hr = min / 60;

            if (hr >= 1) {
                hr = Math.floor(hr);
                min = Math.floor(min - hr * 60);
                sec = Math.floor(sec - (hr * 60 + min) * 60);
                return hr + ":" + this.pad(min) + ":" + this.pad(sec);
            } else {
                min = Math.floor(min);
                sec = Math.floor(sec - min * 60);
                return min + ":" + this.pad(sec);
            }
        },

        // return how many minutes until a server time in a nice display format
        timeDisplayUntil: function (serverTime) {
            var local = this.localTime(serverTime);
            var now = new Date();
            return this.timeDisplay((local - now)/1000);
        },

        // return how many minutes since a server time in a nice display format
        timeDisplaySince: function (serverTime) {
            var local = this.localTime(serverTime);
            var now = new Date();
            return this.timeDisplay((now - local)/1000);
        },

        // make sure parameter is converted to a date
        coerceDate: function (date_or_string) {
            if (date_or_string instanceof Date) {
                return date_or_string;
            } else {
                return new Date(date_or_string);
            }
        },

        // pretty print only a date
        formatDate: function (theDate) {
            theDate = that.coerceDate(theDate);
            return month_names_full[theDate.getMonth()] + " " +
                theDate.getDate() + ", " +
                theDate.getFullYear();
        },

        // pretty print a datetime
        formatDateTime: function (datetime) {
            return this.formatDate(datetime) + " at " +
                datetime.toLocaleTimeString();
        },

        // convert a sever time to a local time
        localTime: function (serverTime) {
            var diff;
            
            serverTime = this.coerceDate(serverTime);

            // find the difference between the local and the server time
            diff = server_time - local_time;
            // apply the differece to the input serverTime
            return new Date(serverTime - diff);
        },

        // convert a local time to a server time
        serverTime: function (localTime) {
            var diff;
            localTime = this.coerceDate(localTime);

            // find the difference between the local and the server time
            diff = local_time - server_time;
            // apply the differece to the input localTime
            return new Date(localTime - diff);
        },

        // return in a nice printable string how much time until then
        printableTimeUntil: function (serverTime) {
            return this.printableTimeDiff(this.secondsUntil(serverTime));
        },

        printableTimeSince: function (serverTime) {
            return this.printableTimeDiff(this.secondsSince(serverTime));
        },

        // display n amount of seconds in a format like
        // x days, y hours, z minutes
        printableTimeDiff: function (seconds) {
            var minutes = seconds / 60;
            var hours = minutes / 60;
            var days = hours / 24;
            var weeks = days / 7;
            var months = days / 30;
            var years = days / 365;

            if (years >= 1) {
                return this.plural(Math.floor(years), "year", "years");
            }

            if (months >= 1) {
                return this.plural(Math.floor(months), "month", "months");
            }

            if (weeks >= 1) {
                return this.plural(Math.floor(weeks), "week", "weeks");
            }

            if (days >= 1) {
                return this.plural(Math.floor(days), "day", "days");
            }

            if (hours >= 1) {
                minutes -= Math.floor(hours) * 60;
                return this.plural(Math.floor(hours), "hour", "hours") + ", " +
                    this.plural(Math.floor(minutes), "minute", "minutes");
            }

            if (minutes >= 1) {
                return this.plural(Math.floor(minutes), "minute", "minutes");
            }

            return this.plural(Math.floor(seconds), "second", "seconds");
        },

        plural: function (n, singular, plural) {
            return n + " " + ((n == 1) ? singular : plural);
        },

        secondsUntil: function (serverTime) {
            // convert to local time
            var local = this.localTime(serverTime);
            // get current time
            var current = new Date();
            // return the difference
            return (local - current)/1000;
        },

        secondsSince: function (serverTime) {
            // convert to local time
            var local = this.localTime(serverTime);
            // get current time
            var current = new Date();
            // return the difference
            return (current - local)/1000;
        },

        isDifferentDay: function (date1, date2) {
            date1 = that.coerceDate(date1);
            date2 = that.coerceDate(date2);
            return date1.getYear() !== date2.getYear() ||
                   date1.getMonth() !== date2.getMonth() ||
                   date1.getDate() !== date2.getDate();
        }
    };
    return that;
} ();
