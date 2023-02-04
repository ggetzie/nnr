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
            document.getElementById("tag-container").before(res);
        } else {
            const res = createAlert(responseJSON.message, ["alert-success"]);
            $(`#untag_${untagForm["tag_slug"].value}`).modal("hide");
            document.getElementById("tag-container").before(res);
            document.getElementById(`untag-container_${untagForm["tag_slug"].value}`).remove();
        }
    })
}

get_all_tags();

async function get_all_tags() {
    fetch("/tags/all/", {
        method: "get",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }
    }).then(response => {
        return response.json();
    }).then(responseJSON => {
        if (responseJSON.error) {
            const res = createAlert(responseJSON.error, ["alert-danger"]);
            document.getElementById("id_tags").before(res);
        } else {
            tag_list = responseJSON.tag_list;
            autocomplete(document.getElementById("id_tags"), responseJSON.tag_list);
        }
    })
}

function search_for_autocomplete(term, options) {
    // options is an array of strings, term is a string
    // find all items in list that contain term
    // sort by occurrence of term in item
    // (items where term occurs earlier are first)
    res = options.filter(s => s.toLowerCase().search(term.toLowerCase()) > -1)
                 .sort(s => s.toLowerCase().search(term.toLowerCase()))
    return res
}

function autocomplete(inp, arr) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val;
        // only look for the last value in a comma separated list
        lastComma = this.value.lastIndexOf(",");
        if (lastComma > -1) {
            val = this.value.slice(lastComma+1).trim()
        } else {
            val = this.value
        }
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) { return false;}
        currentFocus = -1;
        let matches = search_for_autocomplete(val, arr);
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        // Display each match below the input field
        matches.map(m => {
            b = document.createElement("div");
            // highlight occurrences of val in match, but retain case of match
            let sub = new RegExp(val, "gi");
            res = m.replace(sub, (x) => (`<strong>${x}</strong>`))
            b.innerHTML = res;
            b.innerHTML += `<input type='hidden' value='${m}'>`;
            b.addEventListener("click", function (e) {
                // add match to the input when clicked
                selected = this.getElementsByTagName("input")[0].value
                lastComma = inp.value.lastIndexOf(",");
                if (lastComma === -1) {
                    inp.value = selected;
                } else {
                    inp.value = inp.value.slice(0, lastComma) + `, ${selected}`;
                }
                closeAllLists();
            })
            a.appendChild(b);
        })
        // automatically select the first choice
        x = document.getElementById(this.id + "autocomplete-list");
        if (x) {
            ac_list = x.getElementsByTagName("div")
            currentFocus = 0;
            addActive(ac_list);
        }
    });

    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode === 40) {
          /*If the arrow DOWN key is pressed,
          increase the currentFocus variable:*/
          currentFocus++;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode === 38) { //up
          /*If the arrow UP key is pressed,
          decrease the currentFocus variable:*/
          currentFocus--;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode === 13 || e.keyCode === 9) {
          /*If the ENTER or TAB key is pressed, prevent the form from being submitted,*/
          e.preventDefault();
          if (currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (x) x[currentFocus].click();
          }
        } else if (e.keyCode === 188) {
            // reset search on comma
            closeAllLists();
        }
    });
    function addActive(x) {
      /*a function to classify an item as "active":*/
      if (!x) return false;
      /*start by removing the "active" class on all items:*/
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      /*add class "autocomplete-active":*/
      x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
      /*a function to remove the "active" class from all autocomplete items:*/
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }
    function closeAllLists(elmnt) {
      /*close all autocomplete lists in the document,
      except the one passed as an argument:*/
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }
  /*Close all lists when someone clicks in the document:*/
  document.addEventListener("click", function (e) {
      closeAllLists(e.target);
  });
  } 

  