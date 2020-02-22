function showMessage(messageText, messageClass) {
  let msg = document.createElement("div");
  msg.id = "messages"
  msg.classList.add("container", "alert");
  msg.classList.add(messageClass);
  msg.textContent = messageText;
  let closeButton = document.createElement("button");
  closeButton.setAttribute("type", "button");
  closeButton.setAttribute("class", "close");
  closeButton.setAttribute("data-dismiss", "alert");
  closeButton.setAttribute("aria-label", "Close");
  let xSpan = document.createElement("span");
  xSpan.setAttribute("aria-hidden", "true");
  xSpan.innerHTML = "&times;"
  closeButton.appendChild(xSpan);
  msg.appendChild(closeButton);
    
  let mainNav = document.getElementById("main-nav");
  mainNav.after(msg);
}

function toggle(id) {
  let elem = document.getElementById(id);
  if (elem.style.display === "none") {
	  elem.style.display = "initial";
  } else {
	  elem.style.display = "none";
  }
}