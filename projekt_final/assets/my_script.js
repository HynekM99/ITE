function on_loaded() {
    var address = "147.228.121.62";
    var port = "8881";
    var fullAddress = address+":"+port;
    
    teams = {
        black: "black",
        blue: "blue",
        green: "green",
        orange: "orange",
        pink: "pink",
        red: "red",
        yellow: "yellow"
    };

    valueIndexes = {
        curTemp: "posledni",
        avgTemp: "prumerna",
        minTemp: "minimalni",
        maxTemp: "maximalni",
        time: "cas"
    };

    teamStatusIndicators = {
        offline: " ",
        online: "•"
    };

    selectedTeam = teams.black;
    lastSelectedTeam = selectedTeam;

    for (var key in teams) {
        jsonData[teams[key]] = {};
    }

    createButtons();
    setActiveButton();

    document.getElementById("header_img_link").setAttribute("href", "http://"+fullAddress);
    document.getElementById("header_txt_link").setAttribute("href", "http://"+fullAddress);

    ws = new WebSocket("ws://"+fullAddress+"/websocket");
    ws.onopen = onSocketOpen;
    ws.onmessage = onSocketMessage;
    ws.onclose = onSocketClose;
}

function createButtons() {
    var selectionBtns = "";

    for (var key in teams) {
        var team = teams[key];
        var capitalTeamName = team.charAt(0).toUpperCase() + team.slice(1);
        var btn = "<button class=\"btn_team_select_btn\" id=\""+team+"\" onclick=\"selectTeam(this.id)\">"+capitalTeamName+"</button>";
        var indic = "<div class=\"color_indicator\" id=\"color_indicator_"+team+"\">"+teamStatusIndicators.offline+"</div>";
        var btnDiv = "<div class=\"btn_team_select\">"+btn+"</div>";
        selectionBtns += "<div class=\"selection\" id=\"selection_"+team+"\">"+btnDiv+indic+"</div>";
    }

    document.getElementById("team_select_menu").innerHTML = selectionBtns;
}

function setActiveButton() {
    document.getElementById("selection_"+lastSelectedTeam).setAttribute("style", "");
    document.getElementById("selection_"+selectedTeam).setAttribute("style", "color: black; background-color: rgb(200, 200, 200);");
}

function setAllTeamStatuses() {
    for (var key in teams) {
        var state = jsonData[teams[key]] !== null && jsonData[teams[key]]["online"] == true;
        setTeamStatus(teams[key], state);
    }
}

function setTeamStatus(team, status) {
    var indicator = status ? teamStatusIndicators.online : teamStatusIndicators.offline;
    document.getElementById("color_indicator_"+team).innerHTML = indicator;
}

function selectTeam(btnID) {
    lastSelectedTeam = selectedTeam;
    selectedTeam = btnID;
    setActiveButton();
    updateAllStats();
}

function updateStat(stat, value) {
    elementId = "small_section_"+stat;
    if (stat == "cas") {
        document.getElementById(elementId).innerHTML = getFormattedTime(value);
    }
    else {
        document.getElementById(elementId).innerHTML = value;
        if (value != "No data")
            document.getElementById(elementId).innerHTML += " °C";
    }
}

function updateAllStats() {
    for (var key in valueIndexes) {
        stat = valueIndexes[key];
        value = jsonData[selectedTeam][valueIndexes[key]];
        if (value == null)
            value = "No data";
        updateStat(stat, value);
    }
}

function updateServerStatus(status) {
    document.getElementById("server_status").innerHTML = status ? "online" : "offline";
}

function getFormattedTime(time) {
    if (time == "No data") {
        return time;
    }
    var formatted = "";
    var dateTime =  time.split("T");
    var date = dateTime[0].split("-");
    var time = dateTime[1];

    formatted = time+"<br/>"+date[2]+"."+date[1]+"."+date[0];
    return formatted;
}

function onSocketOpen() {
    console.log("WS client: Websocket openned.");
    ws.send("request");
    setTimeout(() => {  ws.send("req_server"); }, 500);
}

function onSocketMessage(evt) {
    console.log("WS client: Message received.");
    dataReceived = evt.data;

    if (dataReceived.substr(0, 10) == "statistics") {
        dataReceived = dataReceived.slice(11);
    
        var jsonReceived = JSON.parse(dataReceived)

        for (var team in jsonData) {
            var dataAvailable = jsonReceived.hasOwnProperty(team);
            if (dataAvailable) {
                for (var key in jsonReceived[team]) {
                    jsonData[team][key] = jsonReceived[team][key]
                }
            }
            if (team == selectedTeam)
                updateAllStats();
        }
        setAllTeamStatuses();
    }
    else if (dataReceived.substr(0, 6) == "server") {
        dataReceived = dataReceived.slice(7);
        updateServerStatus(dataReceived == "true");
    }
}

function onSocketClose() {
    console.log("WS client: Websocket closed.");
}