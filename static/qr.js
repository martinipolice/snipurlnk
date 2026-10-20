const qrDialog = document.getElementById("qrDialog");
const qrCanvas = document.getElementById("qrCanvas");
const qrLink = document.getElementById("qrLink");
const qrMessage = document.getElementById("qrMessage");
const qrDownload = document.getElementById("qrDownload");
const qrShare = document.getElementById("qrShare");
const qrCopy = document.getElementById("qrCopy");
const qrClose = document.getElementById("qrClose");

let currentQr = { url: "", code: "" };

// Browsers without the share menu (like desktop Firefox) don't get a Share button.
if (!navigator.share) qrShare.remove();

// Draws black squares on a white canvas, with the 4-square empty border scanners expect.
function drawQr(text) {
    const qr = qrcode(0, "M");
    qr.addData(text);
    qr.make();

    const quiet = 4;
    const modules = qr.getModuleCount();
    const cell = Math.ceil(520 / (modules + quiet * 2));
    const size = (modules + quiet * 2) * cell;

    qrCanvas.width = size;
    qrCanvas.height = size;
    const ctx = qrCanvas.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = "#000000";
    for (let row = 0; row < modules; row++) {
        for (let col = 0; col < modules; col++) {
            if (qr.isDark(row, col)) {
                ctx.fillRect((col + quiet) * cell, (row + quiet) * cell, cell, cell);
            }
        }
    }
}

function canvasToBlob() {
    return new Promise(function (resolve) {
        qrCanvas.toBlob(resolve, "image/png");
    });
}

function openQr(shortUrl, code) {
    currentQr = { url: shortUrl, code: code };
    qrMessage.textContent = "";
    drawQr(shortUrl);
    qrCanvas.setAttribute("aria-label", "QR code for " + shortUrl);
    qrLink.textContent = shortUrl;
    qrDialog.showModal();
}

qrDownload.addEventListener("click", async function () {
    const blob = await canvasToBlob();
    if (!blob) {
        qrMessage.textContent = "Could not make the image.";
        return;
    }
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = "snipurlnk-" + currentQr.code + ".png";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(objectUrl); }, 1000);
    qrMessage.textContent = "Downloaded.";
});

qrShare.addEventListener("click", async function () {
    let shareData = { title: "snipURlnk", url: currentQr.url };
    const blob = await canvasToBlob();
    if (blob) {
        const file = new File([blob], "snipurlnk-" + currentQr.code + ".png", { type: "image/png" });
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            shareData = { title: "snipURlnk", text: currentQr.url, files: [file] };
        }
    }
    try {
        await navigator.share(shareData);
    } catch (error) {
        if (error.name !== "AbortError") qrMessage.textContent = "Sharing failed.";
    }
});

qrCopy.addEventListener("click", async function () {
    try {
        await navigator.clipboard.writeText(currentQr.url);
        qrMessage.textContent = "Link copied.";
    } catch (error) {
        qrMessage.textContent = "Could not copy the link.";
    }
});

qrClose.addEventListener("click", function () {
    qrDialog.close();
});