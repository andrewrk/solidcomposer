/* Time
 *
 * contains useful functions for displaying things and messing with
 * time.
 *
 * To use any of the functions that take serverTime (the most useful ones),
 * this class needs to have two global variables available.
 *
 * which should look like:
 *
 *      <script type="text/javascript">
 *          // as soon as possible in loading the html
 *          var server_time = new Date('{% now "F d, Y H:i:s" %}');
 *          var local_time = new Date();
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
                months -= Math.floor(years) * 12;
                return this.plural(Math.floor(years), "year", "years") + ", " +
                    this.plural(Math.floor(months), "month", "months");
            }

            if (months >= 1) {
                days -= Math.floor(months) * 30;
                return this.plural(Math.floor(months), "month", "months") + ", " +
                    this.plural(Math.floor(days), "day", "days");
            }

            if (weeks >= 1) {
                days -= Math.floor(weeks) * 7;
                return this.plural(Math.floor(weeks), "week", "weeks") + ", " +
                    this.plural(Math.floor(days), "day", "days");
            }

            if (days >= 1) {
                hours -= Math.floor(days) * 24;
                return this.plural(Math.floor(days), "day", "days") + ", " +
                    this.plural(Math.floor(hours), "hour", "hours");
            }

            if (hours >= 1) {
                minutes -= Math.floor(hours) * 60;
                return this.plural(Math.floor(hours), "hour", "hours") + ", " +
                    this.plural(Math.floor(minutes), "minute", "minutes");
            }

            if (minutes >= 1) {
                seconds -= Math.floor(minutes) * 60;
                return this.plural(Math.floor(minutes), "minute", "minutes") + ", " +
                    this.plural(Math.floor(seconds), "second", "seconds");
            }

            return this.plural(Math.floor(seconds), "second", "seconds");
        },

        plural: function (n, singular, plural) {
            return n + " " + ((n == 1) ? singular : plural);
        },

        // Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
        // 102 bytes, etc).
        fileSizeFormat: function (bytes, digits) {
            digits = digits || 1;

            try {
                bytes = parseFloat(bytes)
            } catch (err) {
                return "0 bytes"
            }

            if (bytes < 1024) {
                return that.plural(bytes, "byte", "bytes");
            } else if (bytes < 1024 * 1024) {
                return Math.round(bytes / 1024, digits) + " KB";
            } else if (bytes < 1024 * 1024 * 1024) {
                return Math.round(bytes / (1024 * 1024), digits) + " MB";
            } else {
                return Math.round(bytes / (1024 * 1024 * 1024), digits) + " GB";
            }
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
        },
        fromDjangoDate: function (django_date) {
            // 0123456789012345678
            // yyyy-mm-dd hh:mm:ss
            var year = parseInt(django_date.substring(0, 4));
            var month = parseInt(django_date.substring(5, 7)) - 1;
            var day = parseInt(django_date.substring(8, 10)) - 1;
            var hour = parseInt(django_date.substring(11, 13));
            var minute = parseInt(django_date.substring(14, 16));
            var second = parseInt(django_date.substring(17, 19));
            return new Date(year, month, day, hour, minute, second);
        },

        toDjangoDate: function (js_date) {
            // yyyy-mm-dd hh:mm:ss
            return js_date.getFullYear() + "-" + that.pad(js_date.getMonth() + 1) + "-" + that.pad(js_date.getDate() + 1) + " " +
                that.pad(js_date.getHours()) + ":" + that.pad(js_date.getMinutes()) + ":" + that.pad(js_date.getSeconds());
        }
    };
    return that;
} ();
$(document).ready(function(){
    Time.initialize(server_time, local_time);
});
