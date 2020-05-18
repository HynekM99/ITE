function on_loaded() {
    var address = "192.168.0.14";
    var port = "8881";
    var fullAddress = address+":"+port;

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
        var indic = "<div class=\"color_indicator\" id=\"color_indicator_"+team+"\" style=\"color:"+team+"\">"+teamStatusIndicators.offline+"</div>";
        var btnDiv = "<div class=\"btn_team_select\">"+btn+"</div>";
        selectionBtns += "<div class=\"selection\" id=\"selection_"+team+"\">"+indic+btnDiv+"</div>";
    }

    document.getElementById("team_select_menu").innerHTML = selectionBtns;
}

function setActiveButton() {
    document.getElementById(lastSelectedTeam).setAttribute("style", "");
    document.getElementById("selection_"+lastSelectedTeam).setAttribute("style", "");
    document.getElementById(selectedTeam).setAttribute("style", "background-color: rgb(73, 73, 73);");
    document.getElementById("selection_"+selectedTeam).setAttribute("style", "background-color: rgb(73, 73, 73);");
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
}

function onSocketMessage(evt) {
    console.log("WS client: Message received.");
    dataReceived = evt.data;
    console.log(dataReceived);
    if (dataReceived.substr(0, 10) == "statistics") {
        dataReceived = dataReceived.slice(11);
    
        var jsonObject = JSON.parse(dataReceived)

        for (var team in jsonData) {
            var dataAvailable = jsonObject.hasOwnProperty(team);
            if (dataAvailable)
                jsonData[team] = jsonObject[team];
            if (team == selectedTeam)
                updateAllStats();
        }
        setAllTeamStatuses();
    }
}

function onSocketClose() {
    console.log("WS client: Websocket closed.");
}