function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

var success_url = "/accounts/thankyou/"

var stripe = Stripe('pk_test_636lQazmHaIY6yf9dA5KLSLa00DLs2u5IF');
var elements = stripe.elements();
var style = {
    base: {
      fontSize: '16px',
      color: "#32325d",
    }
  };
  
var card = elements.create('card', {style: style});
card.mount('#card-element');
  
card.addEventListener('change', function(event) {
  var displayError = document.getElementById('card-errors');
  if (event.error) {
    displayError.textContent = event.error.message;
  } else {
    displayError.textContent = '';
  }
});

var form = document.getElementById('signup_form');
form.addEventListener('submit', function(event) {
  event.preventDefault();
  changeLoadingState(true);
  createPaymentMethodAndCustomer(stripe, card);
});
  
var createPaymentMethodAndCustomer = function(stripe, card) {
  var cardholderEmail = document.getElementById('id_email').value;
  stripe
    .createPaymentMethod('card', card, {
      billing_details: {
        email: cardholderEmail
      }
    })
    .then(function(result) {
      if (result.error) {
        showCardError(result.error);
      } else {
        createCustomer(result.paymentMethod.id, cardholderEmail);
      }
    });
};

async function createCustomer(payment_method) {
  // collect form data and submit it via fetch
  var form = document.getElementById('signup_form');
  let data = {"payment_method": payment_method};
  for (let i=0; i < form.length; i++) {
    if (form[i].type !== "submit") {
      data[form[i].name] = form[i].value
    }
  }
  console.log(data)
  console.log(form.action)
  fetch(form.action, {
    method: "post",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": data["csrfmiddlewaretoken"],
      "Accept": "application/json",
      "X-Requested-With": "XMLHttpRequest"
    },
    body: JSON.stringify(data)
  }).then(response => {
    console.log("returning response JSON")
    return response.json();
  }).then(subscription => {
    handleSubscription(subscription);
  });
}

function handleSubscription(subscription) {
  console.log("Handling subscription");
  console.log(subscription);
  const { latest_invoice } = subscription;
  const { payment_intent } = latest_invoice;

  console.log("Payment intent = " + payment_intent)
  if (payment_intent) {
    const { client_secret, status } = payment_intent;
    if (status === 'requires_action' || status === 'requires_payment_method') {
      stripe.confirmCardPayment(client_secret).then(function(result) {
        if (result.error) {
          showCardError(result.error)
          console.log(result.error)
        } else {
          console.log("Confirmation success!")
          window.location.href = success_url
        }
      });
    } else {
      console.log("No Confirmation needed!")
      window.location.href = success_url
    }
  } else {
    console.log("No payment_intent, order complete")
    window.location.href = success_url
  }
}

function showCardError(error) {
  changeLoadingState(false);
  // The card was declined (i.e. insufficient funds, card has expired, etc)
  var errorMsg = document.getElementById("message");
  errorMsg.classList.add("alert-danger");
  errorMsg.textContent = error.message;
  setTimeout(function() {
    errorMsg.textContent = '';
    errorMsg.classList.remove("alert-danger");
  }, 8000);
}
  
var dotter = 0;
// Show a spinner on subscription submission
var changeLoadingState = function(isLoading) {
  var msg = document.getElementById("message");
  if (isLoading) {
    document.getElementById("signup_form").hidden = true;
    msg.textContent = "Loading";
    dotter = setInterval(function() {msg.textContent = msg.textContent + "."}, 3000);
    // document.querySelector('#spinner').classList.add('loading');
    // document.querySelector('button').disabled = true;

    // document.querySelector('#button-text').classList.add('hidden');
  } else {
    clearInterval(dotter);
    msg.textContent = "";
    document.getElementById("signup_form").hidden = false;
    // document.querySelector('button').disabled = false;
    // document.querySelector('#spinner').classList.remove('loading');
    // document.querySelector('#button-text').classList.remove('hidden');
  }
};