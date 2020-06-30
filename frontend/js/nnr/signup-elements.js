var stripe;
var success_url = "/accounts/thankyou/"

var stripeElements = function(publicKey) {
  stripe = Stripe(publicKey);
  var elements = stripe.elements();
  // Element styles
  var style = {
    base: {
      fontSize: '16px',
      color: '#32325d',
      fontFamily:
        '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
      fontSmoothing: 'antialiased',
      '::placeholder': {
        color: 'rgba(0,0,0,0.4)'
      }
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
    clearErrors();
    changeLoadingState(true);
    createPaymentMethodAndCustomer(card);
  });
};
  
var createPaymentMethodAndCustomer = function(card) {
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
  let form = document.getElementById('signup_form');
  let data = {"payment_method": payment_method};
  for (let i=0; i < form.length; i++) {
    if (form[i].type !== "submit") {
      data[form[i].name] = form[i].value
    }
  }

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
    return response.json();
  }).then(responseJSON => {
    if (responseJSON.status === "success"){
      handleSubscription(responseJSON.subscription);
    } else {
      changeLoadingState(false);
      handleFormErrors(responseJSON.errors);
    }
      
  });
}

function handleSubscription(subscription) {
  const { latest_invoice, pending_setup_intent } = subscription;
  const { payment_intent } = latest_invoice;
  let success_msg = `Success! Your account has been created. 
                     Please check your email for a confirmation 
                     link to activate your account`;
  
  if (pending_setup_intent) {
    const {client_secret, status } = subscription.pending_setup_intent;
    if (status == "requires_action") {
      stripe.confirmCardSetup(client_secret).then(function(result) {
        if (result.error) {
          showCardError(result.error)
        } else {
          // confirmation completed successfully
          changeLoadingState(false);
          document.getElementById("signup_form").reset();
          showMessage(success_msg, "alert-success");
        }
      })
    } else if (status == "requires_payment_method") {
      changeLoadingState(false);
      showCardError("Unable to authorize payment. Please try a different card");
    } else {
      // setup intent does not require action
      changeLoadingState(false);
      document.getElementById("signup_form").reset();
      showMessage(success_msg, "alert-success");
    } 
  } else {
    // no pending setup intent
    changeLoadingState(false);
    document.getElementById("signup_form").reset();
    showMessage(success_msg, "alert-success");
  }
}

function getPublicKey() {
  return fetch('/main/public_key/', {
    method: 'get',
    headers: {
      'Content-Type': 'application/json',
      "X-Requested-With": "XMLHttpRequest"
    }
  })
    .then(function(response) {
      return response.json();
    })
    .then(function(response) {
      stripeElements(response.publicKey);
    });
}

getPublicKey();

function showCardError(error) {
  changeLoadingState(false);
  // The card was declined (i.e. insufficient funds, card has expired, etc)
  let errorMsg = createAlert(error.message, "alert-danger");
  document.getElementById("signup_form").before(errorMsg);
}
  
var dotter; // Loading......

var changeLoadingState = function(isLoading) {
  console.log("changing loading state");
  if (isLoading) {
    let signupForm = document.getElementById("signup_form");
    let msg = document.createElement("div");
    msg.id = "message";
    msg.textContent = "Loading";
    signupForm.before(msg);
    signupForm.hidden = true;
    if (dotter) {
      clearInterval(dotter);
    }
    dotter = setInterval(function() {
      let loadingMessage = document.getElementById("message");
      loadingMessage.textContent = loadingMessage.textContent + ".";
    }, 3000);
    // document.querySelector('#spinner').classList.add('loading');
    // document.querySelector('button').disabled = true;

    // document.querySelector('#button-text').classList.add('hidden');
  } else {
    clearInterval(dotter);
    let msg = document.getElementById("message");
    msg.remove();
    document.getElementById("signup_form").hidden = false;
    // document.querySelector('button').disabled = false;
    // document.querySelector('#spinner').classList.remove('loading');
    // document.querySelector('#button-text').classList.remove('hidden');
  }
};

function appendError(fieldName, errMsg) {
  let field = document.getElementById(`id_${fieldName}`);
  let errorDiv = document.createElement("div");
  errorDiv.classList.add("invalid-feedback");
  errorDiv.textContent = errMsg;
  field.parentElement.appendChild(errorDiv);
}

function handleFormErrors(errors) {
  for (fieldName in errors) {
    let field = document.getElementById(`id_${fieldName}`);
    field.classList.add("is-invalid");
    for (i in errors[fieldName]) {
      appendError(fieldName, errors[fieldName][i]);
    }
  }
}

function clearErrors() {
  let errorFields = document.querySelectorAll(".is-invalid");
  if (errorFields) {
    for (let i=0; i < errorFields.length; i++) {
      errorFields[i].classList.remove("is-invalid");
    }
  }
  
  let errorFeedback = document.querySelectorAll(".invalid-feedback");
  if (errorFeedback) {
    for (let i=0; i < errorFeedback.length; i++) {
      errorFeedback[i].remove();
    }
  }
}