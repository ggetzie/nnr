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
      console.log(response)
      stripeElements(response.publicKey);
    });
}

getPublicKey();

var success_url = "/accounts/thankyou/"
var stripe;
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

  var form = document.getElementById('update_payment');
  form.addEventListener('submit', function(event) {
      event.preventDefault();
      changeLoadingState(true);
      stripe.createPaymentMethod({
          type: 'card',
          card: card,
      }).then(function(result){
          if (result.error) {
            showCardError(result.error)
          } else {
            console.log("Got result")
            console.log(result)
            updatePaymentMethod(result.paymentMethod.id);
          }
      })
  });
};  


async function updatePaymentMethod(payment_method) {
    let form = document.getElementById("update_payment");
    let csrfmiddlewaretoken = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    let data = {"payment_method": payment_method};
    console.log("sending data");
    console.log(data);
    fetch(form.action, {
        method: "post",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfmiddlewaretoken,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(data)
    }).then( response => {
        console.log("returning response JSON")
        return response.json()
    }).then(result => {
        console.log(result)
        if (result.error) {
          showCardError(result.error)
        } else {
          changeLoadingState(false);
          showMessage(result.message, "alert-success");
          cardInfo = document.getElementById("cardinfo")
          cardInfo.textContent = result.newPay;
        }
    })
}

function showCardError(error) {
  changeLoadingState(false);
  // The card was declined (i.e. insufficient funds, card has expired, etc)
  showMessage(error.message, "alert-danger")
}
  
var dotter;
// Show a spinner on subscription submission
var changeLoadingState = function(isLoading) {
  var msg = document.getElementById("message");
  if (isLoading) {
    document.getElementById("update_payment").hidden = true;
    msg.textContent = "Loading";
    dotter = setInterval(function() {msg.textContent = msg.textContent + "."}, 3000);
    // document.querySelector('#spinner').classList.add('loading');
    // document.querySelector('button').disabled = true;

    // document.querySelector('#button-text').classList.add('hidden');
  } else {
    clearInterval(dotter);
    msg.textContent = "";
    document.getElementById("update_payment").hidden = false;
    // document.querySelector('button').disabled = false;
    // document.querySelector('#spinner').classList.remove('loading');
    // document.querySelector('#button-text').classList.remove('hidden');
  }
};