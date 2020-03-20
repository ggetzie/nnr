var stripe;
var checkoutSessionId;

var setupElements = function() {
    fetch("/main/public_key/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then(function(result) {
        return result.json();
      })
      .then(function(data) {
        stripe = Stripe(data.publicKey);
      });
  };

setupElements();

function createCheckoutSession() {
    let form = document.getElementById("signup_form");
    let data = {};
    for (let i=0; i < form.length; i++) {
        if (form[i].type !== "submit") {
            data[form[i].name] = form[i].value
        }
    }
    fetch("/main/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": data["csrfmiddlewaretoken"],
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: JSON.stringify(data)
    })
      .then(function(result) {
        return result.json();
      })
      .then(function(data) {
        stripe.redirectToCheckout({sessionId: data.checkoutSessionId
        }).then(function (result) {
            console.log("error redirecting to stripe");
            console.log(result);
        }).catch(function (err) {
            console.log(err)
        });
      });
};


document.getElementById("signup_form").addEventListener("submit", function (event) {
  event.preventDefault();
  console.log("form submission");
  createCheckoutSession();
});