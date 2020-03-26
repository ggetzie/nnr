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

var createCheckoutSession = function() {
    fetch("/main/create-checkout-session/", {
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
createCheckoutSession();

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

function testpay() {
  console.log("This function was defined")
}