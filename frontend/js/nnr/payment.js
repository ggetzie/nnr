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

var createCheckoutSession = function(plan) {
    if (!plan) {
      ad = createAlert("Please select a plan to continue.", ["alert-danger"]);
      document.getElementById("payment_plan_form").before(ad);
      return
    }
    fetch(`/main/create-checkout-session/?plan=${plan}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
    })
      .then(function(result) {
        return result.json();
      })
      .then(function(data) {
        checkoutSessionId = data.checkoutSessionId
      });
};

setupElements();

document.querySelectorAll("[type='radio'][name='plan']")
        .forEach(inp => {
          inp.addEventListener("change", function (event){
            if (this.checked) {
              document.getElementById("enterPaymentInfo").disabled = false;
              createCheckoutSession(this.value);
            }
          })
        })

document.getElementById("enterPaymentInfo").addEventListener("click", function (event) {
  event.preventDefault();
  stripe.redirectToCheckout({
      sessionId: checkoutSessionId
  }).then(function (result) {
      console.log("error redirecting to stripe checkout");
  }).catch(function (err) {
      console.log(err);
  })
    
});
