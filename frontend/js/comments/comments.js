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
            let ed = createErrorDiv(responseJSON.error);
            commentForm.before(ed);
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
    let ed = createAlert(msg, ["alert-danger"])
    return ed;
}

function createComment(comment) {
    // build up div for a comment with info from comment JSON
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

    let commentEdit = editModal(comment);
    commentDiv.appendChild(commentEdit);

    let commentDelete = deleteModal(comment.id);
    commentDiv.appendChild(commentDelete);
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
        dropdownButton.classList.add("btn", "btn-outline-secondary", "btn-sm", "comment-dropdown");
        dropdownButton.setAttribute("type", "button");
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


        let editButton = document.createElement("button");
        editButton.classList.add("dropdown-item");
        editButton.setAttribute("data-toggle", "modal");
        editButton.setAttribute("data-target", `#edit-${comment.id}-modal`);
        editButton.textContent = "Edit";
        dropdownMenu.appendChild(editButton);
        
        let deleteButton = document.createElement("button");
        deleteButton.classList.add("dropdown-item");
        deleteButton.setAttribute("data-toggle", "modal");
        deleteButton.setAttribute("data-target", `#delete-${comment.id}-modal`);
        deleteButton.textContent = "Delete";
        dropdownMenu.appendChild(deleteButton);

        commentHeader.appendChild(controls);

    }
    
    return commentHeader;
}

function editModal(comment) {
    let form = document.createElement("form");
    form.action = "/comments/edit/";
    form.method = "post";
    form.id = `edit-${comment.id}`;
    form.classList.add("comment-form");
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        editComment(form);
    })

    let cid = document.createElement("input");
    cid.type = "hidden";
    cid.value = comment.id;
    cid.name = "id";

    form.appendChild(cid);

    let text = document.createElement("textarea");
    text.value = comment.text;
    text.classList.add("textarea", "form-control");
    text.setAttribute("cols", 40);
    text.setAttribute("rows", 5);
    text.setAttribute("required", "");
    text.name = "text";

    let fg = document.createElement("div");
    fg.classList.add("form-group");
    fg.appendChild(text);

    form.appendChild(fg)

    let cancel = document.createElement("button");
    cancel.classList.add("btn", "btn-secondary");
    cancel.setAttribute("data-dismiss", "modal");
    cancel.textContent = "Cancel";

    let submit = document.createElement("input");
    submit.type = "submit";
    submit.value = "Submit";
    submit.classList.add("btn", "btn-primary");

    let fc = document.createElement("div");
    fc.classList.add("form-actions");
    fc.appendChild(cancel);
    fc.appendChild(submit);

    form.appendChild(fc);

    modal = Modal(`edit-${comment.id}-modal`, 
                  "Edit Comment",
                  form);

    return modal;

}

function deleteModal(commentId) {
    let bodyP = document.createElement("p");
    bodyP.textContent = "Comment will be deleted. Are you sure?";
    let modalBody = document.createElement("div");
    modalBody.appendChild(bodyP);

    let deleteForm = document.createElement("form");
    deleteForm.id = `delete-${commentId}`;
    deleteForm.action = "/comments/delete/";
    deleteForm.method = "post";
    deleteForm.addEventListener("submit", function (event) {
        event.preventDefault();
        deleteComment(deleteForm);
    })

    let id = document.createElement("input");
    id.name = "id"
    id.value = commentId
    id.type = "hidden"
    deleteForm.appendChild(id)

    let fa = document.createElement("div");
    fa.classList.add("form-actions");
    deleteForm.appendChild(fa)

    let no = document.createElement("button");
    no.textContent = "No";
    no.setAttribute("data-dismiss", "modal");
    no.classList.add("btn", "btn-secondary");
    fa.appendChild(no);

    let yes = document.createElement("input");
    yes.textContent = "Yes";
    yes.type = "submit";
    yes.value = "Yes";
    yes.classList.add("btn", "btn-danger")
    fa.appendChild(yes);

    modalBody.appendChild(deleteForm);

    return Modal(`delete-${commentId}-modal`,
                 "Delete Comment", 
                 modalBody)

}

function Modal(modalId, headerText, bodyElement, footerElement = null) {
    let modal = document.createElement("div");
    modal.id = modalId;
    modal.classList.add("modal");
    modal.setAttribute("tabindex", "-1");
    modal.setAttribute("role", "dialog");
    let titleId = `${modalId}-title`;
    modal.setAttribute("aria-labelledby", titleId);
    modal.setAttribute("aria-hidden", "true");

    let dialog = document.createElement("div");
    dialog.classList.add("modal-dialog", "modal-dialog-centered");
    dialog.setAttribute("role", "document");

    modal.appendChild(dialog);

    let content = document.createElement("div");
    content.classList.add("modal-content")
    dialog.appendChild(content);

    let header = document.createElement("div");
    header.classList.add("modal-header");

    let h5 = document.createElement("h5");
    h5.classList.add("modal-title");
    h5.textContent = headerText;
    header.appendChild(h5);
    header.appendChild(closeModal());
    
    content.appendChild(header);

    let body = document.createElement("div");
    body.classList.add("modal-body");
    body.appendChild(bodyElement);
    content.appendChild(body);

    if (footerElement) {
        let footer = document.createElement("div");
        footer.classList.add("modal-footer");
        footer.appendChild(footerElement);
        content.appendChild(footer);
    }
    
    return modal;

}

function closeModal() {
    let cb = document.createElement("button");
    cb.setAttribute("type", "button");
    cb.classList.add("close");
    cb.setAttribute("data-dismiss", "modal");
    cb.setAttribute("aria-label", "Close");

    let xSpan = document.createElement("span");
    xSpan.setAttribute("aria-hidden", "true");
    xSpan.innerHTML = "&times;"

    cb.appendChild(xSpan);
    return cb;
}

async function deleteComment(deleteForm) {
    let data = {"id": deleteForm["id"].value}
    let csrftoken = document.querySelector('#comment-list input[name="csrfmiddlewaretoken"]').value;

    fetch(deleteForm.action, {
        method: "post",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(data)
    }).then(response => {
        return response.json();
    }).then(responseJSON => {
        let deleted = document.getElementById(data["id"]);
        let c = document.querySelector(`#delete-${deleteForm["id"].value}-modal button.close`);
        c.click()        
        if (responseJSON.error) {
            ed = createErrorDiv(responseJSON.error);
            deleted.before(ed);
        } else {
            let msg = createAlert("Comment Deleted.", ["alert-success"]);
            deleted.before(msg);
            deleted.remove();
        }
    })
}

async function editComment(editForm) {
    let data = {"id": editForm["id"].value,
                "text": editForm["text"].value}
    let csrftoken = document.querySelector('#comment-list input[name="csrfmiddlewaretoken"]').value;
    
    fetch(editForm.action, {
        method: "post",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(data)
    }).then(response => {
        return response.json()
    }).then( responseJSON => {
        if (responseJSON.error) {
            ed = createErrorDiv(response.error.message);
            editForm.before(ed);
        } else {
            // comment successfully updated. 
            // Close the model and replace the comment with the updated version
            let c = document.querySelector(`#edit-${editForm["id"].value}-modal button.close`);
            c.click()
            updateComment(responseJSON.comment);
        }
    })

}

async function loadComments(startFrom = null, max_comments=25) {
    // startFrom is a comment id. All comments fetched will have timestamps prior to
    // but not including startFrom. If null, will fetch the most recent comments
    let recipeId = document.querySelector('meta[name="recipe_id"]').content;
    let listUrl = `/comments/list/?recipe_id=${recipeId}&max_comments=${max_comments}`
    if (startFrom) {
        listUrl += `&start_from=${startFrom}`
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
        let cl = document.getElementById("comment-list");
        let oldB = document.getElementById("loadMoreButton");
        if (oldB) {
            oldB.remove()
        }        
        if (responseJSON.error) {
            let ed = createErrorDiv(response.error);
            cl.appendChild(ed);
        } else {
            for (let i=0; i < responseJSON.comment_list.length ; i++) {
                let c = createComment(responseJSON.comment_list[i]);
                cl.appendChild(c);
                if ((i === responseJSON.comment_list.length - 1) && responseJSON.has_more) {
                    let lb = loadMoreButton(c);
                    cl.appendChild(lb);
                }
            }
        }
    })
    
}

function loadMoreButton(comment) {
    
    let b = document.createElement("button");
    b.id = "loadMoreButton"
    b.classList.add("btn", "btn-primary");
    b.textContent = "Load more comments";
    b.addEventListener("click", function () {
        loadComments(startFrom=comment.id);
    })
    return b;
}

function updateComment(newComment) {
    let oldCommentDiv = document.getElementById(newComment.id);
    oldCommentDiv.id += "-old";
    let newCommentDiv = createComment(newComment);
    oldCommentDiv.before(newCommentDiv);
    oldCommentDiv.remove()
}

window.onload = loadComments();

