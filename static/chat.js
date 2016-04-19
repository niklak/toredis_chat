window.onload = function(){
    var socket = new SocketHandler();
    var form = document.getElementById('messageform');

    form.onsubmit = function(e){
        socket.send_message(form);
        return false;
    };
    form.onkeypress = function(e){
        if (e.keyCode == 13) {
            socket.send_message(form);
            return false;
        }
    };
    var inbox = document.getElementById('inbox');
    inbox.scrollTop = inbox.scrollHeight;
    document.getElementById('message').select();
};
/*
window.onbeforeunload = function(){
    socket.close();
};
*/

var SocketHandler = function() {
    var title = document.getElementById('channel').getAttribute('data-title');
    var url = "ws://" + location.host + "/chatsocket/" + title + '/';

    var sock = new WebSocket(url);
    var intervalId;
    sock.onopen = function(){
        intervalId = setInterval(function(){sock.send('{"dummy": 1}');}, 150000);
    };
    sock.onmessage = function(event) {
        var message = JSON.parse(event.data);
        var parent = document.getElementById(message.parent);
        if (message.parent == 'inbox'){
            parent.innerHTML += message.html;
            parent.scrollTop = parent.scrollHeight;

        }
        else{
            parent.innerHTML = message.html;
        }
    };
    sock.onclose = function(event){
        clearInterval(intervalId);
        console.log(event); // delete in production
        var ulist = document.getElementById('user_list');
        ulist.innerHTML = '<h4>Information unavailable</h4>';
        var error_span = document.getElementById('error');
        error_span.innerHTML = 'Sorry! Server has closed the connection!';
    };
    this.send_message = function(form){
        var elements = form.elements;
        var data = {};
        var i = 0;
        for (i; i < elements.length; i++){
            data[elements[i].name] = elements[i].value;
        }
        sock.send(JSON.stringify(data));
        var input = form.querySelector("input[type=text]");
        input.value = '';
        input.select();
    };
};