function on_loaded() {
    var address = "localhost:8881";

    for (var key in teams) {
        jsonData[teams[key]] = null;
    }

    createButtons();
    setActiveButton();
    document.getElementById("header_img_link").setAttribute("href", "http://"+address)
    document.getElementById("header_txt_link").setAttribute("href", "http://"+address)
    ws = new WebSocket("ws://"+address+"/websocket");
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
        var btnDiv = "<div class=\"btn_team_select\">"+btn+"</div>"
        selectionBtns += "<div class=\"selection\" id=\"selection_"+team+"\">"+indic+btnDiv+"</div>";
    }

    document.getElementById("team_select_menu").innerHTML = selectionBtns;
}

function setActiveButton() {
    document.getElementById(lastSelectedTeam).setAttribute("style", "");
    document.getElementById(selectedTeam).setAttribute("style", "background-color: rgb(73, 73, 73);");
}

function setAllTeamStatuses() {
    for (var key in teams)
        setTeamStatus(teams[key], jsonData[teams[key]] !== null)
}

function setTeamStatus(team, status) {
    var indicator = status ? teamStatusIndicators.online : teamStatusIndicators.offline;
    document.getElementById("color_indicator_"+team).innerHTML = indicator;
}

function selectTeam(btnID) {
    lastSelectedTeam = selectedTeam;
    selectedTeam = btnID;
    setActiveButton();
    var dataAvailable = jsonData[selectedTeam] !== null;
    setTableStatus(dataAvailable)
    tableCreated = dataAvailable
}

function setTableStatus(visible) {
    if (visible) {
        setNoStatsAlert("");
        if (tableCreated)
            updateTable();
        else
            createTable();
    }
    else {
        setNoStatsAlert("Nejsou k dispozici data");
        document.getElementById("main_table").remove();
    }
}

function createTable() {
    addNewElementToExisting("table", "main_table", "stat_table")

    for (var key in headers) {
        addNewElementToExisting("tr", "tr_"+valueIndexes[key], "main_table");
        addNewElementToExisting("th", "th_"+valueIndexes[key], "tr_"+valueIndexes[key]);
        addNewElementToExisting("td", "td_"+valueIndexes[key], "tr_"+valueIndexes[key]);

        document.getElementById("th_"+valueIndexes[key]).innerHTML = headers[key];
        updateTableValue("td_"+valueIndexes[key], jsonData[selectedTeam][valueIndexes[key]])
        tableCreated = true;
    }
}

function addNewElementToExisting(newElement, newElementId, existingElementId) {
    var el = document.createElement(newElement);
    el.setAttribute("id", newElementId);
    document.getElementById(existingElementId).appendChild(el);
}

function updateTableValue(elementId, value) {
    document.getElementById(elementId).innerHTML = value;
    if (elementId != "cas" && value != "No data")
        document.getElementById(elementId).innerHTML += " °C";
}

function updateTable() {
    for (var key in headers) {
        updateTableValue("td_"+valueIndexes[key], jsonData[selectedTeam][valueIndexes[key]]);
    }
}

function setNoStatsAlert(message) {
    document.getElementById("no_stats_alert").innerHTML = message;
}

function getKeyFromTeams(string) {
    for (var key in teams) {
        if (teams[key] == string) return key;
    }
    return null;
}

function onSocketOpen() {
    console.log("WS client: Websocket openned.");
};

function onSocketMessage(evt) {
    console.log("WS client: Message received.");
    var jsonObject = JSON.parse(evt.data)

    for (var team in jsonData) {
        var dataAvailable = jsonObject.hasOwnProperty(team);
        if (dataAvailable)
            jsonData[team] = jsonObject[team];
        if (team == selectedTeam)
            setTableStatus(dataAvailable);            
    }
    setAllTeamStatuses();
};

function onSocketClose() {
    console.log("WS client: Websocket closed.");
}