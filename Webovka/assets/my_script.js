function on_loaded() {
    var address = "localhost:8881";

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
    var btns = "";

    for (var key in teams) {
        var team = teams[key];
        var capitalTeamName = team.charAt(0).toUpperCase() + team.slice(1);
        var btn = "<button class=\"btn_team_select\" id=\""+team+"\" onclick=\"selectTeam(this.id)\">"+capitalTeamName+"</button>";
        btns += "<div class=\"selection\" id=\"selection_"+team+"\"><div class=\"color_indicator\" id=\"color_indicator_"+team+"\" style=\"color:"+team+"\">"+teamStatusIndicators.offline+"</div><div class=\"btn_team_select\">"+btn+"</div></div>";
    }

    document.getElementById("team_select_menu").innerHTML = btns;
}

function setActiveButton() {
    document.getElementById(lastSelectedTeam).setAttribute("style", "");
    document.getElementById(selectedTeam).setAttribute("style", "background-color: rgb(73, 73, 73);");
}

function setAllTeamStatuses() {
    for (var key in teams) {
        setTeamStatus(teams[key], jsonData[teams[key]] !== null)
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

    if (jsonData[selectedTeam] !== null) {
        if (tableCreated) {
            updateTable();
        }
        else {
            createTable();
        }
        setNoStatsAlert("");
    }
    else {
        setNoStatsAlert("Nejsou k dispozici data");
        document.getElementById("mainTable").remove();
        tableCreated = false;
    }
}

function createTable() {
    var table = document.createElement("table");
    table.setAttribute("id", "mainTable");
    document.getElementById("stat_table").appendChild(table);

    for (var key in headers) {
        var tr = document.createElement("tr");
        var th = document.createElement("th");
        var td = document.createElement("td");
        tr.setAttribute("id", "tr_"+valueIndexes[key]);
        th.setAttribute("id", "th_"+valueIndexes[key]);
        td.setAttribute("id", "td_"+valueIndexes[key]);

        document.getElementById("mainTable").appendChild(tr);
        
        document.getElementById("tr_"+valueIndexes[key]).appendChild(th);
        document.getElementById("tr_"+valueIndexes[key]).appendChild(td);

        document.getElementById("th_"+valueIndexes[key]).innerHTML = headers[key];
        document.getElementById("td_"+valueIndexes[key]).innerHTML = jsonData[selectedTeam][valueIndexes[key]];
        if (valueIndexes[key] != "cas") {
            document.getElementById("td_"+valueIndexes[key]).innerHTML += " °C";
        }
        tableCreated = true;
        setAllTeamStatuses();
    }
}

function updateTable() {
    for (var key in headers) {
        document.getElementById("td_"+valueIndexes[key]).innerHTML = jsonData[selectedTeam][valueIndexes[key]];
        if (valueIndexes[key] != "cas") {
            document.getElementById("td_"+valueIndexes[key]).innerHTML += " °C";
        }
    }
    setAllTeamStatuses();
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
        if (jsonObject.hasOwnProperty(team)) {
            jsonData[team] = jsonObject[team];
            if (!tableCreated) {
                createTable();
            }
            else {
                updateTable();
            }
            setNoStatsAlert("");
        }
        else {
            setNoStatsAlert("Nejsou k dispozici data");
        }
    }
};

function onSocketClose() {
    console.log("WS client: Websocket closed.");
}