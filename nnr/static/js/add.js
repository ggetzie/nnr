document.getElementById("id_ingredients_text").addEventListener("paste", function(event) {
    // remove leading spaces in ingredients lists when pasted from elsewhere
    event.stopPropagation();
    event.preventDefault();

    let data = event.clipboardData || window.clipboardData;

    let text = data.getData("text");

    for (line of text.split("\n")) {
        this.value += line.trim() + "  \n";
    }
})

document.getElementById("id_instructions_text").addEventListener("paste", function (event) {
    // remove leading spaces and number lines
    event.stopPropagation();
    event.preventDefault();

    let data = event.clipboardData || window.clipboardData;
    let text = data.getData("text");
    let i = 1;
    for (line of text.split("\n")) {
        if (line[0] === " ") {
            this.value += `${i}. ${line.trim()}  \n`;
            i += 1;
        } else {
            this.value += line + "\n";
        }
    }
})