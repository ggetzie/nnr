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