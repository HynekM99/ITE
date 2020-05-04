function on_loaded() {
    ws = new WebSocket("ws://localhost:8881/websocket")
    ws.onopen = onSocketOpen
    ws.onmessage = onSocketMessage
    ws.onclose = onSocketClose
}

function onSocketOpen() {
    console.log("WS client: Websocket openned.")
    document.getElementById("text_frame").innerHTML = "Websocket openned"
};

function onSocketMessage(evt) {
    console.log("WS message:", evt.data)
    document.getElementById("text_frame").innerHTML = "Last message from server: "+evt.data
};

function onSocketClose() {
    console.log("WS client: Websocket closed.")
    document.getElementById("text_frame").innerHTML = "Websocket closed"
}

function sendToServer() {
    ws.send("data")
}