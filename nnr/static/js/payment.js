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
        // Send the token to your server.
        stripePaymentHandler(result.payment_method);
      }
    });
  });

  function stripePaymentHandler(payment_method) {
    // Insert the payment method ID into the form so it gets submitted to the server
    var form = document.getElementById('signup_form');
    var hiddenInput = document.createElement('input');
    hiddenInput.setAttribute('type', 'hidden');
    hiddenInput.setAttribute('name', 'stripePaymentMethod');
    hiddenInput.setAttribute('value', payment_method);
    form.appendChild(hiddenInput);
  
    // Submit the form
    form.submit();
  }