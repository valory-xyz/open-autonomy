$(document).ready(function(){
    //connect to the socket server.
    const socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    let FSM_state_data_received = [];
    //receive details from server
    socket.on('new_data', function(msg) {
        console.log("Received FSM state data" + msg["period"]);
        //maintain a list of ten items
        if (FSM_state_data_received.length >= 10){
            FSM_state_data_received.shift()
        }
        FSM_state_data_received.push(msg["period"]);
        //convert to string for HTML display
        let state_data_string = '';
        let s;
        for (let i = 0; i < FSM_state_data_received.length; i++) {
            s = FSM_state_data_received[i].toString()
            state_data_string = state_data_string + '<p>' + s + '</p>';
        }
        $('#log').html(state_data_string);
    });
});