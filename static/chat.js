document.onready = function(){

    var socket = new SocketHandler();
    var form = document.getElementById('messageform');
    form.onsubmit = function(){
        socket.send_message(form);
        return false;
    };
    form.onkeypress = function(e){
        if (e.keyCode == 13) {
            socket.send_message(form);
            return false;
        }
    };
    inbox = document.getElementById('inbox');
    inbox.scrollTop = inbox.scrollHeight;
    document.getElementById('message').select();
};
/*
window.onbeforeunload = function(){
    socket.close();
};
*/

var SocketHandler = function() {
    var url = "ws://" + location.host + "/chatsocket/";
    var title = document.getElementById('channel').getAttribute('data-title');
    url += (title == 'main') ? '' : title + '/';

    var sock = new WebSocket(url);
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
}