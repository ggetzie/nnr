// functions for managing tags

for (untagForm of document.getElementsByClassName("untag-form")) {
    untagForm.addEventListener("submit", function (event) {
        event.preventDefault();
        untag(this);
    })
}

async function untag(untagForm) {
    const data = {
        "recipe": parseInt(untagForm["recipe"].value),
        "tag_slug": untagForm["tag_slug"].value
    }
        fetch(untagForm.action, {
        method: "post",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": untagForm["csrfmiddlewaretoken"].value,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(data)
    }).then(response => {
        return response.json();
    }).then(responseJSON => {
        if (responseJSON.error) {
            const res = createAlert(responseJSON.error, ["alert-danger"]);
            $(`#untag_${untagForm["tag_slug"].value}`).modal("hide");
        } else {
            console.log(responseJSON);
            console.log(responseJSON.message)
            const res = createAlert(responseJSON.message, ["alert-success"]);
            console.log(res)
            $(`#untag_${untagForm["tag_slug"].value}`).modal("hide");
            document.getElementById(`untag-container_${untagForm["tag_slug"].value}`).remove();
        }
        document.getElementById("tag-container").before(res);
    })
        
}