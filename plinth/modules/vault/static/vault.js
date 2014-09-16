// Most of the actions will finish fast enough, so better display the spinner
// with a delay to not confuse the users
$('.vault-grid .show-spinner').on('click', function() {
  setTimeout(function() {
    showSpinner('Applying changes, please wait...');
  }, 1500);
});
