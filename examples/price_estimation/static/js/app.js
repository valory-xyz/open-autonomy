$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var numbers_received = [];

    //receive details from server
    socket.on('new_data', function(msg) {
        console.log("Received number" + msg.period);
        //maintain a list of ten items
        if (numbers_received.length >= 10){
            numbers_received.shift()
        }
        numbers_received.push(msg.period);
        numbers_string = '';
        for (var i = 0; i < numbers_received.length; i++){
            n = numbers_received[i]["-1"]["0x_address_agent1"]["estimate"].toString()
            agent1 = numbers_received[i]["-1"]["0x_address_agent1"]
            numbers_string = numbers_string + '<p>'
            for (let k in agent1) {
                numbers_string = numbers_string + ' ' + k + ' ' + agent1[k].toString() + '</br>'
            }
            numbers_string = numbers_string + '</p>';

        }
        $('#log').html(numbers_string);
    });

});