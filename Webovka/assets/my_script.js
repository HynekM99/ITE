function on_loaded() {
    createButtons();
    
    ws = new WebSocket("ws://localhost:8881/websocket");
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
        btns += "<div class=\"selection\"><div class=\"color_indicator\" style=\"color:"+team+"\">•</div><div class=\"btn_team_select\">"+btn+"</div></div>";
    }

    document.getElementById("team_select_menu").innerHTML = btns;
}

function selectTeam(btnID) {
    selectedTeam = btnID
    if (jsonData[selectedTeam] !== null) {
        if (tableCreated) {
            updateTable();
        }
        else {
            createTable();
        }
    }
    else {
        document.getElementById("team_stats").innerHTML = "Nejsou k dispozici data";
        tableCreated = false;
    }
}

function createTable() {
    var table = document.createElement("table");
    table.setAttribute("id", "mainTable");
    document.getElementById("team_stats").appendChild(table);

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
        tableCreated = true;
    }
}

function updateTable() {
    for (var key in headers) {
        document.getElementById("td_"+valueIndexes[key]).innerHTML = jsonData[selectedTeam][valueIndexes[key]];
    }
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
        }
    }
};

function onSocketClose() {
    console.log("WS client: Websocket closed.");
}