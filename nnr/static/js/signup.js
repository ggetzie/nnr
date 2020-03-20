var stripe;
var checkoutSessionId;

var setupElements = function() {
    fetch("/public-key", {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
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

var createCheckoutSession = async function() {
    let form = document.getElementById("signup_form");
    let data = {};
    for (let i=0; i < form.length; i++) {
    if (form[i].type !== "submit") {
      data[form[i].name] = form[i].value
    }
  }
    fetch(form.action, {
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
        checkoutSessionId = data.checkoutSessionId;
      });
};


document.getElementById("signup_form").addEventListener("submit", function (event) {
  event.preventDefault();
  createCheckoutSession();
  stripe.redirectToCheckout({
      sessionId: checkoutSessionId
  }).then(function (result) {
      console.log("error redirecting to stripe");
      console.log(result)
  }).catch(function (err) {
      console.log(err);
  })
});