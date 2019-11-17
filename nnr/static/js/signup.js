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
        // Send the token to your server.
        stripePaymentHandler(result.payment_method);
      }
    });
  });

  function stripePaymentHandler(payment_method) {
    // collect form data and submit it via fetch
    var form = document.getElementById('signup_form');
    let data = {"payment_method": payment_method};
    for (let i=0; i < form.length; i++) {
      data[form[i].name] = form[i].value
    }
    console.log(data)
    console.log(form.action)
    fetch(form.action, {
      method: "post",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    }).then(response => {
      console.log(response)
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