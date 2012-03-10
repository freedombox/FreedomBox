function main_menu(items) {
    output = '<ul class="nav">'
    for (item in items) {
	i = items[item];

	// Handle active page
        if (i["active"]) {
	    active = ' class="active"';
        } else {
	    active = '';
	}

	// Line break labels
	/*label = i["label"];
	if (label.search(" ") != -1) {
	    label = label.replace(" ", "<br />");
	} else {
	    label = "&nbsp;<br />" + label;
	}*/

	// Add icon before labels
	icon = '<i class="' + i["icon"] + ' icon-white nav-icon"></i>';
	label = icon + i["label"];

	output = output +'<li' + active + '><a href="' + i["url"] + '"' + active + '>' + label + "</a></li>";
    }
    output = output + "</ul>";
    document.write(output);
}

function render_items(items) {
    output = '<ul class="nav nav-list"><li class="nav-header">Menu</li>';
    for (item in items) {
	i = items[item];

	// Handle active page
        if (i["active"]) {
	    active = ' class="active"';

	    // Add icon before labels
	    icon = '<i class="' + i["icon"] + ' icon-white sidenav-icon"></i>';
	    label = icon + i["label"];
        } else {
	    active = '';

	    // Add icon before labels
	    icon = '<i class="' + i["icon"] + ' sidenav-icon"></i>';
	    label = icon + i["label"];
	}

	output = output +'<li' + active + '><a href="' + i["url"] + '"' + active + '>' + label + "</a></li>";

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
    output = render_items(items);
    document.write(output);
}
