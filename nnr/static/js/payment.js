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