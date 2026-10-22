// Small messages in the corner ("Link copied"), modelled on shadcn/ui's toast (Sonner).
// showToast(message, kind) where kind is "success" (default) or "error".
// The holder is a popover, so it can appear above an open dialog.

const TOAST_ICONS = document.currentScript.dataset.icons;
const TOAST_SECONDS = 2.6;
const TOAST_LIMIT = 3;

let toaster = null;

function getToaster() {
    if (toaster) return toaster;
    toaster = document.createElement("section");
    toaster.className = "toaster";
    toaster.setAttribute("aria-label", "Notifications");
    toaster.setAttribute("aria-live", "polite");
    if (toaster.showPopover) toaster.setAttribute("popover", "manual");
    document.body.appendChild(toaster);
    return toaster;
}

function showToast(message, kind) {
    kind = kind || "success";
    const holder = getToaster();

    // Showing the popover again puts it above anything opened since, like the QR dialog
    if (holder.showPopover) {
        if (holder.matches(":popover-open")) holder.hidePopover();
        holder.showPopover();
    }

    const toast = document.createElement("div");
    toast.className = "toast toast-" + kind;
    toast.setAttribute("role", kind === "error" ? "alert" : "status");

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "icon");
    svg.setAttribute("aria-hidden", "true");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", TOAST_ICONS + (kind === "error" ? "#i-alert" : "#i-check"));
    svg.appendChild(use);

    const text = document.createElement("span");
    text.textContent = message;
    toast.append(svg, text);
    holder.appendChild(toast);

    while (holder.children.length > TOAST_LIMIT) holder.firstElementChild.remove();

    setTimeout(function () {
        toast.classList.add("toast-leaving");
        setTimeout(function () {
            toast.remove();
            if (!holder.children.length && holder.hidePopover && holder.matches(":popover-open")) holder.hidePopover();
        }, 200);
    }, TOAST_SECONDS * 1000);
}

// A message saved before a page change (like removing a link), shown once the next page loads.
document.addEventListener("DOMContentLoaded", function () {
    let pending = null;
    try {
        pending = sessionStorage.getItem("snipurlnk-toast");
        sessionStorage.removeItem("snipurlnk-toast");
    } catch (error) {
        return;
    }
    if (pending) showToast(pending);
});

function toastAfterReload(message) {
    try { sessionStorage.setItem("snipurlnk-toast", message); } catch (error) { /* no storage: skip the message */ }
}
