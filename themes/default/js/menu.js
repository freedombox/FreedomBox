function main_menu(items) {
    output = "<ul>"
    for (item in items) {
	i = items[item];

	// Handle active page
        if (i["active"]) {
	    active = 'class = "active"';
        } else {
	    active = '';
	}

	// Line break labels
	label = i["label"];
	if (label.search(" ") != -1) {
	    label = label.replace(" ", "<br />");
	} else {
	    label = "&nbsp;<br />" + label;
	}

	output = output +'<li><a href="' + i["url"] + '" ' + active + '>' + label + "</a></li>";
    }
    output = output + "</ul>";
    document.write(output);
}

function render_items(items) {
    output = "<ul>";
    for (item in items) {
	i = items[item];

	// Handle active page
        if (i["active"]) {
	    active = 'class = "active"';
        } else {
	    active = '';
	}

	output = output +'<li><a href="' + i["url"] + '" ' + active + '>' + i['label'] + "</a></li>";
	if (i['subs']) {
	    output += render_items(i['subs']);
	}
    }
    output = output + "</ul>";
    return output
}

function side_menu(items) {
    if (items.length == 0) {
	return 0;
    }
    output = "<h2>Menu</h2>" + render_items(items);
    document.write(output);
}