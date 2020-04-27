function on_loaded() {
    document.getElementById("text_frame").innerHTML = "Co musí řidič znát?";
    
    for (i = 0; i < parts.length; i++) {
        var img_part = document.createElement("img");
        img_part.id = "img_part_"+parts[i];
        img_part.setAttribute("class", "img_part");
        var style = "top: "+(img_parts_spacing * Math.floor(2*i/parts.length) + img_parts_start_top)+"px; ";
        style += "left: "+(img_parts_spacing * (i % Math.floor(parts.length/2)) + img_parts_start_left)+"px; ";
        img_part.style = style;
        img_part.src = "question_mark.jpg";
        document.body.appendChild(img_part);
    }
}

function check(element) {
    if (event.keyCode != 13 && element.id != "btn_check") return;

    var part = document.getElementById("textbox").value.toLowerCase();
    var text = "Špatně!";

    if (parts_input.length >= parts.length) {
        text = "Resetujte";
    }
    else if (parts_input.includes(part)) {
        text = "Již zadáno.";
    }
    else if (parts.includes(part)) {
        parts_input.push(part);
        document.getElementById("img_part_"+part).src = part+".jpg";

        if (parts_input.length < parts.length) {
            text = "Dobře!";
        }
        else {
            text = "Výborně, Ladislav je spokojen!";
            document.getElementById("img_lvodicka").src = "lvodicka_spokojen.jpg";
        }
    }
    
    document.getElementById("text_frame").innerHTML = text;
    document.getElementById("textbox").value = "";
}

function reset() {
    parts_input = [];
    document.getElementById("text_frame").innerHTML = "Co by měl řidič znát?";
    document.getElementById("img_lvodicka").src = "lvodicka_zmaten.jpg";
    for (i = 0; i < parts.length; i++) {
        document.getElementById("img_part_"+parts[i]).src = "question_mark.jpg";
    }
    document.getElementById("textbox").value = "";
}