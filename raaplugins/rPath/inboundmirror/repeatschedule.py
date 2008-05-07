#
# Copyright (C) 2006-2007 rPath, Inc.
# All rights reserved.
#

from turbogears import widgets

class MirrorScheduleWidget(widgets.Widget):
    template = '''
    <div xmlns:py="http://purl.org/kid/ns#">
    <script type="text/javascript">
function initSchedule()
{
    var checkFreq = "${value['checkFreq']}";
    var timeHour = "${value['timeHour']}";
    var timeDay = "${value['timeDay']}";
    var timeDayMonth = "${value['timeDayMonth']}";
    var hours = "${value['hours']}";

    var opts = getElementsByTagAndClassName("option", null, "checkFreq");
    for(var i in opts) {
        var opt = opts[i];
        opt.selected = (opt.value == checkFreq);
    }
    frequencyChange(checkFreq);

    var inputs = getElementsByTagAndClassName("input", null, "timeDayCont");
    for(var i in inputs) {
        var inp = inputs[i];
        inp.checked = (inp.value == timeDay);
    }

    var opts = getElementsByTagAndClassName("option", null, "timeHour");
    for(var i in opts) {
        var opt = opts[i];
        opt.selected = (opt.value == timeHour);
    }

    var opts = getElementsByTagAndClassName("option", null, "timeDayMonth");
    for(var i in opts) {
        var opt = opts[i];
        opt.selected = (opt.value == timeDayMonth);
    }

    getElement('hours').value = hours;
}

addLoadEvent(initSchedule);

function frequencyChange(freq) {
    if("Weekly" == freq) {
        showElement($("timeDayCont"));
        hideElement($("timeDayMonth"));
        showElement($("timeHour"));
        hideElement($("every"));
    } else if("Monthly" == freq) {
        hideElement($("timeDayCont"));
        showElement($("timeDayMonth"));
        showElement($("timeHour"));
        hideElement($("every"));
    } else if("Daily" == freq)   {
        hideElement($("timeDayCont"));
        hideElement($("timeDayMonth"));
        showElement($("timeHour"));
        hideElement($("every"));
    } else {
        hideElement($("timeDayCont"));
        hideElement($("timeDayMonth"));
        hideElement($("timeHour"));
        showElement($("every"));
    }
}

    </script>
    <select id="checkFreq" name="checkFreq" onchange="javascript:frequencyChange(this.value);">
      <option value="Hourly">Hourly</option>
      <option value="Daily">Daily</option>
      <option value="Weekly" selected="true">Weekly</option>
      <option value="Monthly">Monthly</option>
    </select>
    <span id="timeDayCont" name="timeDayCont">
        <input class="radio" type="radio" name="timeDay" value="0">Mon</input>
        <input class="radio" type="radio" name="timeDay" value="1">Tue</input>
        <input class="radio" type="radio" name="timeDay" value="2">Wed</input>
        <input class="radio" type="radio" name="timeDay" value="3">Thu</input>
        <input class="radio" type="radio" name="timeDay" value="4">Fri</input>
        <input class="radio" type="radio" name="timeDay" value="5">Sat</input>
        <input class="radio" type="radio" name="timeDay" value="6">Sun</input>
    </span>
    <span id="timeDayMonth">
        Day of the month:
        <select name="timeDayMonth">
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
            <option value="6">6</option>
            <option value="7">7</option>
            <option value="8">8</option>
            <option value="9">9</option>
            <option value="10">10</option>
            <option value="11">11</option>
            <option value="12">12</option>
            <option value="13">13</option>
            <option value="14">14</option>
            <option value="15">15</option>
            <option value="16">16</option>
            <option value="17">17</option>
            <option value="18">18</option>
            <option value="19">19</option>
            <option value="20">20</option>
            <option value="21">21</option>
            <option value="22">22</option>
            <option value="23">23</option>
            <option value="24">24</option>
            <option value="25">25</option>
            <option value="26">26</option>
            <option value="27">27</option>
            <option value="28">28</option>
        </select>
    </span>
    <span id="timeHour">
    At specific time:
    <select name="timeHour">
        <option value="0">12 AM</option>
        <option value="1">1 AM</option>
        <option value="2">2 AM</option>
        <option value="3">3 AM</option>
        <option value="4">4 AM</option>
        <option value="5">5 AM</option>
        <option value="6">6 AM</option>
        <option value="7">7 AM</option>
        <option value="8">8 AM</option>
        <option value="9">9 AM</option>
        <option value="10">10 AM</option>
        <option value="11">11 AM</option>
        <option value="12">12 PM</option>
        <option value="13">1 PM</option>
        <option value="14">2 PM</option>
        <option value="15">3 PM</option>
        <option value="16">4 PM</option>
        <option value="17">5 PM</option>
        <option value="18">6 PM</option>
        <option value="19">7 PM</option>
        <option value="20">8 PM</option>
        <option value="21">9 PM</option>
        <option value="22">10 PM</option>
        <option value="23">11 PM</option>
    </select>
    </span>
    <span id="every">
            Every <input id="hours" type="text" size="1" name="hours" /> hour(s)
    </span>
    </div>
'''
