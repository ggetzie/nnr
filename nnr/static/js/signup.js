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
  
    stripe.createPaymentMethod('card', card, {
      billing_details: {
        email: document.getElementById("id_email").value
      },
    }).then(function(result) {
      if (result.error) {
        // Inform the customer that there was an error.
        var errorElement = document.getElementById('card-errors');
        errorElement.textContent = result.error.message;
      } else {
        console.log("Result from creating payment method")
        console.log(result)
        console.log(result.paymentMethod.id)
        // Send the token to your server.
        stripePaymentHandler(result.paymentMethod.id);
      }
    });
  });

  function stripePaymentHandler(payment_method) {
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
      console.log(response)
      const subscription = response.body;
      const { latest_invoice } = subscription;
      const { payment_intent } = latest_invoice;

      if (payment_intent) {
        const { client_secret, status } = payment_intent;
        if (status === 'requires_action') {
          stripe.confirmCardPayment.then(function(result) {
            if (result.error) {
              console.log(result.error)
            } else {
              console.log("Confirmation success!")
            }
          });
        } else {
          console.log("No Confirmation needed!")
        }
      }
      return response.json();
    });
    
    // var hiddenInput = document.createElement('input');
    // hiddenInput.setAttribute('type', 'hidden');
    // hiddenInput.setAttribute('name', 'stripePaymentMethod');
    // hiddenInput.setAttribute('value', payment_method);
    // form.appendChild(hiddenInput);
  
    // // Submit the form
    // form.submit();
  }