function toggle_visibility(id) {
    var d = document.getElementById(id);
    if(d.style.display == 'block')
        d.style.display = 'none';
    else
        d.style.display = 'block';
}

function show(id) {
    var d = document.getElementById(id);
    d.style.display = 'block';
}

function hide(id) {
    document.getElementById(id).style.display = 'none';
}
