
$(document).ready(function () {

//$(".up").on("click",function(e){
//    e.preventDefault();
//    $.ajax {
//        url: "/up"
//        type: "POST",
//        data: {}
//    }
//});
var down = document.getElementById('down');
var off = document.getElementById('off');
var up = document.getElementById('up');

var setPtText = document.getElementById('set-pt-txt')
var tempText = document.getElementById('temp-txt')
var heatText = document.getElementById('heat-txt')

function adjustSetPoint (cmd) {
    var request = new XMLHttpRequest();
    request.open('POST', cmd);
    request.onreadystatechange = function() {
        if(request.readyState === 4) {
            if(request.status === 200) {
                var new_setpt = JSON.parse(request.responseText);
                setPtText.textContent = new_setpt.set_point.toFixed(1);
            }
        }
   };
   request.send();
   updateTemp();
   updateHeat();
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


function updateHeat () {
    var request = new XMLHttpRequest();
    request.open('GET', '/states/latest');
    request.onreadystatechange = function() {
        if(request.readyState === 4) {
            if(request.status === 200) {
                var new_state = JSON.parse(request.responseText);
                heatText.textContent = new_state.heat_on ? "On" : "Off";
            }
        }
   };
   request.send();
}

down.addEventListener('click', function () {
    adjustSetPoint('setpt-down');
})

off.addEventListener('click', function () {
    adjustSetPoint('setpt-off');
})

up.addEventListener('click', function () {
    adjustSetPoint('setpt-up');
})


//down.addEventListener('click', function() {
//    var request = new XMLHttpRequest();
//    request.open('POST', 'setpt-down');
//    request.onreadystatechange = function() {
//        if(request.readyState === 4) {
//            if(request.status === 200) {
//                var new_setpt = JSON.parse(request.responseText);
////                $(".set-pt").textContent = new_setpt.set_point;
//                setPtText.textContent = new_setpt.set_point;
//            }
//        }
//   };
//
//    request.send();
//});


//$(".off").on("click",function(e){
//    e.preventDefault();
//    $.ajax {
//        url: "/off"
//        type: "POST",
//        data: {}
//    }
//});
});