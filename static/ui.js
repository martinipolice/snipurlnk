// Shared page behaviour: dropdown menus and keyboard shortcuts.

// Dropdown menus, modelled on shadcn/ui's DropdownMenu: a button with aria-haspopup="menu"
// opens the element named in its aria-controls. Arrow keys, Home and End move between items,
// Escape closes and returns to the button, and Tab or a click elsewhere closes it.
document.querySelectorAll('[aria-haspopup="menu"]').forEach(function (trigger) {
    const menu = document.getElementById(trigger.getAttribute("aria-controls"));
    if (!menu) return;

    function items() {
        return Array.from(menu.querySelectorAll('[role="menuitem"]'));
    }

    function open(index) {
        menu.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
        const list = items();
        list[(index + list.length) % list.length].focus();
    }

    function close(returnFocus) {
        if (menu.hidden) return;
        menu.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
        if (returnFocus) trigger.focus();
    }

    trigger.addEventListener("click", function () {
        if (menu.hidden) open(0); else close(false);
    });

    trigger.addEventListener("keydown", function (event) {
        if (event.key === "ArrowDown") { event.preventDefault(); open(0); }
        if (event.key === "ArrowUp") { event.preventDefault(); open(-1); }
    });

    menu.addEventListener("keydown", function (event) {
        const list = items();
        const current = list.indexOf(document.activeElement);
        const moves = { ArrowDown: current + 1, ArrowUp: current - 1, Home: 0, End: list.length - 1 };
        if (event.key in moves) {
            event.preventDefault();
            list[(moves[event.key] + list.length) % list.length].focus();
        } else if (event.key === "Escape") {
            event.preventDefault();
            close(true);
        } else if (event.key === "Tab") {
            close(false);
        }
    });

    document.addEventListener("click", function (event) {
        if (!menu.contains(event.target) && !trigger.contains(event.target)) close(false);
    });
});

// Press / to jump to a search box on the page (like the one on Your links), unless you're already typing.
document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
    const typing = event.target.closest("input, textarea, select, [contenteditable]");
    const search = document.querySelector("[data-shortcut='/']");
    if (typing || !search) return;
    event.preventDefault();
    search.focus();
});
