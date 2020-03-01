let addCommentForm = document.getElementById("addCommentForm");

addCommentForm.addEventListener('submit', function(event) {
    event.preventDefault();
    submitComment(this);
})

async function submitComment(commentForm) {
    let data = {
        "text": commentForm["text"].value,
        "recipe": commentForm["recipe"].value,
        "user": commentForm["user"].value,
    }

    fetch(commentForm.action, {
        method: "post",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": commentForm["csrfmiddlewaretoken"].value,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(data)
    }).then(response => {
        return response.json()
    }).then(responseJSON => {
        if (responseJSON.error) {
            ed = createErrorDiv(response.error.message)
            commentForm.parentNode.insertBefore(ed, commentForm);
        } else {
            // clear form
            commentForm["text"].value = "";

            // insert new comment at top of list
            let newComment = createComment(responseJSON.comment);
            let cl = document.getElementById("comment-list");
            cl.insertBefore(newComment, cl.children[0])
        }
    })
}

function createErrorDiv(msg) {
    let ed = document.createElement("div");
    ed.classList.add("alert", "alert-danger", "comment-error");
    ed.textContent = msg;
    let closeButton = document.createElement("button");
    closeButton.setAttribute("type", "button");
    closeButton.setAttribute("class", "close");
    closeButton.setAttribute("data-dismiss", "alert");
    closeButton.setAttribute("aria-label", "Close");
    let xSpan = document.createElement("span");
    xSpan.setAttribute("aria-hidden", "true");
    xSpan.innerHTML = "&times;"
    closeButton.appendChild(xSpan);
    ed.appendChild(closeButton);
    return ed;
}

function createComment(comment) {
    
    let commentDiv = document.createElement("div");
    commentDiv.id = comment.id;
    commentDiv.classList.add("comment");
    let commentHeader = createCommentHeader(comment);
    commentHeader.classList.add("comment-header")
    commentDiv.appendChild(commentHeader);

    let commentBody = document.createElement("div");
    commentBody.classList.add("comment-body");
    commentBody.innerHTML = comment.html;
    commentDiv.appendChild(commentBody);
    return commentDiv;

}

function createCommentHeader(comment) {
    let commentHeader = document.createElement("div");
    commentHeader.classList.add("text-muted", "comment-header");
    userSpan = document.createElement("span");
    userSpan.textContent = comment.user.username;
    userSpan.classList.add("comment-user");
    commentHeader.appendChild(userSpan);

    tsSpan = document.createElement("span");
    tsSpan.classList.add("comment-ts");
    tsSpan.textContent = comment.timestamp;
    commentHeader.appendChild(tsSpan);

    let currentUserId = Number(document.querySelector('meta[name="user_id"]')["content"]);
    if (currentUserId === Number(comment.user.id)) {
        let controls = document.createElement("div");
        controls.classList.add("dropdown", "float-right", "comment-control");
        dropdownButton = document.createElement("button");
        // dropdownButton.classList.add("btn", "btn-outline-secondary", "btn-sm", "dropdown-toggle", "comment-dropdown");
        dropdownButton.classList.add("btn", "btn-outline-secondary", "btn-sm", "comment-dropdown");
        dropdownButton.setAttribute("type", "button");
        // dropdownButton.innerHTML = "&#183;&#183;&#183;";
        dropdownButton.innerHTML = "&#8901;&#8901;&#8901;";
        let dd_id = `${comment.id}-dropdown`;
        dropdownButton.id = dd_id;
        dropdownButton.setAttribute("data-toggle", "dropdown");
        dropdownButton.setAttribute("aria-haspopup", "true");
        dropdownButton.setAttribute("aria-expanded", "false");
        controls.appendChild(dropdownButton);

        let dropdownMenu = document.createElement("div");
        dropdownMenu.classList.add("dropdown-menu");
        dropdownMenu.setAttribute("aria-labelledby", dd_id);
        controls.appendChild(dropdownMenu);


        let editLink = document.createElement("a");
        editLink.href = "#" + dd_id;
        editLink.classList.add("dropdown-item");
        editLink.textContent = "Edit";
        editLink.onclick = function () { editComment(comment.id) };
        dropdownMenu.appendChild(editLink);
        
        let deleteLink = document.createElement("a");
        deleteLink.href = "#" + dd_id;
        deleteLink.classList.add("dropdown-item");
        deleteLink.textContent = "Delete";
        deleteLink.onclick = function () { deleteComment(comment.id) };
        dropdownMenu.appendChild(deleteLink);

        commentHeader.appendChild(controls);

    }
    
    return commentHeader;
}

function deleteComment(commentId) {
    console.log(`Delete comment ${commentId}`);
}

function editComment(commentId) {
    console.log(`Edit comment ${commentId}`);
}

async function loadComments(startFrom = null) {
    // startFrom is a comment id. All comments fetched will have timestamps prior to
    // but not including startFrom. If null, will fetch the most recent comments
    let recipeId = document.querySelector('meta[name="recipe_id"]').content;
    let listUrl = `/comments/list/?recipe_id=${recipeId}`
    if (startFrom) {
        listUrl += `?start_from=${startFrom}`
    }
    fetch(listUrl, {
        method: "get",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
    }).then(response => {
        return response.json()
    }).then(responseJSON => {
        console.log(responseJSON);
        let cl = document.getElementById("comment-list");
        if (responseJSON.error) {
            ed = createErrorDiv(response.error);
            cl.appendChild(ed);
        } else {
            console.log(responseJSON.comment_list);
            for (let i=0; i < responseJSON.comment_list.length ; i++) {
                c = createComment(responseJSON.comment_list[i]);
                cl.appendChild(c);
            }
        }
    })
    
}

window.onload = loadComments();