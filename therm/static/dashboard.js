
//$(document).ready(function () {

//$(".up").on("click",function(e){
//    e.preventDefault();
//    $.ajax {
//        url: "/up"
//        type: "POST",
//        data: {}
//    }
//});


var setPtText = document.getElementById('set-pt-txt')
var tempText = document.getElementById('temp-txt')
var heatText = document.getElementById('heat-txt')


function setSetPoint (newSetPt) {
    setPtText.textContent = newSetPt.toFixed(1);
    $.post('setpt-set', { set_point: newSetPt },
        function(new_state){
            if (new_state.set_point_enabled) {
                setPtText.textContent = new_state.set_point.toFixed(1);
            } else {
                setPtText.textContent = "Off";
            }
            heatText.textContent = new_state.heat_on ? "On" : "Off";
            updateTemp();
        }
    );
};

function adjustSetPoint (cmd) {
    $.post(cmd, {},
        function(new_state){
            if (new_state.set_point_enabled) {
                setPtText.textContent = new_state.set_point.toFixed(1);
            } else {
                setPtText.textContent = "Off";
            }
            heatText.textContent = new_state.heat_on ? "On" : "Off";
            updateTemp();
        }
    );
}

function updateSetPoint () {
    $.get('/states/latest', {},
        function(new_state){
            if (new_state.set_point_enabled) {
                setPtText.textContent = new_state.set_point.toFixed(1);
            } else {
                setPtText.textContent = "Off";
            }
            heatText.textContent = new_state.heat_on ? "On" : "Off";
            updateTemp();
        }
    );
}

function updateTemp () {
    var request = new XMLHttpRequest();
    request.open('GET', '/samples/latest');
    request.onreadystatechange = function() {
        if(request.readyState === 4) {
            if(request.status === 200) {
                var new_sample = JSON.parse(request.responseText);
                tempText.textContent = new_sample.temp.toFixed(2);
            }
        }
   };
   request.send();
}
