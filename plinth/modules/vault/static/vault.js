// Most of the actions will finish fast enough, so better display the spinner
// with a delay to not confuse the users
$('.vault-grid a.btn').on('click', function() {
  setTimeout(showSpinner, 1500);
});
