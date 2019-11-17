const share_checkbox = $(".shareform > input[type='checkbox']");

share_checkbox.change(function(event) {
    this.disabled=true;
    this.style.cursor='wait';
    this.form.submit();
});
